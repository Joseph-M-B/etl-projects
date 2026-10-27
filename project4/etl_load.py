import logging
import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

log = logging.getLogger("etl")


def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=int(os.environ["PG_PORT"]),
        database=os.environ["PG_DB"],
    )
    return create_engine(url)


def validate(df, source, frames):
    problems = []
    name = source["name"]

    for col in source.get("required", []):
        n = int(df[col].isna().sum())
        if n:
            problems.append(f"{n} blank values in required column {col}")

    key = source["primary_key"]
    n = int(df.duplicated(subset=key).sum())
    if n:
        problems.append(f"{n} duplicate values of primary key {key}")

    for check in source.get("checks", []):
        if check["type"] == "foreign_key":
            parent = frames[check["references_source"]][check["references_column"]]
            n = int((~df[check["column"]].isin(parent)).sum())
            if n:
                problems.append(
                    f"{n} values in {check['column']} not found in {check['references_source']}")
        elif check["type"] == "date_order":
            e, l = check["earlier"], check["later"]
            n = int((df[l].notna() & (df[l] < df[e])).sum())
            if n:
                problems.append(f"{n} rows where {l} is before {e}")
        else:
            raise ValueError(f"unknown check type: {check['type']}")

    if problems:
        for p in problems:
            log.error("%s: FAIL %s", name, p)
        raise ValueError(f"{name}: validation failed, nothing loaded")
    log.info("%s: all checks passed", name)


def load_table(df, source, engine):
    table = source["table"]
    cols = list(source["columns"])
    key = source["primary_key"]
    required = set(source.get("required", [])) | set(key)

    col_defs = [f"{c} {t}" + (" NOT NULL" if c in required else "")
                for c, t in source["columns"].items()]
    create_sql = (f"CREATE TABLE IF NOT EXISTS {table} ("
                  + ", ".join(col_defs)
                  + f", PRIMARY KEY ({', '.join(key)}),"
                  + " loaded_at TIMESTAMP NOT NULL DEFAULT now())")

    update_cols = [c for c in cols if c not in key]
    upsert_sql = (f"INSERT INTO {table} ({', '.join(cols)}) "
                  f"VALUES ({', '.join(':' + c for c in cols)}) "
                  f"ON CONFLICT ({', '.join(key)}) DO UPDATE SET "
                  + ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
                  + ", loaded_at = now()")

    df = df.copy()
    for c, t in source["columns"].items():
        if t.upper() == "DATE":
            df[c] = df[c].dt.date
    records = df.astype(object).where(df.notna(), None).to_dict("records")
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        if records:
            conn.execute(text(upsert_sql), records)
        n = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    log.info("%s: loaded %s rows; table now holds %s", table, len(df), n)
    return n