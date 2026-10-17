from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
df = pd.read_csv(BASE_DIR / "equipment_rentals_raw.csv")


print(df.shape)
print(df.columns.tolist())
print(df.dtypes)
print(df.isnull().sum())
print(df.head(10))