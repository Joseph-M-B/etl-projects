from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
assets = pd.read_csv(BASE_DIR / "data" / "assets.csv")
events = pd.read_csv(BASE_DIR / "data" / "maintenance_events.csv")

print(assets.shape, events.shape)
print(assets["equipment_type"].value_counts())
print(events.isnull().sum())
print("duplicate rows:", events.duplicated().sum())
print("duplicate event_ids:", events["event_id"].duplicated().sum())
print(events["cause"].value_counts())
print(events["breakdown_start"].min(), events["breakdown_start"].max())
print("assets in events but not in assets:",
      set(events["asset_id"]) - set(assets["asset_id"]))