import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text, types
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).parent
df = pd.read_csv(BASE_DIR / "equipment_rentals_raw.csv")
raw_row_count = len(df)

df.columns = (
    df.columns
      .str.strip()
      .str.lower()
      .str.replace(r"[^a-z0-9]+", "_", regex=True)
      .str.strip("_")
)
print(df.columns.tolist())


def clean_text(series):
    return series.str.strip().str.replace(r"\s+", " ", regex=True)

df["equipment_type"] = clean_text(df["equipment_type"]).str.title()
df["equipment_type"] = df["equipment_type"].replace({"Bull Dozer": "Bulldozer"})
df["site"] = clean_text(df["site"]).str.title()
df["status"] = clean_text(df["status"]).str.lower()

print(df["equipment_type"].value_counts())
print(df["site"].value_counts())
print(df["status"].value_counts(dropna=False))


def to_number(series):
    cleaned = series.astype(str).str.replace(r"[^\d.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")

df["days"] = to_number(df["days"])
df["daily_rate_ngn"] = to_number(df["daily_rate_ngn"])

df["days"] = df["days"].where(df["days"] > 0)
df["daily_rate_ngn"] = df["daily_rate_ngn"].where(df["daily_rate_ngn"] > 0)

df["status"] = df["status"].fillna("unknown")

print(df[["days", "daily_rate_ngn"]].describe())
print(df[["days", "daily_rate_ngn"]].isnull().sum())
print(df["status"].value_counts())

print(df[df["days"].isnull()])


raw = df["start_date"].astype(str).str.strip()

d1 = pd.to_datetime(raw, format="%Y-%m-%d", errors="coerce")
d2 = pd.to_datetime(raw, format="%d/%m/%Y", errors="coerce")
d3 = pd.to_datetime(raw, format="%B %d, %Y", errors="coerce")

df["start_date"] = d1.fillna(d2).fillna(d3)

print(df["start_date"].isnull().sum())
print(df["start_date"].min(), df["start_date"].max())
print(df["start_date"].dt.month.value_counts().sort_index())


print("rows before dedupe:", len(df))

removed = df[df.duplicated(keep="first")]
removed.to_csv(BASE_DIR / "removed_duplicates.csv", index=False)
print("duplicate rows removed:", len(removed))

df = df.drop_duplicates()
print("rows after dedupe:", len(df))
print("rental_ids still repeated:", df["rental_id"].duplicated().sum())


checks = {
    "rows reconcile": raw_row_count - len(removed) == len(df),
    "rental_id unique": df["rental_id"].is_unique,
    "no missing rental_id": df["rental_id"].notnull().all(),
    "days positive when present": (df["days"].dropna() > 0).all(),
    "rate positive when present": (df["daily_rate_ngn"].dropna() > 0).all(),
    "status values valid": df["status"].isin(["active", "closed", "completed", "unknown"]).all(),
    "equipment types valid": df["equipment_type"].nunique() == 6,
}

for name, passed in checks.items():
    print(("PASS  " if passed else "FAIL  ") + name)

if not all(checks.values()):
    raise ValueError("Validation failed - not loading to the database")


df["days"] = df["days"].astype("Int64")

url = URL.create(
    "postgresql+psycopg2",
    username=os.environ["PG_USER"],
    password=os.environ["PG_PASSWORD"],
    host=os.environ["PG_HOST"],
    port=int(os.environ["PG_PORT"]),
    database=os.environ["PG_DB"],
)
engine = create_engine(url)

df.to_sql(
    "equipment_rentals_clean", engine,
    if_exists="replace", index=False,
    dtype={"start_date": types.Date(), "days": types.Integer()},
    method="multi", chunksize=1000,
)
print("loaded", len(df), "rows")

with engine.connect() as conn:
    in_db = conn.execute(text("SELECT COUNT(*) FROM equipment_rentals_clean")).scalar()
print("rows in database:", in_db)
if in_db != len(df):
    raise ValueError("Row count in database does not match the cleaned data")