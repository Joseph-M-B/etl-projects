import requests

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 4.64, "longitude": 7.92,
    "start_date": "2025-01-01", "end_date": "2025-01-03",
    "daily": "temperature_2m_max", "timezone": "Africa/Lagos",
}

r = requests.get(url, params=params, timeout=30)

print("URL actually sent:", r.url)
print("--- headers WE sent ---")
for name, value in r.request.headers.items():
    print(name, ":", value)
print("--- headers the SERVER sent back ---")
for name, value in r.headers.items():
    print(name, ":", value)