import time
import pandas as pd
import requests
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BASE = "https://archive-api.open-meteo.com/v1/archive"

SITES = {
    "Eket Yard": (4.64, 7.92),
    "Uyo Road Project": (5.03, 7.93),
    "Calabar Bridge": (4.95, 8.32),
    "Port Harcourt Depot": (4.82, 7.03),
}

def fetch(url, params):
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"API error {r.status_code}: {r.text[:200]}")
    return r.json()

frames = []
for site, (lat, lon) in SITES.items():
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": "2025-01-01", "end_date": "2025-06-30",
        "daily": "temperature_2m_max,precipitation_sum",
        "timezone": "Africa/Lagos",
    }
    data = fetch(BASE, params)
    df_site = pd.DataFrame(data["daily"])
    df_site["site"] = site
    frames.append(df_site)
    time.sleep(1)

weather = pd.concat(frames, ignore_index=True)
weather = weather.rename(columns={
    "time": "weather_date",
    "temperature_2m_max": "temp_max_c",
    "precipitation_sum": "precip_mm",
})
weather["weather_date"] = pd.to_datetime(weather["weather_date"])
weather = weather[["site", "weather_date", "temp_max_c", "precip_mm"]]

print(weather.shape)
print(weather.head())
print(weather.isnull().sum())
print(weather.groupby("site").size())

url = URL.create(
    "postgresql+psycopg2",
    username=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
    host=os.environ["PG_HOST"],
    port=int(os.environ["PG_PORT"]),
    database=os.environ["PG_DB"],
)
engine = create_engine(url)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS weather_daily (
    site          TEXT          NOT NULL,
    weather_date  DATE          NOT NULL,
    temp_max_c    NUMERIC(5,2),
    precip_mm     NUMERIC(6,2),
    loaded_at     TIMESTAMP     NOT NULL DEFAULT now(),
    PRIMARY KEY (site, weather_date)
);
"""

UPSERT_SQL = """
INSERT INTO weather_daily (site, weather_date, temp_max_c, precip_mm)
VALUES (:site, :weather_date, :temp_max_c, :precip_mm)
ON CONFLICT (site, weather_date)
DO UPDATE SET temp_max_c = EXCLUDED.temp_max_c,
              precip_mm  = EXCLUDED.precip_mm,
              loaded_at  = now();
"""

weather["weather_date"] = weather["weather_date"].dt.date
records = weather.astype(object).where(weather.notna(), None).to_dict("records")

with engine.begin() as conn:
    conn.execute(text(CREATE_SQL))
    conn.execute(text(UPSERT_SQL), records)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM weather_daily")).scalar()
print("rows in database:", n)