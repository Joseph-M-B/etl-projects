import time
import requests
from sqlalchemy import inspect, text
import logging
from pathlib import Path
import pandas as pd
import yaml


log = logging.getLogger("etl")


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


RETRY_STATUS = {429, 500, 502, 503, 504}


def fetch_json(url, params, retries=3, pause=2):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout) as e:
            log.warning("attempt %s/%s: network problem (%s)", attempt, retries, type(e).__name__)
        else:
            if r.status_code == 200:
                return r.json()
            if r.status_code not in RETRY_STATUS:
                raise RuntimeError(f"API error {r.status_code} (not retrying): {r.text[:200]}")
            log.warning("attempt %s/%s: status %s, will retry", attempt, retries, r.status_code)
        if attempt < retries:
            time.sleep(pause * attempt)
    raise RuntimeError(f"gave up after {retries} attempts")


def _start_for(source, location, engine):
    api = source["api"]
    config_start = pd.Timestamp(api["start_date"])
    start = config_start
    inc = api.get("incremental")
    if inc and engine is not None and inspect(engine).has_table(source["table"]):
        sql = (f"SELECT MAX({inc['date_column']}) FROM {source['table']} "
               f"WHERE {api['location_column']} = :loc")
        with engine.connect() as conn:
            latest = conn.execute(text(sql), {"loc": location}).scalar()
        if latest is not None:
            start = pd.Timestamp(latest) + pd.Timedelta(days=1 - inc.get("lookback_days", 0))
    return max(start, config_start)


def read_api(source, engine):
    api = source["api"]
    end = pd.Timestamp(api["end_date"])
    frames = []
    for location, (lat, lon) in api["locations"].items():
        start = _start_for(source, location, engine)
        if start > end:
            log.info("%s: %s is up to date", source["name"], location)
            continue
        params = dict(api["params"], latitude=lat, longitude=lon,
                      start_date=start.strftime("%Y-%m-%d"),
                      end_date=end.strftime("%Y-%m-%d"))
        log.info("%s: %s fetching %s to %s", source["name"], location,
                 params["start_date"], params["end_date"])
        data = fetch_json(api["url"], params)
        df = pd.DataFrame(data["daily"])
        df[api["location_column"]] = location
        frames.append(df)
        time.sleep(1)
    if not frames:
        return pd.DataFrame(columns=list(source["columns"]))
    return pd.concat(frames, ignore_index=True).rename(columns=api["rename"])


def read_source(source, base_dir, engine=None):
    if source["type"] == "csv":
        df = pd.read_csv(Path(base_dir) / source["path"])
    elif source["type"] == "api":
        df = read_api(source, engine)
    else:
        raise ValueError(f"unsupported source type: {source['type']}")
    log.info("%s: read %s rows", source["name"], len(df))
    return df


def clean_frame(df, source):
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip()

    rules = source.get("clean", {})
    for col, style in rules.get("case", {}).items():
        if style == "title":
            df[col] = df[col].str.title()
        elif style == "lower":
            df[col] = df[col].str.lower()
        elif style == "upper":
            df[col] = df[col].str.upper()
        else:
            raise ValueError(f"unknown case style: {style}")

    if rules.get("drop_duplicates"):
        before = len(df)
        df = df.drop_duplicates()
        log.info("%s: removed %s duplicate rows", source["name"], before - len(df))
    return df


def apply_types(df, source):
    df = df.copy()
    for col, sqltype in source["columns"].items():
        t = sqltype.upper()
        before = df[col].isna().sum()
        if t in ("TIMESTAMP", "DATE"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif t in ("INTEGER", "BIGINT"):
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif t.startswith("NUMERIC"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        after = df[col].isna().sum()
        if after > before:
            log.warning("%s.%s: %s values could not be converted to %s",
                        source["name"], col, after - before, sqltype)
    return df[list(source["columns"])]