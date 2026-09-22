"""Inferential statistics: which conversion differences are real, and which are just noise?

* chi-square test of independence (purchased x group) for every candidate driver
* Wilson 95% confidence intervals for every group's conversion rate
* Bonferroni threshold, because 13 variables are scanned at once
* the discount question: 0% vs 11-20% two-proportion z-test, revenue per session,
  is the basket mix the same across discount bands, and is the discount assigned independently
  of price / category / channel ... (i.e. is the comparison "as good as random")
* checkout funnel by user type

Association only. The dataset is observational (and looks simulated), so nothing here is a causal
claim and nothing generalises to real shoppers - it describes THIS dataset.
"""
import numpy as np, pandas as pd
from scipy import stats
from project_utils import CLEANED, save_table, save_json

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1]

# ------------------------------------------------------------------ helpers
def wilson(k, n, z=1.96):
    """Wilson score interval for a proportion (better than the normal approximation)."""
    p = k / n
    d = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return centre - half, centre + half

def two_prop(a, b):
    """b minus a for two 0/1 series: difference (points), unpooled 95% CI, pooled z-test p-value."""
    diff = b.mean() - a.mean()
    pool = (a.sum() + b.sum()) / (len(a) + len(b))
    z = diff / np.sqrt(pool * (1 - pool) * (1 / len(a) + 1 / len(b)))
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return {"n_a": int(len(a)), "n_b": int(len(b)),
            "rate_a_pct": round(float(100 * a.mean()), 2), "rate_b_pct": round(float(100 * b.mean()), 2),
            "diff_pts": round(float(100 * diff), 2),
            "ci_low_pts": round(float(100 * (diff - 1.96 * se)), 2),
            "ci_high_pts": round(float(100 * (diff + 1.96 * se)), 2),
            "p_value": float(2 * (1 - stats.norm.cdf(abs(z))))}

def quartiles(s):
    """Quartile bins labelled with their real value ranges, e.g. 'Q2: 8-13'."""
    q = pd.qcut(s, 4, duplicates="drop")
    cats = list(q.cat.categories)
    names = {}
    for i, iv in enumerate(cats, 1):
        lo = int(s.min()) if i == 1 else int(cats[i - 2].right) + 1
        names[iv] = f"Q{i}: {lo}-{int(iv.right)}"
    return q.map(names).astype(str)

df["pages_q"] = quartiles(df.pages_viewed)
df["time_q"] = quartiles(df.time_on_site_sec)

ORDER = {"weekday_name": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
         "discount_band": ["0%", "1-10%", "11-20%", "21-30%"],
         "price_band": ["Budget", "Mid", "High", "Premium"],
         "season_name": ["Winter (Dec-Feb)", "Spring (Mar-May)", "Summer (Jun-Aug)", "Autumn (Sep-Nov)"]}

# ------------------------------------------------------------------ 1) scan every candidate driver
VARS = {"channel": "channel_label", "device": "device_label", "discount band": "discount_band",
        "user type": "user_type_label", "weekday": "weekday_name", "season": "season_name",
        "product category": "category_label", "payment method": "payment_label", "price band": "price_band",
        "pages viewed (quartile)": "pages_q", "time on site (quartile)": "time_q",
        "quantity": "quantity", "location": "location"}
ALPHA = 0.05 / len(VARS)                      # Bonferroni: 13 simultaneous tests

tests, groups = [], []
for name, col in VARS.items():
    ct = pd.crosstab(df[col], df.purchased)
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    tests.append({"variable": name, "levels": int(ct.shape[0]), "chi2": round(chi2, 2), "dof": int(dof),
                  "p_value": p, "significant_bonferroni": bool(p < ALPHA), "nominal_significant": bool(p < 0.05)})
    if name == "location":                     # 225 levels - test only, no per-group table
        continue
    for g, r in ct.iterrows():
        n, k = int(r.sum()), int(r.get(1, 0))
        lo, hi = wilson(k, n)
        groups.append({"variable": name, "group": str(g), "sessions": n, "orders": k,
                       "conversion_pct": round(100 * k / n, 2),
                       "ci_low_pct": round(100 * lo, 2), "ci_high_pct": round(100 * hi, 2)})
