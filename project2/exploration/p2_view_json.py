import json
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 4.64, "longitude": 7.92,
    "start_date": "2025-01-01", "end_date": "2025-01-03",
    "daily": "temperature_2m_max,precipitation_sum",
    "timezone": "Africa/Lagos",
}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
data = r.json()

print("TYPE:", type(data))
print(data)
print()
print(json.dumps(data, indent=2))

with open(BASE_DIR / "sample_response.json", "w") as f:
    json.dump(data, f, indent=2)


#What each part does:
#type(data) shows what Python holds.
#print(data) shows the dictionary on one long line.
#json.dumps(data, indent=2) shows the same content spread out, one item per line, indented by structure. This is the easier version to read.
#The last lines save a copy as sample_response.json next to the script. The BASE_DIR trick is the same one you used in Project 1, so the file lands in the right folder whichever folder the terminal is in. Open that file in VS Code. Pressing Shift+Alt+F formats any JSON file neatly.