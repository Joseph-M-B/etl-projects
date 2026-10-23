import requests

BASE = "https://archive-api.open-meteo.com/v1/archive"
good = {
    "latitude": 4.64, "longitude": 7.92,
    "start_date": "2025-01-01", "end_date": "2025-01-03",
    "daily": "temperature_2m_max", "timezone": "Africa/Lagos",
}
bad_param = dict(good, latitude=400)

r1 = requests.get(BASE, params=good, timeout=30)
print("good request:", r1.status_code)

r2 = requests.get(BASE, params=bad_param, timeout=30)
print("bad parameter:", r2.status_code)
print(r2.text)

r3 = requests.get("https://archive-api.open-meteo.com/v1/archiv", params=good, timeout=30)
print("wrong endpoint:", r3.status_code)

print(r3.text[:200])
try:
    r3.json()
    print("the 404 reply was valid JSON")
except Exception as e:
    print("calling .json() failed with:", type(e).__name__)