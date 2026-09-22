"""KPIs + revenue/conversion breakdowns + Pareto + discount analysis."""
import numpy as np, pandas as pd
from project_utils import CLEANED, save_table, save_json

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1]

kpis = {
    "total_sessions": len(df),
    "total_orders": int(len(pur)),
    "units_sold": int(pur.quantity.sum()),
    "gross_revenue": round(float(pur.gross_revenue.sum()), 2),
    "total_discount_given": round(float(pur.discount_amount.sum()), 2),
    "net_revenue": round(float(pur.revenue.sum()), 2),
    "discount_share_of_gross_pct": round(100 * pur.discount_amount.sum() / pur.gross_revenue.sum(), 2),
    "aov": round(float(pur.revenue.mean()), 2),
    "median_order_value": round(float(pur.revenue.median()), 2),
    "avg_unit_price_sold": round(float(pur.unit_price.mean()), 2),
    "items_per_order": round(float(pur.quantity.mean()), 2),
    "conversion_rate_pct": round(100 * df.purchased.mean(), 2),
    "cart_abandonment_rate_pct": round(100 * df.cart_abandoned.sum() / df.added_to_cart.sum(), 2),
    "revenue_per_session": round(float(pur.revenue.sum() / len(df)), 2),
}
save_json(kpis, "kpis.json")

def seg(col, fname):
    t = (df.groupby(col, observed=True)
           .agg(sessions=("session_id", "count"), orders=("purchased", "sum"),
                net_revenue=("revenue", lambda s: s[df.loc[s.index, "purchased"] == 1].sum()),
                avg_order_value=("revenue", lambda s: s[df.loc[s.index, "purchased"] == 1].mean() \
                                 if df.loc[s.index, "purchased"].sum() else np.nan)))
    t["conversion_rate"] = (t.orders / t.sessions).round(4)
    t["revenue_share_pct"] = (100 * t.net_revenue / pur.revenue.sum()).round(2)
    t["revenue_per_session"] = (t.net_revenue / t.sessions).round(2)
    # Round ONLY the money columns. conversion_rate is a fraction: t.round(2) would collapse every
    # rate to a whole percentage point (0.2274 -> 0.23) and invent gaps between groups.
    save_table(t.round({"net_revenue": 2, "avg_order_value": 2, "revenue_share_pct": 2,
                        "revenue_per_session": 2}).reset_index(), fname)
    return t

for col, f in [("channel_label", "sales_by_channel.csv"), ("device_label", "sales_by_device.csv"),
               ("user_type_label", "sales_by_user_type.csv"), ("payment_label", "sales_by_payment.csv"),
               ("discount_band", "sales_by_discount_band.csv"), ("season_name", "sales_by_season.csv"),
               ("weekday_name", "sales_by_weekday.csv"), ("category_label", "sales_by_category.csv")]:
    seg(col, f)

# weekend vs weekday
wk = df.groupby("is_weekend").agg(sessions=("session_id", "count"),
                                  conversion=("purchased", "mean")).round(4)
wk.index = ["Weekday", "Weekend"]
save_table(wk.reset_index(), "sales_weekday_vs_weekend.csv")

# Pareto — products & categories
for by, f in [("product_id", "pareto_products.csv"), ("category_label", "pareto_categories.csv")]:
    p = (pur.groupby(by).revenue.sum().sort_values(ascending=False).to_frame("net_revenue"))
    p["cum_share_pct"] = (100 * p.net_revenue.cumsum() / p.net_revenue.sum()).round(2)
    top20_n = max(1, int(np.ceil(0.2 * len(p))))
    n80 = int((p.cum_share_pct < 80).sum()) + 1
    save_json({"top_20pct_entities": by, "count": top20_n, "entities_total": int(len(p)),
               # ceil() means "top 20%" of 8 categories is 2 categories = 25% of them; report the real share
               "share_of_entities_pct": round(100 * top20_n / len(p), 2),
               "revenue_share_pct": round(float(p.cum_share_pct.iloc[top20_n - 1]), 2),
               "entities_for_80pct_revenue": n80,
               "share_of_entities_for_80pct": round(100 * n80 / len(p), 2)},
              f.replace(".csv", ".json"))
    save_table(p.reset_index(), f)

# locations
loc = (pur.groupby("location").revenue.sum().sort_values(ascending=False).head(15)
          .to_frame("net_revenue"))
loc["share_pct"] = (100 * loc.net_revenue / pur.revenue.sum()).round(2)
save_table(loc.reset_index(), "top_locations_by_revenue.csv")

print(pd.Series(kpis).to_string())
