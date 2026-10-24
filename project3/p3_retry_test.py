import logging
import weather_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
weather_api.BASE = "https://archive-api.open-meteo.invalid/v1/archive"

try:
    weather_api.fetch_json({}, retries=2, pause=1)
except RuntimeError as e:
    print("pipeline stopped with:", e)