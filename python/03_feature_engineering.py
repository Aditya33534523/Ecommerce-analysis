"""Adds analytically valid derived fields; re-verifies every file-supplied
derived column; produces the single analysis-ready dataset."""
import numpy as np, pandas as pd
from project_utils import BASE, CLEANED, PROC, save_table, save_json, apply_labels, \
    DEVICE_LABELS, USERTYPE_LABELS, CHANNEL_LABELS, CATEGORY_LABELS, PAYMENT_LABELS, \
    WEEKDAY_LABELS, SEASON_LABELS

df = pd.read_csv(BASE, parse_dates=["visit_date"])

# --- recompute-and-verify (never blind-trust) ---
gross = (df.unit_price * df.quantity).round(2)
rev_calc = (gross * (1 - df.discount_percent / 100)).round(2)
mismatch = df[(df.purchased == 1) & (np.abs(rev_calc - df.revenue) > 0.02)]
if len(mismatch):
    mismatch.to_csv(PROC / "revenue_mismatches.csv", index=False)
    print(f"WARNING {len(mismatch)} revenue mismatches → processed/revenue_mismatches.csv")
else:
    print("revenue verified: revenue == price × qty × (1 − disc%) on all purchased rows")

# --- engineered features ---
df["gross_revenue"]    = gross                                   # list-price value of basket
df["effective_price"]  = np.where(df.purchased == 1, (df.revenue / df.quantity).round(2), np.nan)
df["funnel_stage"]     = np.select(
    [df.purchased == 1, df.added_to_cart == 1],
    ["Purchased", "Cart Abandoned"], default="Browse Only")
df["discount_band"]    = pd.cut(df.discount_percent, [-1, 0, 10, 20, 100],
                                labels=["0%", "1-10%", "11-20%", "21-30%"])
df["price_band"]       = pd.qcut(df.unit_price.rank(method="first"), 4,
                                 labels=["Budget", "Mid", "High", "Premium"])
df["year_month"]       = df.visit_date.dt.strftime("%Y-%m")
df["quarter"]          = "Q" + df.visit_date.dt.quarter.astype(str)
df["month_name"]       = df.visit_date.dt.strftime("%b")
df["is_weekend"]       = (df.visit_weekday >= 5).astype(int)
df["review_valid"]     = (df.purchased == 1).astype(int)
df["device_label"]     = apply_labels(df.device_type, DEVICE_LABELS, "Device")
df["user_type_label"]  = apply_labels(df.user_type, USERTYPE_LABELS, "UserType")
df["channel_label"]    = apply_labels(df.marketing_channel, CHANNEL_LABELS, "Channel")
df["category_label"]   = apply_labels(df.product_category, CATEGORY_LABELS, "Category")
df["payment_label"]    = apply_labels(df.payment_method, PAYMENT_LABELS, "Payment")
df["weekday_name"]     = df.visit_weekday.map(WEEKDAY_LABELS)
df["season_name"]      = df.visit_season.map(SEASON_LABELS)

df.to_csv(CLEANED, index=False)
save_json({"features_added": ["gross_revenue", "effective_price", "funnel_stage", "discount_band",
           "price_band", "year_month", "quarter", "month_name", "is_weekend", "review_valid",
           "*_label decodes", "weekday_name", "season_name"],
           "rows": len(df), "cols": df.shape[1],
           "revenue_mismatches": int(len(mismatch))}, "feature_log.json")
print(f"analysis-ready dataset → {CLEANED} ({len(df)} rows × {df.shape[1]} cols)")
