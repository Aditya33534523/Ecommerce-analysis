"""Assembles the executive summary from computed artifacts only —
every number in the report comes from YOUR file's run."""
import pandas as pd
from project_utils import TABLES, load_json, ROOT

o  = load_json("overview.json"); k = load_json("kpis.json")
tk = load_json("time_series_kpis.json"); ck = load_json("customer_kpis.json")
pp = load_json("pareto_products.json"); pc = load_json("pareto_categories.json")
cat = pd.read_csv(TABLES / "product_category_summary.csv")
ch  = pd.read_csv(TABLES / "sales_by_channel.csv").sort_values("net_revenue", ascending=False)
db  = pd.read_csv(TABLES / "sales_by_discount_band.csv")
mon = pd.read_csv(TABLES / "monthly_series.csv")
top = pd.read_csv(TABLES / "top_products.csv").head(5)
rfm = pd.read_csv(TABLES / "rfm_segments.csv")
d0  = pd.read_csv(TABLES / "corr_behaviour.csv", index_col=0)
best_ch, worst_ch = ch.iloc[0], ch.iloc[-1]
db0 = db[db.discount_band.astype(str) == "0%"].iloc[0]
dbm = db.loc[db.conversion_rate.idxmax()]

md = f"""# Executive Summary — E-Commerce Session Analytics ({o['date_min']} → {o['date_max']})

*Generated automatically from the cleaned dataset. All figures come from the data run.*

## Headline KPIs
| KPI | Value |
|---|---|
| Sessions analysed | {k['total_sessions']:,} |
| Orders (purchased sessions) | {k['total_orders']:,} |
| Overall conversion rate | {k['conversion_rate_pct']}% |
| Cart abandonment rate (of cart adds) | {k['cart_abandonment_rate_pct']}% |
| Net revenue | {k['net_revenue']:,} |
| Gross revenue (pre-discount) | {k['gross_revenue']:,} |
| Discounts given | {k['total_discount_given']:,} ({k['discount_share_of_gross_pct']}% of gross) |
| Average order value (AOV) | {k['aov']:,} |
| Items per order | {k['items_per_order']} |
| Revenue per session | {k['revenue_per_session']} |

## Time
- Best month: **{tk['best_month']}** (revenue {tk['best_month_revenue']:,}, MoM {tk['best_month_growth_pct']}%)
- Weakest month: **{tk['worst_month']}** (revenue {tk['worst_month_revenue']:,})
- Peak quarter: **{tk['peak_quarter']}** (revenue {tk['peak_quarter_revenue']:,})

## Products & categories
- Top category by revenue: **{cat.iloc[0].category_label}** ({cat.iloc[0].revenue_share_pct}% of net revenue,
  conversion {cat.iloc[0].conversion_rate:.1%}, avg rating {cat.iloc[0].avg_rating})
- Top 20% of products generate **{pp['revenue_share_pct']}%** of revenue; top 20% of categories **{pc['revenue_share_pct']}%**.
- Top products by revenue: {", ".join("P"+str(p) for p in top.product_id)}.

## Channels & customers
- Strongest channel by revenue: **{best_ch.channel_label}** ({best_ch.net_revenue:,.0f}; conversion {best_ch.conversion_rate:.1%})
- Weakest channel: **{worst_ch.channel_label}** (conversion {worst_ch.conversion_rate:.1%})
- Repeat purchasers: {ck['repeat_purchasers']} of {ck['customers_with_purchase']} ({ck['repeat_rate_pct']}%);
  top-10 customers hold {ck['top10_customer_revenue_share_pct']}% of customer revenue.
- RFM segments: {", ".join(f"{r.segment} ({r.customers})" for r in rfm.itertuples())}.

## Discount & engagement observations (associations, not causal claims)
- Conversion in the **{dbm.discount_band}** discount band is {100*dbm.conversion_rate:.1f}%
  vs {100*db0.conversion_rate:.1f}% with **no discount**; AOV {dbm.avg_order_value:,.0f} vs {db0.avg_order_value:,.0f}.
- Correlation of purchase flag with pages_viewed: {d0.loc['purchased','pages_viewed']:.2f};
  with time_on_site: {d0.loc['purchased','time_on_site_sec']:.2f};
  with discount_percent: {d0.loc['purchased','discount_percent']:.2f}.

## Method & limitations
- Session-grain data; an "order" is a purchased session (one product, qty 1–4).
- Revenue metrics computed on purchased sessions only (non-purchase revenue is structurally 0).
- device/user_type/channel/category/payment/location are unlabeled integer codes —
  labelled generically, never guessed (see documentation/data_quality_report.md).
- Single year of data → no YoY analysis; seasonality claims limited to 2024 patterns.
- Descriptive/associative analysis only; no causal inference.
"""
out = ROOT / "reports" / "executive_summary.md"
out.write_text(md)
print(f"executive summary → {out}")
