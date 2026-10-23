import os
import requests

os.environ.setdefault("DEMO_API_KEY", "not-a-real-key-123")

headers = {"Authorization": f"Bearer {os.environ['DEMO_API_KEY']}"}
params = {
    "latitude": 4.64, "longitude": 7.92,
    "start_date": "2025-01-01", "end_date": "2025-01-02",
    "hourly": "temperature_2m",
}
r = requests.get("https://archive-api.open-meteo.com/v1/archive",
                 params=params, headers=headers, timeout=30)

print(r.status_code)
print("full header:", r.request.headers["Authorization"])
print("masked     :", r.request.headers["Authorization"][:12] + "...")