import logging
from pathlib import Path
import p3_pipeline
import p3_load

BASE_DIR = Path(__file__).parent
log = logging.getLogger("p3")


def validate(result, bad, total):
    checks = {
        "rental_id unique": result["rental_id"].is_unique,
        "every rental accounted for": len(result) + len(bad) == total,
        "every rental day has weather": (result["weather_days_matched"] == result["days"]).all(),
        "rainy days never exceed days": (result["rainy_days"] <= result["days"]).all(),
        "rainfall not negative": (result["total_precip_mm"] >= 0).all(),
        "temperatures plausible (10-50 C)": result["avg_temp_max_c"].between(10, 50).all(),
    }
    for name, ok in checks.items():
        if ok:
            log.info("PASS  %s", name)
        else:
            log.error("FAIL  %s", name)
    if not all(checks.values()):
        raise ValueError("validation failed - nothing will be loaded")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(BASE_DIR / "pipeline.log"), logging.StreamHandler()],
    )
    result, bad, total = p3_pipeline.run()
    validate(result, bad, total)
    p3_load.load(result)
    log.info("pipeline finished OK: %s rentals enriched, %s quarantined", len(result), len(bad))


"""What it does:
The six checks use .all() for “true in every row”. The temperature range is a plausibility rule: an average high outside 10 to 50°C would point to a unit or join error.
raise ValueError(...) stops the run before anything is loaded, which is the safeguard we’ll rely on next.
handlers=[FileHandler, StreamHandler] sends every message to both a file, pipeline.log, and your screen. """