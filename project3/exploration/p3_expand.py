from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
rentals = pd.read_csv(BASE_DIR / "equipment_rentals_clean.csv", parse_dates=["start_date"])

usable = rentals.dropna(subset=["start_date", "days"]).copy()
usable["days"] = usable["days"].astype(int)
usable["end_date"] = usable["start_date"] + pd.to_timedelta(usable["days"] - 1, unit="D")

usable["rental_date"] = usable.apply(
    lambda r: list(pd.date_range(r["start_date"], periods=r["days"])), axis=1
)
rental_days = usable.explode("rental_date")[["rental_id", "site", "rental_date"]].copy()
rental_days["rental_date"] = pd.to_datetime(rental_days["rental_date"])

print(rental_days.shape)
print(rental_days.head())
print(rental_days["rental_date"].min().date(), rental_days["rental_date"].max().date())

last = usable.loc[usable["end_date"].idxmax(), "rental_id"]
print(last, rental_days[rental_days["rental_id"] == last]["rental_date"].agg(["min", "max", "count"]))


"""What the new parts do:
apply(..., axis=1) runs a function on each row. Here it builds a list of consecutive dates for that rental.
pd.date_range(start, periods=n) makes n consecutive days from the start date.
explode("rental_date") turns each list into separate rows.
idxmax() finds the row with the largest end date, so the last lines show the rental that ends latest """