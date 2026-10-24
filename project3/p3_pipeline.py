import logging
from pathlib import Path
import pandas as pd
import weather_api

BASE_DIR = Path(__file__).parent
log = logging.getLogger("p3")


def load_rentals():
    rentals = pd.read_csv(BASE_DIR / "equipment_rentals_clean.csv", parse_dates=["start_date"])
    log.info("read %s rentals", len(rentals))
    return rentals


def split_usable(rentals):
    ok = rentals["start_date"].notna() & rentals["days"].notna()
    usable = rentals[ok].copy()
    bad = rentals[~ok].copy()
    bad["reason"] = bad["start_date"].isna().map({True: "missing start_date", False: "missing days"})
    usable["days"] = usable["days"].astype(int)
    usable["end_date"] = usable["start_date"] + pd.to_timedelta(usable["days"] - 1, unit="D")
    return usable, bad


def expand_to_days(usable):
    d = usable.copy()
    d["rental_date"] = d.apply(
        lambda r: list(pd.date_range(r["start_date"], periods=r["days"])), axis=1
    )
    out = d.explode("rental_date")[["rental_id", "site", "rental_date"]].reset_index(drop=True)
    out["rental_date"] = pd.to_datetime(out["rental_date"])
    return out


def summarize(usable, rental_days, weather):
    joined = rental_days.merge(
        weather, how="left",
        left_on=["site", "rental_date"], right_on=["site", "weather_date"],
    )
    summary = joined.groupby("rental_id").agg(
        days_in_period=("rental_date", "size"),
        weather_days_matched=("temp_max_c", "count"),
        rainy_days=("precip_mm", lambda s: int((s >= 1).sum())),
        total_precip_mm=("precip_mm", "sum"),
        avg_temp_max_c=("temp_max_c", "mean"),
    ).reset_index()
    summary["total_precip_mm"] = summary["total_precip_mm"].round(1)
    summary["avg_temp_max_c"] = summary["avg_temp_max_c"].round(1)
    result = usable.merge(summary, on="rental_id", how="left")
    if len(result) != len(usable):
        raise ValueError("join changed the number of rentals - check the grain")
    return result


def run():
    rentals = load_rentals()
    usable, bad = split_usable(rentals)
    bad.to_csv(BASE_DIR / "rentals_quarantine.csv", index=False)
    log.warning("%s rentals quarantined (see rentals_quarantine.csv)", len(bad))

    start = usable["start_date"].min().strftime("%Y-%m-%d")
    end = usable["end_date"].max().strftime("%Y-%m-%d")
    log.info("weather window needed: %s to %s", start, end)
    weather = weather_api.get_weather(start, end)

    rental_days = expand_to_days(usable)
    return summarize(usable, rental_days, weather), bad, len(rentals)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result, bad, total = run()
    print(result.shape)
    print("all rental days have weather:", (result["weather_days_matched"] == result["days"]).all())
    print(result[["rental_id", "site", "start_date", "days", "rainy_days",
                  "total_precip_mm", "avg_temp_max_c"]].head())