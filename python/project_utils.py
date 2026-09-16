"""Shared config/paths/label-maps for the whole project."""
from pathlib import Path
import json
import pandas as pd

ROOT   = Path(__file__).resolve().parents[1]
RAW    = ROOT / "data" / "raw" / "Ecommerce.csv"
PROC   = ROOT / "data" / "processed"
TABLES = ROOT / "reports" / "tables"
FIGS   = ROOT / "reports" / "figures"
DOCS   = ROOT / "documentation"
for p in (PROC, TABLES, FIGS, DOCS):
    p.mkdir(parents=True, exist_ok=True)

CLEANED = PROC / "ecommerce_cleaned.csv"
BASE    = PROC / "ecommerce_cleaned_base.csv"

# ------------------------------------------------------------------
# INTEGER-CODE LABELS.
# The file ships device_type / user_type / marketing_channel /
# product_category / payment_method / location as integer codes with
# NO codebook. We do NOT invent business names. If you learn the real
# labels, edit the strings below - every script, SQL export and the
# Excel workbook read from this one place.
# ------------------------------------------------------------------
DEVICE_LABELS   = {0: "Device 0", 1: "Device 1", 2: "Device 2"}
USERTYPE_LABELS = {0: "User Type 0", 1: "User Type 1"}
CHANNEL_LABELS  = {i: f"Channel {i}" for i in range(6)}
CATEGORY_LABELS = {i: f"Category {i}" for i in range(8)}
PAYMENT_LABELS  = {i: f"Payment {i}" for i in range(6)}

# These two WERE verified against the calendar in the file (see
# documentation/data_quality_report.md). The validator re-checks them
# on every run and warns if the full file ever disagrees.
WEEKDAY_LABELS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
SEASON_LABELS  = {0: "Autumn (Sep-Nov)", 1: "Spring (Mar-May)",
                  2: "Summer (Jun-Aug)", 3: "Winter (Dec-Feb)"}

def apply_labels(s: pd.Series, mapping: dict, prefix: str) -> pd.Series:
    return s.map(lambda v: mapping.get(v, f"{prefix} {v} (unexpected)"))

def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    first = str(df.columns[0])
    if first.startswith("Unnamed") or first == "":
        df = df.rename(columns={df.columns[0]: "source_row_number"})
    return df

def save_json(obj, name: str) -> Path:
    out = TABLES / name
    out.write_text(json.dumps(obj, indent=2, default=str))
    print(f"saved → {out}")
    return out

def load_json(name: str) -> dict:
    return json.loads((TABLES / name).read_text())

def save_table(df: pd.DataFrame, name: str) -> Path:
    out = TABLES / name
    df.to_csv(out, index=False)
    print(f"saved → {out}")
    return out
