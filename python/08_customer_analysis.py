"""Customer base, repeat behaviour, RFM segmentation (single-year data)."""
import pandas as pd
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
    "avg_orders_per_purchasing_customer": round(float(cust.frequency.mean()), 2),
    "avg_revenue_per_customer": round(float(cust.monetary.mean()), 2),
    "top10_customer_revenue_share_pct": round(
        100 * cust.monetary.nlargest(10).sum() / cust.monetary.sum(), 2),
}
save_json(summary, "customer_kpis.json")

# ---- RFM scores: R = 5 for most recent; F/M = 5 for highest ----
# rank(method="first") makes all values unique, so qcut never fails on ties
score_map = [("recency_days", "R_score", [5, 4, 3, 2, 1]),   # ascending rank → newest gets 5
             ("frequency",   "F_score", [1, 2, 3, 4, 5]),   # ascending rank → highest gets 5
             ("monetary",    "M_score", [1, 2, 3, 4, 5])]
for col, score_name, labels in score_map:
    cust[score_name] = pd.qcut(
        cust[col].rank(method="first"), 5, labels=labels).astype(int)

def seg(r):
    R, F = r["R_score"], r["F_score"]   # item access — can't hit attribute-name issues
    if R >= 4 and F >= 4: return "Champions"
    if R >= 4 and F <= 2: return "New / Low-frequency"
    if R <= 2 and F >= 4: return "At-risk loyalists"
    if R <= 2:            return "Hibernating"
    return "Core"

cust["segment"] = cust.apply(seg, axis=1)
seg_table = cust.groupby("segment").agg(customers=("monetary", "count"),
                                        revenue=("monetary", "sum")).round(2)
seg_table["revenue_share_pct"] = (100 * seg_table.revenue / seg_table.revenue.sum()).round(2)
save_table(seg_table.reset_index(), "rfm_segments.csv")
save_table(cust.sort_values("monetary", ascending=False).head(15).reset_index(), "top_customers.csv")
print(pd.Series(summary).to_string()); print(seg_table.to_string())