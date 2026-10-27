import logging
from pathlib import Path
import etl_core
import etl_load

BASE_DIR = Path(__file__).parent

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(BASE_DIR / "pipeline.log"), logging.StreamHandler()],
    )
    log = logging.getLogger("etl")
    config = etl_core.load_config(BASE_DIR / "config.yaml")
    engine = etl_load.get_engine()

    frames = {}
    for source in config["sources"]:
        df = etl_core.read_source(source, BASE_DIR, engine)
        df = etl_core.clean_frame(df, source)
        df = etl_core.apply_types(df, source)
        etl_load.validate(df, source, frames)
        etl_load.load_table(df, source, engine)
        frames[source["name"]] = df
    log.info("run complete: %s sources loaded", len(frames))