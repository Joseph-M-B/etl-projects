import requests

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 52.52, "longitude": 13.41,
    "start_date": "2026-10-05", "end_date": "2026-10-19",
    "hourly": "temperature_2m",
}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
data = r.json()

times = data["hourly"]["time"]
temps = data["hourly"]["temperature_2m"]
print(len(times), len(temps))
print(times[13], temps[13])
print(times[-1], temps[-1])

# what each part does
#url is the endpoint, and params holds the order details, as in the docs table.
#requests.get(...) sends the request, with a 30-second timeout.
#r.raise_for_status() stops the script with an error if the reply is a 4xx or 5xx.
#r.json() turns the reply into a Python dictionary.
#data["hourly"]["time"] reaches into the dictionary: first the "hourly" section, then its "time" list. The temperatures work the same way.
#times[13] is the 14th item, since Python counts from 0. times[-1] is the last item.