tests = pd.DataFrame(tests).sort_values("p_value")
groups = pd.DataFrame(groups)
# natural ordering of the groups inside each variable (weekday Mon..Sun etc.)
rank = {}
for var, col in VARS.items():
    order = ORDER.get(col) or (sorted(groups.loc[groups.variable == var, "group"]))
    for i, g in enumerate(order):
        rank[(var, g)] = i
groups["_o"] = [rank.get((v, g), 99) for v, g in zip(groups.variable, groups.group)]
groups = groups.sort_values(["variable", "_o"]).drop(columns="_o")
save_table(tests, "conversion_tests.csv")
save_table(groups, "conversion_by_group_ci.csv")

# ------------------------------------------------------------------ 2) the discount question
BANDS = ["0%", "1-10%", "11-20%", "21-30%"]
a = df.loc[df.discount_band == "0%", "purchased"]
b = df.loc[df.discount_band == "11-20%", "purchased"]
disc_test = two_prop(a, b)

# 2a) is the basket the same across bands?  (purchased sessions)
mix = pur.groupby("discount_band").agg(
    orders=("session_id", "count"), avg_discount_pct=("discount_percent", "mean"),
    avg_unit_price=("unit_price", "mean"), avg_quantity=("quantity", "mean"),
    avg_gross_order=("gross_revenue", "mean"), avg_net_order=("revenue", "mean")).loc[BANDS]
base = mix.loc["0%"]
mix["net_change_vs_0pct"] = 100 * (mix.avg_net_order / base.avg_net_order - 1)
mix["expected_change_from_discount_alone"] = -mix.avg_discount_pct
mix["gross_change_vs_0pct"] = 100 * (mix.avg_gross_order / base.avg_gross_order - 1)
g0 = pur.loc[pur.discount_band == "0%", "gross_revenue"]
mix["gross_vs_0pct_p_value"] = [np.nan if band == "0%" else
                               stats.ttest_ind(g0, pur.loc[pur.discount_band == band, "gross_revenue"],
                                               equal_var=False).pvalue for band in BANDS]
save_table(mix.round(4).reset_index(), "discount_mix_check.csv")

# 2b) revenue per session by band (conversion x order value in one number)
g = df.groupby("discount_band")
rps = g.agg(sessions=("purchased", "size"), orders=("purchased", "sum"), net_revenue=("revenue", "sum")).loc[BANDS]
rps["discount_given"] = pur.groupby("discount_band").discount_amount.sum().reindex(BANDS)
rps["conversion_pct"] = 100 * rps.orders / rps.sessions
rps["aov_net"] = rps.net_revenue / rps.orders
rps["revenue_per_session"] = rps.net_revenue / rps.sessions
rps["rps_change_vs_0pct"] = 100 * (rps.revenue_per_session / rps.loc["0%", "revenue_per_session"] - 1)
save_table(rps.round(4).reset_index(), "revenue_per_session_by_discount.csv")

# 2c) is the discount assigned independently of everything else?  (p > 0.05 = no detectable link)
assign = []
for name, col in [("channel", "channel_label"), ("device", "device_label"), ("user type", "user_type_label"),
                  ("product category", "category_label"), ("price band", "price_band"),
                  ("weekday", "weekday_name"), ("season", "season_name"), ("payment method", "payment_label")]:
    p = stats.chi2_contingency(pd.crosstab(df[col], df.discount_percent))[1]
    assign.append({"variable": name, "test": "chi-square vs discount level", "statistic": "p-value", "value": round(p, 4)})
for name, col in [("unit_price", "unit_price"), ("quantity", "quantity"),
                  ("pages_viewed", "pages_viewed"), ("time_on_site_sec", "time_on_site_sec")]:
    assign.append({"variable": name, "test": "Pearson r with discount_percent", "statistic": "r",
                   "value": round(df[col].corr(df.discount_percent), 4)})
assign = pd.DataFrame(assign)
save_table(assign, "discount_assignment_tests.csv")

