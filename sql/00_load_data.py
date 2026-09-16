"""Load cleaned data into SQLite so every .sql file runs as-is."""
import sqlite3, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent
CLEANED = HERE.parent / "data" / "processed" / "ecommerce_cleaned.csv"
DB = HERE.parent / "data" / "processed" / "ecommerce.db"

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
df["visit_date"] = df["visit_date"].dt.strftime("%Y-%m-%d")   # ISO for SQLite date funcs
df.to_sql("sessions", sqlite3.connect(DB), if_exists="replace", index=False)
con = sqlite3.connect(DB)
con.execute("CREATE INDEX IF NOT EXISTS ix_date ON sessions(visit_date)")
con.execute("CREATE INDEX IF NOT EXISTS ix_prod ON sessions(product_id)")
con.execute("CREATE INDEX IF NOT EXISTS ix_cust ON sessions(customer_id)")
print("rows loaded:", con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], "→", DB)
