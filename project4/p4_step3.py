import logging
from pathlib import Path
import etl_core

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
BASE_DIR = Path(__file__).parent
config = etl_core.load_config(BASE_DIR / "config.yaml")

for source in config["sources"]:
    df = etl_core.read_source(source, BASE_DIR)
    df = etl_core.clean_frame(df, source)
    df = etl_core.apply_types(df, source)
    print(source["name"], df.shape)
    print(df.dtypes)
    if source["name"] == "maintenance_events":
        print(df["cause"].value_counts())
        print("open work orders:", df["repair_end"].isna().sum())