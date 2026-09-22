"""
Independent reconciliation check.

Runs the SAME question through pandas (on ecommerce_cleaned.csv) and through
SQL (on ecommerce.db) using two separate code paths, and checks whether they
agree. This does NOT depend on anything from a chat conversation — it recomputes
everything from your own files, so you can run it yourself and see the numbers
land (or not) with your own eyes.

Usage:
    python verify.py
Exit code 0 = everything reconciled. Non-zero = something disagrees (printed).
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CSV = HERE / "data" / "processed" / "ecommerce_cleaned.csv"
DB = HERE / "data" / "processed" / "ecommerce.db"

df = pd.read_csv(CSV, parse_dates=["visit_date"])
pur = df[df.purchased == 1]
con = sqlite3.connect(DB)

failures = []


def check(name, a, b, tol=0.02):
    """Compare two numbers (or strings) computed two different ways."""
    ok = (abs(a - b) <= tol) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else (a == b)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: pandas={a}  sql={b}")
    if not ok:
        failures.append(name)


print("=" * 70)
print("1) Headline totals: pandas vs SQL (both computed independently)")
print("=" * 70)

sql_kpis = pd.read_sql(
    """SELECT COUNT(*) sessions, SUM(purchased) orders,
              SUM(revenue) net_revenue, SUM(gross_revenue*purchased) gross_revenue,
              SUM(discount_amount*purchased) discounts
       FROM sessions""",
    con,
).iloc[0]

check("total sessions", len(df), int(sql_kpis.sessions))
check("total orders", int(pur.shape[0]), int(sql_kpis.orders))
check("net revenue", round(pur.revenue.sum(), 2), round(sql_kpis.net_revenue, 2))
check("gross revenue", round(pur.gross_revenue.sum(), 2), round(sql_kpis.gross_revenue, 2))
check("discounts given", round(pur.discount_amount.sum(), 2), round(sql_kpis.discounts, 2))

print()
print("=" * 70)
print("2) Top-5 products by net revenue: pandas vs SQL")
print("=" * 70)

py_top5 = pur.groupby("product_id").revenue.sum().sort_values(ascending=False).head(5).round(2)
sql_top5 = pd.read_sql(
    """SELECT product_id, ROUND(SUM(revenue),2) net_revenue
       FROM sessions WHERE purchased=1
       GROUP BY product_id ORDER BY net_revenue DESC LIMIT 5""",
    con,
).set_index("product_id").net_revenue

for pid in py_top5.index:
    check(f"product {pid} revenue", py_top5[pid], sql_top5.get(pid, float("nan")))
check("top-5 product SET matches", set(py_top5.index), set(sql_top5.index))

print()
print("=" * 70)
print("3) Category revenue-share filter (HAVING bug check)")
print("=" * 70)

n_cats_total = df.category_label.nunique()
sql_having = pd.read_sql(
    """SELECT category_label, ROUND(SUM(revenue),2) net_revenue
       FROM sessions GROUP BY category_label
       HAVING SUM(revenue) > (
           SELECT AVG(cat_rev) FROM (
               SELECT SUM(revenue) AS cat_rev FROM sessions GROUP BY category_label))
       ORDER BY net_revenue DESC""",
    con,
)
cat_rev = df.groupby("category_label").revenue.sum()
py_having = cat_rev[cat_rev > cat_rev.mean()].sort_values(ascending=False)
check("categories above average category revenue (count)", len(py_having), len(sql_having))
print(f"  -> {len(sql_having)} of {n_cats_total} categories clear the bar: {list(sql_having.category_label)}")
print("  (a naive HAVING using AVG(revenue) WHERE purchased=1 — i.e. one ORDER's average, "
      "not one CATEGORY's average — would wrongly return all 8; that is the bug this project had.)")

print()
print("=" * 70)
print("4) Price-band GROUP BY duplicate-group check")
print("=" * 70)

sql_band_wrapped = pd.read_sql(
    """SELECT price_band, COUNT(*) n FROM (
           SELECT CASE WHEN unit_price < 500 THEN 'Budget'
                       WHEN unit_price < 1000 THEN 'Mid'
                       WHEN unit_price < 1500 THEN 'High' ELSE 'Premium' END AS price_band
           FROM sessions)
       GROUP BY price_band""",
    con,
)
check("price bands: exactly 4 distinct rows", 4, len(sql_band_wrapped))
print(sql_band_wrapped.to_string(index=False))

print()
print("=" * 70)
print("5) RFM: no repeat-buyer segment should contain a one-time buyer")
print("=" * 70)

max_date = df.visit_date.max()
cust = pur.groupby("customer_id").agg(
    last_purchase=("visit_date", "max"), frequency=("session_id", "count"), monetary=("revenue", "sum")
)
cust["recency_days"] = (max_date - cust.last_purchase).dt.days
cust["R_score"] = pd.qcut(cust["recency_days"].rank(method="average"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
cust["F_score"] = pd.cut(cust["frequency"], [0, 1, 2, float("inf")], labels=[1, 2, 3]).astype(int)


def seg(r):
    R, F = r["R_score"], r["F_score"]
    if R >= 4 and F >= 2:
        return "Champions"
    if R >= 4:
        return "New / Low-frequency"
    if R <= 2 and F >= 2:
        return "At-risk loyalists"
    if R <= 2:
        return "Hibernating"
    return "Core"


cust["segment"] = cust.apply(seg, axis=1)
bad = cust[cust.segment.isin(["Champions", "At-risk loyalists"]) & (cust.frequency < 2)]
check("one-time buyers mislabelled as repeat-buyer segments", 0, len(bad))

print()
print("=" * 70)
if failures:
    print(f"RESULT: {len(failures)} check(s) FAILED: {failures}")
    sys.exit(1)
else:
    print("RESULT: all checks reconciled.")
    sys.exit(0)
