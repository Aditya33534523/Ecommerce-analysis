"""Customer base, repeat behaviour, RFM segmentation (single-year data)."""
import numpy as np, pandas as pd
from project_utils import CLEANED, save_table, save_json

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1].copy()
max_date = df.visit_date.max()

cust = (pur.groupby("customer_id")
           .agg(last_purchase=("visit_date", "max"),
                frequency=("session_id", "count"),
                monetary=("revenue", "sum")))
cust["recency_days"] = (max_date - cust.last_purchase).dt.days
repeat = cust[cust.frequency >= 2]

# empirical check on the unlabeled user_type code (no guessing — measurement)
ut = (df.groupby("user_type_label")
        .agg(sessions=("session_id", "count"),
             sessions_per_customer=("session_id", lambda s: len(s) / df.loc[s.index, "customer_id"].nunique()),
             conversion=("purchased", "mean"),
             net_revenue=("revenue", lambda s: s[df.loc[s.index, "purchased"] == 1].sum()))
        .round(3))
save_table(ut.reset_index(), "user_type_check.csv")

summary = {
    "customers_with_sessions": int(df.customer_id.nunique()),
    "customers_with_purchase": int(cust.index.nunique()),
    "repeat_purchasers": int(len(repeat)),
    "repeat_rate_pct": round(100 * len(repeat) / cust.index.nunique(), 2),
    "one_time_buyers": int((cust.frequency == 1).sum()),
    "one_time_buyer_share_pct": round(100 * (cust.frequency == 1).mean(), 2),
    "avg_orders_per_purchasing_customer": round(float(cust.frequency.mean()), 2),
    "avg_revenue_per_customer": round(float(cust.monetary.mean()), 2),
    "top10_customer_revenue_share_pct": round(
        100 * cust.monetary.nlargest(10).sum() / cust.monetary.sum(), 2),
}
save_json(summary, "customer_kpis.json")

# ---- RFM scores: R = 5 for most recent; F/M = highest for the best customers ----
# Recency and monetary value are (near) continuous, so quintiles work. Identical values must get the SAME
# score, which is why recency uses rank(method="average").
# Frequency is different: ~72% of buyers purchased exactly once. Quintiles (rank "first") would give those
# identical one-time buyers scores 1-4 in customer-ID order - an arbitrary ranking. So frequency uses fixed,
# business-meaningful bins instead: 1 purchase / 2 purchases / 3+ purchases.
cust["R_score"] = pd.qcut(cust["recency_days"].rank(method="average"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
cust["F_score"] = pd.cut(cust["frequency"], [0, 1, 2, np.inf], labels=[1, 2, 3]).astype(int)
cust["M_score"] = pd.qcut(cust["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

def seg(r):
    R, F = r["R_score"], r["F_score"]
    if R >= 4 and F >= 2: return "Champions"             # recent AND repeat buyers
    if R >= 4:            return "New / Low-frequency"   # recent, single purchase
    if R <= 2 and F >= 2: return "At-risk loyalists"     # repeat buyers who have gone quiet
    if R <= 2:            return "Hibernating"           # single purchase, long ago
    return "Core"                                        # mid recency

cust["segment"] = cust.apply(seg, axis=1)
# self-check: the two "repeat buyer" segments must contain only customers with 2+ purchases
assert cust.loc[cust.segment.isin(["Champions", "At-risk loyalists"]), "frequency"].ge(2).all()
seg_table = cust.groupby("segment").agg(customers=("monetary", "count"), revenue=("monetary", "sum"),
                                        avg_recency_days=("recency_days", "mean"),
                                        avg_orders=("frequency", "mean"),
                                        avg_revenue=("monetary", "mean")).round(2)
seg_table["revenue_share_pct"] = (100 * seg_table.revenue / seg_table.revenue.sum()).round(2)
seg_table = seg_table[["customers", "revenue", "revenue_share_pct", "avg_recency_days", "avg_orders", "avg_revenue"]]
save_table(seg_table.reset_index(), "rfm_segments.csv")
save_table(pd.crosstab(cust.segment, cust.frequency).reset_index(), "rfm_segment_by_purchase_count.csv")
save_table(cust.sort_values("monetary", ascending=False).head(15).reset_index(), "top_customers.csv")
print(pd.Series(summary).to_string()); print(seg_table.to_string())
