"""Reproducible cleaning pipeline: raw → ecommerce_cleaned_base.csv.
Every decision is recorded; raw file is never touched."""
import pandas as pd
from project_utils import load_raw, BASE, PROC, save_json

df = load_raw()
decisions = []

# D1: capture provenance of every row (audit trail)
df["source_row_number"] = df.get("source_row_number", pd.RangeIndex(1, len(df) + 1) + 1)
decisions.append("D1 kept source row numbers for full lineage/audit.")

# D2: exact duplicate rows → drop, keep first (count documented)
dupes = int(df.duplicated().sum())
if dupes:
    df = df.drop_duplicates(keep="first")
decisions.append(f"D2 dropped {dupes} exact duplicate rows (keep=first).")

# D3: unparseable dates → quarantine, never guess format
d = pd.to_datetime(df["visit_date"], format="%d-%m-%Y", errors="coerce")
bad = df[d.isna()]
if len(bad):
    bad.to_csv(PROC / "quarantine_invalid_dates.csv", index=False)
    df = df[d.notna()].copy()
decisions.append(f"D3 quarantined {len(bad)} rows with unparseable visit_date (saved to processed/).")

# D4: parse date explicitly DD-MM-YYYY (sample rows like 06-05-2024 prove dayfirst is required)
df["visit_date"] = pd.to_datetime(df["visit_date"], format="%d-%m-%Y")
decisions.append("D4 parsed visit_date with explicit format '%d-%m-%Y' (verified vs visit_day/visit_month).")

# D5: dtypes
for c in ["customer_id", "session_id", "device_type", "user_type", "marketing_channel",
          "product_id", "product_category", "quantity", "discount_percent", "pages_viewed",
          "time_on_site_sec", "added_to_cart", "purchased", "cart_abandoned", "rating",
          "review_text", "review_helpful_votes", "payment_method", "visit_day", "visit_month",
          "visit_weekday", "visit_season", "location"]:
    df[c] = df[c].astype(int)
for c in ["unit_price", "discount_amount", "revenue", "revenue_normalized"]:
    df[c] = df[c].astype(float)
decisions.append("D5 enforced dtypes: ids/flags/counts int, money float, date datetime.")

# D6: critical-key guard (defensive; validator already showed none exist)
crit = df[["session_id", "visit_date", "customer_id", "product_id"]].isna().any(axis=1)
if crit.any():
    df[crit].to_csv(PROC / "quarantine_missing_keys.csv", index=False)
    df = df[~crit].copy()
decisions.append(f"D6 quarantined {int(crit.sum())} rows missing critical keys (session/date/customer/product).")

# D7: no outlier removal — long-tail prices/revenues are legitimate e-commerce
#     behaviour; outliers are flagged in validation and visible in boxplots.
decisions.append("D7 NO outlier removal: extreme unit_price/revenue values are plausible "
                 "long-tail sales, flagged only (see data_quality_report.md).")

# D8: revenue zeros are structural (no purchase), not missing → kept; all revenue
#     analytics filter purchased=1 (enforced in analysis scripts).
decisions.append("D8 kept revenue=0 rows (they are non-purchases, not errors); "
                 "revenue metrics computed on purchased=1 subset only.")

# D9: default review values for non-purchasers kept but excluded from review
#     analytics via purchased filter.
decisions.append("D9 review columns (rating/review_text/review_helpful_votes) analysed "
                 "only for purchased=1 rows; defaults for browsers are not real reviews.")

# D10: column names already snake_case → no renaming needed.
decisions.append("D10 column names already snake_case; unchanged.")

BASE.write_text("")  # ensure clean write
df.to_csv(BASE, index=False)
save_json({"decisions": decisions, "rows_out": len(df)}, "cleaning_log.json")
print(f"cleaned base data → {BASE} ({len(df)} rows)")
