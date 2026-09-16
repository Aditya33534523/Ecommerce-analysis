"""Category & product performance using real purchased sessions."""
import pandas as pd
from project_utils import CLEANED, save_table

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1].copy()

# --- session-level metrics (all sessions, per category) ---
all_sess = (df.groupby("category_label", observed=True)
              .agg(sessions=("session_id", "count"),
                   conversion_rate=("purchased", "mean"),
                   avg_unit_price=("unit_price", "mean"),
                   avg_discount_pct=("discount_percent", "mean"))
              .round(3))

# --- purchase-level metrics (purchased sessions only, per category) ---
purch = (pur.groupby("category_label", observed=True)
            .agg(orders=("session_id", "count"),
                 units_sold=("quantity", "sum"),
                 net_revenue=("revenue", "sum"),
                 avg_rating=("rating", "mean"))
            .round(3))

cat = all_sess.join(purch).sort_values("net_revenue", ascending=False)
cat["orders"] = cat["orders"].fillna(0).astype(int)
cat["units_sold"] = cat["units_sold"].fillna(0).astype(int)
cat["revenue_share_pct"] = (100 * cat.net_revenue / cat.net_revenue.sum()).round(2)
save_table(cat.reset_index(), "product_category_summary.csv")

# --- product-level (purchased sessions only) ---
prod = (pur.groupby("product_id")
           .agg(orders=("session_id", "count"), units=("quantity", "sum"),
                net_revenue=("revenue", "sum"),
                category=("category_label", "first"),
                avg_price=("unit_price", "mean"), avg_rating=("rating", "mean"))
           .round(2))
save_table(prod.sort_values("net_revenue", ascending=False).head(15).reset_index(), "top_products.csv")
save_table(prod.sort_values("net_revenue").head(15).reset_index(), "bottom_products.csv")
save_table(prod.sort_values("units", ascending=False).head(15).reset_index(), "top_products_by_units.csv")
print("Top 5 products by net revenue:")
print(prod.sort_values("net_revenue", ascending=False).head().to_string())
