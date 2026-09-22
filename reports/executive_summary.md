# Executive Summary — E-Commerce Session Analytics (2024-01-01 → 2024-12-30)

*Generated automatically from the cleaned dataset. All figures come from the data run.*

## Headline KPIs
| KPI | Value |
|---|---|
| Sessions analysed | 25,000 |
| Orders (purchased sessions) | 5,616 |
| Overall conversion rate | 22.46% |
| Cart abandonment rate (of cart adds) | 65.15% |
| Net revenue | 10,116,169.06 |
| Gross revenue (pre-discount) | 11,107,779.58 |
| Discounts given | 991,610.57 (8.93% of gross) |
| Average order value (AOV) | 1,801.31 |
| Items per order | 2.5 |
| Revenue per session | 404.65 |

## Time
- Best month: **2024-08** (revenue 917,972.7, MoM 15.15%)
- Weakest month: **2024-11** (revenue 771,484.47)
- Peak quarter: **2024Q3** (revenue 2,619,096.78)

## Products & categories
- Top category by revenue: **Category 2** (20.14% of net revenue,
  conversion 22.3%, avg rating 3.712)
- Top 20% of products generate **35.75%** of revenue; top 20% of categories **39.23%**.
- Top products by revenue: P130, P292, P806, P49, P453.

## Channels & customers
- Strongest channel by revenue: **Channel 5** (1,820,824; conversion 23.6%)
- Weakest channel: **Channel 4** (conversion 21.7%)
- Repeat purchasers: 1159 of 4176 (27.75%);
  top-10 customers hold 1.25% of customer revenue.
- RFM segments: At-risk loyalists (244), Champions (682), Core (827), Hibernating (1426), New / Low-frequency (997).

## Discount & engagement observations (associations, not causal claims)
- Conversion in the **11-20%** discount band is 22.7%
  vs 22.4% with **no discount**; AOV 1,624 vs 1,992.
- Correlation of purchase flag with pages_viewed: 0.01;
  with time_on_site: 0.03;
  with discount_percent: 0.00.

## Method & limitations
- Session-grain data; an "order" is a purchased session (one product, qty 1–4).
- Revenue metrics computed on purchased sessions only (non-purchase revenue is structurally 0).
- device/user_type/channel/category/payment/location are unlabeled integer codes —
  labelled generically, never guessed (see documentation/data_quality_report.md).
- Single year of data → no YoY analysis; seasonality claims limited to 2024 patterns.
- Descriptive/associative analysis only; no causal inference.
