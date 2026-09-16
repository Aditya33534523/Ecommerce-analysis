"""Full data-quality audit of the RAW file. Writes validation JSON +
documentation/data_quality_report.md. Modifies nothing."""
import numpy as np, pandas as pd
from project_utils import RAW, load_raw, save_json, DOCS

df = load_raw()
n = len(df)
results, issues = [], []

def check(name, ok, detail):
    results.append({"check": name, "status": "PASS" if ok else "FLAG", "detail": str(detail)})
    if not ok:
        issues.append(f"{name}: {detail}")
    print(f"[{'PASS' if ok else 'FLAG'}] {name}: {detail}")

# ---------- structural ----------
check("rows", True, n)
check("columns", True, df.shape[1])
check("column_names", True, list(df.columns))
check("dtypes", True, {c: str(t) for c, t in df.dtypes.items()})
check("duplicate_full_rows", int(df.duplicated().sum()) == 0, f"{df.duplicated().sum()} exact duplicate rows")
check("duplicate_session_id", df["session_id"].duplicated().sum() == 0,
      f"{df['session_id'].duplicated().sum()} duplicated session ids")
check("session_id_is_sequential_pk", df["session_id"].is_unique and df["session_id"].min() == 0,
      f"min={df['session_id'].min()}, max={df['session_id'].max()}, unique={df['session_id'].is_unique}")

# ---------- missing ----------
miss = df.isna().sum()
blanks = {c: int((df[c].astype(str).str.strip() == "").sum()) for c in df.columns if df[c].dtype == object}
check("missing_values", miss.sum() == 0, miss[miss > 0].to_dict() if miss.sum() else "none")
check("blank_strings", sum(blanks.values()) == 0, blanks)

# ---------- dates ----------
dates = pd.to_datetime(df["visit_date"], format="%d-%m-%Y", errors="coerce")
check("date_parse_all", dates.notna().all(), f"{dates.isna().sum()} unparseable")
check("date_range", True, f"{dates.min().date()} → {dates.max().date()}")
check("no_future_dates", (dates <= pd.Timestamp.today()).all(), "all in the past")
check("visit_day_matches_date", (dates.dt.day == df["visit_day"]).all(),
      f"{(dates.dt.day != df['visit_day']).sum()} mismatches")
check("visit_month_matches_date", (dates.dt.month == df["visit_month"]).all(),
      f"{(dates.dt.month != df['visit_month']).sum()} mismatches")
check("visit_weekday_mon0", (dates.dt.dayofweek == df["visit_weekday"]).all(),
      f"{(dates.dt.dayofweek != df['visit_weekday']).sum()} mismatches (encoding Monday=0)")
season_map = {12: 3, 1: 3, 2: 3, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 0, 10: 0, 11: 0}
expected_season = dates.dt.month.map(season_map)
check("visit_season_map_0=Autumn", (expected_season == df["visit_season"]).all(),
      f"{(expected_season != df['visit_season']).sum()} mismatches")

# ---------- numeric ranges ----------
check("unit_price_positive", (df["unit_price"] > 0).all(),
      f"min={df['unit_price'].min():.2f}, max={df['unit_price'].max():.2f}")
check("quantity_in_1_4", df["quantity"].between(1, 4).all(),
      f"values={sorted(df['quantity'].unique())}")
check("discount_percent_allowed", set(df["discount_percent"]) <= {0, 5, 10, 15, 20, 25, 30},
      f"values={sorted(df['discount_percent'].unique())}")
check("discount_amount_nonneg", (df["discount_amount"] >= 0).all(), f"min={df['discount_amount'].min()}")
check("revenue_nonneg", (df["revenue"] >= 0).all(), f"min={df['revenue'].min()}, max={df['revenue'].max():.2f}")
check("flags_binary", all(set(df[c]) <= {0, 1} for c in
      ["added_to_cart", "purchased", "cart_abandoned"]), "added/purchased/abandoned all 0-1")
check("rating_1_5_when_purchased", df.loc[df.purchased == 1, "rating"].between(1, 5).all(),
      f"purchaser ratings {sorted(df.loc[df.purchased==1,'rating'].unique())}")
check("helpful_votes_nonneg", (df["review_helpful_votes"] >= 0).all(), "ok")

# ---------- consistency (funnel + finance) ----------
gross = (df["unit_price"] * df["quantity"]).round(2)
rev_expect = (gross * (1 - df["discount_percent"] / 100)).round(2)
disc_expect = (gross * df["discount_percent"] / 100).round(2)
bad_rev = (np.abs(rev_expect - df["revenue"]) > 0.02) & (df["purchased"] == 1)
check("revenue_formula_purchased", bad_rev.sum() == 0,
      f"{bad_rev.sum()} purchased rows violate revenue=price*qty*(1-disc%) (tol 0.02)")
check("nonpurchase_revenue_zero", (df.loc[df.purchased == 0, "revenue"] == 0).all(),
      f"{(df.loc[df.purchased==0,'revenue']!=0).sum()} non-purchase rows with revenue>0")