# ------------------------------------------------------------------ 3) checkout funnel by user type
ut = df.groupby("user_type_label").agg(sessions=("purchased", "size"), cart_adds=("added_to_cart", "sum"),
                                       orders=("purchased", "sum"))
ut["cart_rate_pct"] = 100 * ut.cart_adds / ut.sessions
ut["cart_to_purchase_pct"] = 100 * ut.orders / ut.cart_adds
ut["conversion_pct"] = 100 * ut.orders / ut.sessions
for col, num, den in [("conversion", "orders", "sessions"), ("cart_to_purchase", "orders", "cart_adds"),
                      ("cart_rate", "cart_adds", "sessions")]:
    ci = [wilson(k, n) for k, n in zip(ut[num], ut[den])]
    ut[f"{col}_ci_low_pct"] = [100 * x[0] for x in ci]
    ut[f"{col}_ci_high_pct"] = [100 * x[1] for x in ci]
save_table(ut.round(4).reset_index(), "user_type_funnel.csv")

hi, lo = ut.conversion_pct.idxmax(), ut.conversion_pct.idxmin()
gap = two_prop(df.loc[df.user_type_label == lo, "purchased"], df.loc[df.user_type_label == hi, "purchased"])
carted = df[df.added_to_cart == 1]
gap_checkout = two_prop(carted.loc[carted.user_type_label == lo, "purchased"],
                        carted.loc[carted.user_type_label == hi, "purchased"])
multi_type = int((df.groupby("customer_id").user_type.nunique() > 1).sum())

# ------------------------------------------------------------------ summary for the report / charts
summary = {
    "note": "association only - observational, apparently synthetic data",
    "alpha_bonferroni": round(ALPHA, 5), "n_variables_tested": len(VARS),
    "tests": {r.variable: {"chi2": r.chi2, "dof": r.dof, "p": float(r.p_value),
                           "significant": r.significant_bonferroni, "nominal": bool(r.nominal_significant)}
              for r in tests.itertuples()},
    "discount_0_vs_11_20": disc_test,
    "discount_mix": {band: {"avg_discount_pct": round(float(mix.loc[band, "avg_discount_pct"]), 2),
                            "avg_gross_order": round(float(mix.loc[band, "avg_gross_order"]), 2),
                            "avg_net_order": round(float(mix.loc[band, "avg_net_order"]), 2),
                            "net_change_pct": round(float(mix.loc[band, "net_change_vs_0pct"]), 1)} for band in BANDS},
    "revenue_per_session": {band: {"value": round(float(rps.loc[band, "revenue_per_session"]), 2),
                                   "change_vs_0pct": round(float(rps.loc[band, "rps_change_vs_0pct"]), 1)} for band in BANDS},
    "discount_assignment_min_p": round(float(assign.loc[assign.test.str.startswith("chi"), "value"].min()), 3),
    "user_type": {"higher": hi, "lower": lo,
                  "conversion_higher_pct": round(float(ut.loc[hi, "conversion_pct"]), 2),
                  "conversion_lower_pct": round(float(ut.loc[lo, "conversion_pct"]), 2),
                  "conversion_gap": gap,
                  "cart_rate_higher_pct": round(float(ut.loc[hi, "cart_rate_pct"]), 2),
                  "cart_rate_lower_pct": round(float(ut.loc[lo, "cart_rate_pct"]), 2),
                  "cart_to_purchase_higher_pct": round(float(ut.loc[hi, "cart_to_purchase_pct"]), 2),
                  "cart_to_purchase_lower_pct": round(float(ut.loc[lo, "cart_to_purchase_pct"]), 2),
                  "cart_to_purchase_gap": gap_checkout,
                  "customers_seen_with_both_types": multi_type,
                  "customers_total": int(df.customer_id.nunique())},
}
save_json(summary, "stat_tests.json")

pd.set_option("display.width", 200)
print(tests[["variable", "levels", "chi2", "dof", "p_value", "significant_bonferroni"]].to_string(index=False))
print(f"\nBonferroni alpha = {ALPHA:.4f}")
print("\ndiscount 0% vs 11-20%:", disc_test)
print("\nuser type gap:", gap["diff_pts"], "pts  CI", (gap["ci_low_pts"], gap["ci_high_pts"]))
