import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

log = logging.getLogger("p3")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS rental_weather (
    rental_id             TEXT PRIMARY KEY,
    equipment_type        TEXT,
    site                  TEXT          NOT NULL,
    start_date            DATE          NOT NULL,
    days                  INTEGER       NOT NULL,
    end_date              DATE          NOT NULL,
    daily_rate_ngn        NUMERIC(12,2),
    status                TEXT,
    days_in_period        INTEGER,
    weather_days_matched  INTEGER,
    rainy_days            INTEGER,
    total_precip_mm       NUMERIC(8,1),
    avg_temp_max_c        NUMERIC(5,1),
    loaded_at             TIMESTAMP     NOT NULL DEFAULT now()
);
"""

COLUMNS = [
    "rental_id", "equipment_type", "site", "start_date", "days", "end_date",
    "daily_rate_ngn", "status", "days_in_period", "weather_days_matched",
    "rainy_days", "total_precip_mm", "avg_temp_max_c",
]
UPDATE_COLS = [c for c in COLUMNS if c != "rental_id"]

UPSERT_SQL = (
    f"INSERT INTO rental_weather ({', '.join(COLUMNS)}) "
    f"VALUES ({', '.join(':' + c for c in COLUMNS)}) "
    "ON CONFLICT (rental_id) DO UPDATE SET "
    + ", ".join(f"{c} = EXCLUDED.{c}" for c in UPDATE_COLS)
    + ", loaded_at = now()"
)


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


def load(result):
    df = result[COLUMNS].copy()
    df["start_date"] = df["start_date"].dt.date
    df["end_date"] = df["end_date"].dt.date
    records = df.astype(object).where(df.notna(), None).to_dict("records")

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(CREATE_SQL))
        conn.execute(text(UPSERT_SQL), records)
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM rental_weather")).scalar()

    log.info("loaded %s rentals; rental_weather now holds %s rows", len(df), n)
    if n < len(df):
        raise ValueError("fewer rows in the database than were loaded")