"""EDA: shape, cardinality, funnel, categorical distributions."""
import pandas as pd
from project_utils import CLEANED, save_table, save_json

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1]

overview = {
    "rows": len(df), "columns": df.shape[1],
    "date_min": str(df.visit_date.min().date()), "date_max": str(df.visit_date.max().date()),
    "unique_customers": int(df.customer_id.nunique()),
    "unique_products": int(df.product_id.nunique()),
    "categories": int(df.product_category.nunique()),
    "locations": int(df.location.nunique()),
    "sessions": len(df), "orders": int(df.purchased.sum()),
    "overall_conversion_rate": round(float(df.purchased.mean()), 4),
    "cart_adds": int(df.added_to_cart.sum()),
    "cart_abandonment_rate": round(float(df.cart_abandoned.sum() / df.added_to_cart.sum()), 4),
}
funnel = (df.groupby("funnel_stage").agg(sessions=("session_id", "count"))
            .reindex(["Browse Only", "Cart Abandoned", "Purchased"]))
funnel["share_pct"] = (100 * funnel.sessions / len(df)).round(2)
save_table(funnel.reset_index(), "funnel.csv")

for col, fname in [("device_label", "by_device.csv"), ("user_type_label", "by_user_type.csv"),
                   ("channel_label", "by_channel.csv"), ("category_label", "by_category_counts.csv"),
                   ("payment_label", "by_payment.csv"), ("weekday_name", "by_weekday.csv"),
                   ("season_name", "by_season.csv"), ("discount_band", "by_discount_band.csv")]:
    t = df.groupby(col, observed=True).agg(
        sessions=("session_id", "count"),
        conversion_rate=("purchased", "mean")).round(4)
    save_table(t.reset_index(), fname)

save_json(overview, "overview.json")
print(pd.Series(overview).to_string())