bad_disc = (np.abs(disc_expect - df["discount_amount"]) > 0.02) & (df["discount_percent"] > 0)
check("discount_amount_formula", bad_disc.sum() == 0, f"{bad_disc.sum()} mismatches")
check("purchased_implies_cart", ((df.purchased == 1) <= (df.added_to_cart == 1)).all(),
      f"{((df.purchased==1)&(df.added_to_cart==0)).sum()} purchases without add-to-cart")
abandon_ok = ((df.added_to_cart == 1) & (df.purchased == 0)) == (df.cart_abandoned == 1)
check("abandoned_iff_carted_not_purchased", abandon_ok.all(), f"{(~abandon_ok).sum()} funnel violations")

# ---------- categorical / integrity ----------
for col, allowed in [("device_type", {0, 1, 2}), ("user_type", {0, 1}),
                     ("marketing_channel", set(range(6))), ("product_category", set(range(8))),
                     ("payment_method", set(range(6)))]:
    check(f"{col}_codes", set(df[col]) <= allowed, f"distinct={sorted(df[col].unique())}")
pc = df.groupby("product_id")["product_category"].nunique()
check("product_maps_to_one_category", pc.max() == 1, f"{(pc > 1).sum()} products with >1 category")
check("cardinality", True, {c: int(df[c].nunique()) for c in
      ["customer_id", "product_id", "product_category", "location", "marketing_channel"]})

# ---------- derived-column re-validation ----------
max_rev = df["revenue"].max()
check("revenue_normalized", np.abs(df["revenue"] / max_rev - df["revenue_normalized"]).max() < 1e-6,
      "= revenue / max(revenue), max deviation "
      f"{np.abs(df['revenue']/max_rev - df['revenue_normalized']).max():.2e}")
q = df["time_on_site_sec"].quantile([.25, .5, .75])
bucket_calc = pd.qcut(df["time_on_site_sec"].rank(method="first"), 4,
                      labels=["Very Short", "Short", "Long", "Very Long"])
match = (bucket_calc.astype(str) == df["session_duration_bucket"]).mean()
check("duration_bucket_vs_quartiles", match > 0.95,
      f"{match:.1%} consistent with quartile cuts (q25={q[.25]:.0f}, q50={q[.5]:.0f}, q75={q[.75]:.0f}); "
      "bucket kept as-is, not overwritten")

# ---------- review-field defaults ----------
nonp = df[df.purchased == 0]
check("review_defaults_on_nonpurchases",
      bool((nonp["rating"] == 4).all() and (nonp["review_text"] == 1).all()
           and (nonp["review_helpful_votes"] == 0).all()),
      f"non-purchasers: rating={sorted(nonp.rating.unique())}, review_text={sorted(nonp.review_text.unique())}, "
      "votes=0 → review analytics restricted to purchased=1")

# ---------- outliers (flag only) ----------
def iqr_flags(s):
    q1, q3 = s.quantile([.25, .75]); iqr = q3 - q1
    return int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
check("outliers_flag_only", True,
      {"unit_price": iqr_flags(df["unit_price"]), "revenue_purchased": iqr_flags(df.loc[df.purchased == 1, "revenue"]),
       "time_on_site": iqr_flags(df["time_on_site_sec"])})

# ---------- persist ----------
ok = not issues
save_json({"rows": n, "cols": df.shape[1],
           "date_min": str(dates.min().date()), "date_max": str(dates.max().date()),
           "results": results}, "validation.json")

report = ["# Data Quality Report — Ecommerce.csv", "",
          f"**Rows:** {n} · **Columns:** {df.shape[1]} · "
          f"**Date range:** {dates.min().date()} → {dates.max().date()}", "",
          "## Verified findings (from the dataset itself)",
          "- Session-level funnel data: one product visit per row; `session_id` is the primary key.",
          "- `revenue = round(unit_price × quantity × (1 − discount_percent/100), 2)` on purchased rows; 0 otherwise.",
          "- `discount_amount = round(unit_price × quantity × discount_percent/100, 2)`.",
          "- Funnel integrity: purchased ⇒ added_to_cart; cart_abandoned ⇔ added & not purchased.",
          "- `visit_weekday` = Monday-0; `visit_season`: 0=Sep–Nov, 1=Mar–May, 2=Jun–Aug, 3=Dec–Feb.",
          "- `revenue_normalized` = revenue ÷ max(revenue).",
          "- Review columns carry defaults (rating 4 / text 1 / votes 0) for non-purchasers.",
          "- device/user/channel/category/payment/location are integer codes with no codebook → never label-guessed.",
          "", "## Full check results", "",
          "| Check | Status | Detail |", "|---|---|---|"]
report += [f"| {r['check']} | {r['status']} | {r['detail']} |" for r in results]
report += ["", "## Issues requiring attention", ""] + (["- " + i for i in issues] if issues else ["- None."])
(DOCS / "data_quality_report.md").write_text("\n".join(report))
print(f"\n{'ALL CHECKS PASSED' if ok else str(len(issues)) + ' ITEMS FLAGGED (documented, not silently fixed)'}")
