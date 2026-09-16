# Data Quality Report — Ecommerce.csv

**Rows:** 25000 · **Columns:** 29 · **Date range:** 2024-01-01 → 2024-12-30

## Verified findings (from the dataset itself)
- Session-level funnel data: one product visit per row; `session_id` is the primary key.
- `revenue = round(unit_price × quantity × (1 − discount_percent/100), 2)` on purchased rows; 0 otherwise.
- `discount_amount = round(unit_price × quantity × discount_percent/100, 2)`.
- Funnel integrity: purchased ⇒ added_to_cart; cart_abandoned ⇔ added & not purchased.
- `visit_weekday` = Monday-0; `visit_season`: 0=Sep–Nov, 1=Mar–May, 2=Jun–Aug, 3=Dec–Feb.
- `revenue_normalized` = revenue ÷ max(revenue).
- Review columns carry defaults (rating 4 / text 1 / votes 0) for non-purchasers.
- device/user/channel/category/payment/location are integer codes with no codebook → never label-guessed.

## Full check results

| Check | Status | Detail |
|-------|--------|--------|
| rows  |  PASS  |  25000 |
|columns|  PASS  |  29    |
|column_names | PASS | ['customer_id', 'session_id', 'visit_date', 'device_type', 'user_type', 'marketing_channel', 'product_id', 'product_category', 'unit_price', 'quantity', 'discount_percent', 'discount_amount', 'revenue', 'pages_viewed', 'time_on_site_sec', 'added_to_cart', 'purchased', 'cart_abandoned', 'rating', 'review_text', 'review_helpful_votes', 'payment_method', 'visit_day', 'visit_month', 'visit_weekday', 'visit_season', 'session_duration_bucket', 'revenue_normalized', 'location'] |
| dtypes | PASS | {'customer_id': 'int64', 'session_id': 'int64', 'visit_date': 'str', 'device_type': 'int64', 'user_type': 'int64', 'marketing_channel': 'int64', 'product_id': 'int64', 'product_category': 'int64', 'unit_price': 'float64', 'quantity': 'int64', 'discount_percent': 'int64', 'discount_amount': 'float64', 'revenue': 'float64', 'pages_viewed': 'int64', 'time_on_site_sec': 'int64', 'added_to_cart': 'int64', 'purchased': 'int64', 'cart_abandoned': 'int64', 'rating': 'int64', 'review_text': 'int64', 'review_helpful_votes': 'int64', 'payment_method': 'int64', 'visit_day': 'int64', 'visit_month': 'int64', 'visit_weekday': 'int64', 'visit_season': 'int64', 'session_duration_bucket': 'str', 'revenue_normalized': 'float64', 'location': 'int64'} |
| duplicate_full_rows | PASS | 0 exact duplicate rows |
| duplicate_session_id | PASS | 0 duplicated session ids |
| session_id_is_sequential_pk | PASS | min=0, max=24999, unique=True |
| missing_values | PASS | none |
| blank_strings | PASS | {} |
| date_parse_all | PASS | 0 unparseable |
| date_range | PASS | 2024-01-01 → 2024-12-30 |
| no_future_dates | PASS | all in the past |
| visit_day_matches_date | PASS | 0 mismatches |
| visit_month_matches_date | PASS | 0 mismatches |
| visit_weekday_mon0 | PASS | 0 mismatches (encoding Monday=0) |
| visit_season_map_0=Autumn | PASS | 0 mismatches |
| unit_price_positive | PASS | min=50.05, max=1999.83 |
| quantity_in_1_4 | PASS | values=[np.int64(1), np.int64(2), np.int64(3), np.int64(4)] |
| discount_percent_allowed | PASS | values=[np.int64(0), np.int64(5), np.int64(10), np.int64(15), np.int64(20), np.int64(25), np.int64(30)] |
| discount_amount_nonneg | PASS | min=0.0 |
| revenue_nonneg | PASS | min=0.0, max=7889.36 |
| flags_binary | PASS | added/purchased/abandoned all 0-1 |
| rating_1_5_when_purchased | PASS | purchaser ratings [np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5)] |
| helpful_votes_nonneg | PASS | ok |
| revenue_formula_purchased | PASS | 0 purchased rows violate revenue=price*qty*(1-disc%) (tol 0.02) |
| nonpurchase_revenue_zero | PASS | 0 non-purchase rows with revenue>0 |
| discount_amount_formula | PASS | 0 mismatches |
| purchased_implies_cart | PASS | 0 purchases without add-to-cart |
| abandoned_iff_carted_not_purchased | PASS | 0 funnel violations |
| device_type_codes | PASS | distinct=[np.int64(0), np.int64(1), np.int64(2)] |
| user_type_codes | PASS | distinct=[np.int64(0), np.int64(1)] |
| marketing_channel_codes | PASS | distinct=[np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5)] |
| product_category_codes | PASS | distinct=[np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7)] |
| payment_method_codes | PASS | distinct=[np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5)] |
| product_maps_to_one_category | FLAG | 899 products with >1 category |
| cardinality | PASS | {'customer_id': 8442, 'product_id': 899, 'product_category': 8, 'location': 225, 'marketing_channel': 6} |
| revenue_normalized | PASS | = revenue / max(revenue), max deviation 5.00e-10 |
| duration_bucket_vs_quartiles | PASS | 99.9% consistent with quartile cuts (q25=453, q50=903, q75=1355); bucket kept as-is, not overwritten |
| review_defaults_on_nonpurchases | PASS | non-purchasers: rating=[np.int64(4)], review_text=[np.int64(1)], votes=0 → review analytics restricted to purchased=1 |
| outliers_flag_only | PASS | {'unit_price': 0, 'revenue_purchased': 214, 'time_on_site': 0} |

## Issues requiring attention

- product_maps_to_one_category: 899 products with >1 category
