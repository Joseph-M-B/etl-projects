import logging
import time
import pandas as pd
import requests

log = logging.getLogger(__name__)

BASE = "https://archive-api.open-meteo.com/v1/archive"
SITES = {
    "Eket Yard": (4.64, 7.92),
    "Uyo Road Project": (5.03, 7.93),
    "Calabar Bridge": (4.95, 8.32),
    "Port Harcourt Depot": (4.82, 7.03),
}
RETRY_STATUS = {429, 500, 502, 503, 504}


def fetch_json(params, retries=3, pause=2):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(BASE, params=params, timeout=30)
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


def get_weather(start_date, end_date):
    frames = []
    for site, (lat, lon) in SITES.items():
        params = {
            "latitude": lat, "longitude": lon,
            "start_date": start_date, "end_date": end_date,
            "daily": "temperature_2m_max,precipitation_sum",
            "timezone": "Africa/Lagos",
        }
        data = fetch_json(params)
        df = pd.DataFrame(data["daily"])
        df["site"] = site
        log.info("%s: %s rows", site, len(df))
        frames.append(df)
        time.sleep(1)
    weather = pd.concat(frames, ignore_index=True)
    weather = weather.rename(columns={
        "time": "weather_date",
        "temperature_2m_max": "temp_max_c",
        "precipitation_sum": "precip_mm",
    })
    weather["weather_date"] = pd.to_datetime(weather["weather_date"])
    return weather[["site", "weather_date", "temp_max_c", "precip_mm"]]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    w = get_weather("2025-01-14", "2025-07-14")
    print(w.shape)
    print(w.groupby("site").size())
    print(w["weather_date"].min().date(), w["weather_date"].max().date())