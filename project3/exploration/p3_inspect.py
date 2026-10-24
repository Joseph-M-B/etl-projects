from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
rentals = pd.read_csv(BASE_DIR / "equipment_rentals_clean.csv", parse_dates=["start_date"])

print(rentals.shape)
print(sorted(rentals["site"].unique()))

usable = rentals.dropna(subset=["start_date", "days"]).copy()
usable["days"] = usable["days"].astype(int)
usable["end_date"] = usable["start_date"] + pd.to_timedelta(usable["days"] - 1, unit="D")

print("usable rentals:", len(usable), "of", len(rentals))
print("first start:", usable["start_date"].min().date())
print("last end:", usable["end_date"].max().date())
print("total rental-days:", usable["days"].sum())


#What it does:
#dropna(subset=[...]) keeps only rentals with both a start date and a number of days.
#The others can’t be placed on a calendar.
""" end_date = start_date + days - 1 is a business rule
 I am assuming: a rental of 3 days starting on the 1st covers the 1st, 2nd and 3rd. 
 On a real job, you will confirm this with the client"""