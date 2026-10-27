from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "config.yaml") as f:
    config = yaml.safe_load(f)

print(type(config))
print(list(config.keys()))
print(len(config["sources"]))
for s in config["sources"]:
    print(s["name"], "->", s["table"], "key:", s["primary_key"])
print(config["sources"][1]["clean"]["case"])