import sqlite3, sys, pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 40)
con = sqlite3.connect(HERE.parent / "data" / "processed" / "ecommerce.db")
sql = Path(sys.argv[1]).read_text()
for i, stmt in enumerate([s for s in sql.split(";") if s.strip(" \n\t-")], 1):
    try:
        print(f"\n===== statement {i} =====")
        print(pd.read_sql(stmt, con).to_string(index=False))
    except Exception as e:
        print("skipped (comment block):", str(e)[:80])
