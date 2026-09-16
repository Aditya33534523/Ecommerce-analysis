"""Descriptive statistics + plain-English interpretation, on real data.
Revenue/rating stats use purchased rows only (documented decision)."""
import numpy as np, pandas as pd
from project_utils import CLEANED, save_table

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1]

targets = {
    "unit_price (all sessions)":        df["unit_price"],
    "quantity (purchased)":             pur["quantity"],
    "discount_percent (all sessions)":  df["discount_percent"],
    "discount_amount (purchased)":      pur["discount_amount"],
    "net revenue per order (purchased)": pur["revenue"],
    "pages_viewed (all sessions)":      df["pages_viewed"],
    "time_on_site_sec (all sessions)":  df["time_on_site_sec"],
    "rating (purchased)":               pur["rating"],
}
rows = []
for name, s in targets.items():
    q1, q3 = s.quantile([.25, .75])
    mode = s.mode()
    rows.append({
        "variable": name, "count": int(s.count()), "mean": round(s.mean(), 2),
        "median": round(s.median(), 2),
        "mode": round(float(mode.iloc[0]), 2) if len(mode) else None,
        "min": round(s.min(), 2), "max": round(s.max(), 2),
        "range": round(s.max() - s.min(), 2),
        "std": round(s.std(), 2), "variance": round(s.var(), 2),
        "q1": round(q1, 2), "q3": round(q3, 2), "iqr": round(q3 - q1, 2),
        "p05": round(s.quantile(.05), 2), "p95": round(s.quantile(.95), 2),
        "cv": round(s.std() / s.mean(), 3) if s.mean() else None,
        "skew": round(s.skew(), 3), "kurtosis": round(s.kurtosis(), 3)})
stats = pd.DataFrame(rows)
save_table(stats, "statistical_summary.csv")

lines = ["# Statistical Summary — interpretation", ""]
for r in stats.itertuples():
    shape = ("strongly right-skewed" if r.skew > 1 else
             "moderately right-skewed" if r.skew > 0.5 else
             "roughly symmetric" if abs(r.skew) <= 0.5 else "left-skewed")
    disp = ("high relative dispersion" if (r.cv or 0) > 0.5 else "moderate dispersion")
    lines.append(f"- **{r.variable}**: mean {r.mean} vs median {r.median} → {shape}; "
                 f"IQR {r.iqr} (Q1 {r.q1}–Q3 {r.q3}); std {r.std} (CV {r.cv}) → {disp}; "
                 f"90% of values fall between {r.p05} and {r.p95}.")
lines += ["", "_Descriptive statistics only — no causal claims are made anywhere in this project._"]
(  # also save as markdown next to the CSV
    __import__("project_utils").TABLES / "statistical_summary.md"
).write_text("\n".join(lines))
print(stats[["variable", "mean", "median", "std", "iqr", "skew"]].to_string(index=False))
