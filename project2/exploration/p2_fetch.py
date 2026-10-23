import requests

BASE = "https://archive-api.open-meteo.com/v1/archive"

def fetch(url, params):
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"API error {r.status_code}: {r.text[:200]}")
    return r.json()

good = {
    "latitude": 4.64, "longitude": 7.92,
    "start_date": "2025-01-01", "end_date": "2025-01-03",
    "daily": "temperature_2m_max", "timezone": "Africa/Lagos",
}

data = fetch(BASE, good)
print(data["daily"]["time"])

try:
    fetch(BASE, dict(good, latitude=400))
except RuntimeError as e:
    print("caught:", e)