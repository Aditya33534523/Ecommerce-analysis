"""Every chart answers a business question. Matplotlib only → reports/figures/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
from project_utils import CLEANED, TABLES, FIGS, save_table

plt.rcParams.update({"figure.autolayout": True, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": .3, "figure.dpi": 120})
def save(fig, name):
    fig.savefig(FIGS / f"{name}.png", bbox_inches="tight"); plt.close(fig)
    print("figure →", name)

df  = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1]

# 1 Monthly revenue & orders — Q: how does revenue evolve?
m = pd.read_csv(TABLES / "monthly_series.csv")
fig, ax = plt.subplots(figsize=(9, 4)); ax2 = ax.twinx(); ax2.grid(False)
ax.bar(m.ym, m.revenue, color="#4C72B0", label="net revenue")
ax2.plot(m.ym, m.orders, color="#DD8452", marker="o", lw=2, label="orders")
ax.set_ylabel("Net revenue"); ax2.set_ylabel("Orders")
ax.set_title("Monthly net revenue & orders (purchased sessions)")
ax.tick_params(axis="x", rotation=45)
fig.legend(loc="upper left", bbox_to_anchor=(.08, .95)); save(fig, "01_monthly_revenue_orders")

# 2 Daily revenue + 7-day rolling — Q: trend vs noise?
d = pd.read_csv(TABLES / "daily_series.csv", parse_dates=["date"])
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(d.date, d.revenue, alpha=.35, label="daily")
ax.plot(d.date, d.revenue_7d_rolling, color="crimson", lw=2, label="7-day rolling")
ax.set_title("Daily net revenue with 7-day rolling average"); ax.set_ylabel("Revenue")
ax.legend(); save(fig, "02_daily_revenue_rolling7")

# 3 Revenue by category — Q: which categories drive revenue?
c = pd.read_csv(TABLES / "product_category_summary.csv")
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(c.category_label, c.net_revenue, color="#55A868")
ax.invert_yaxis(); ax.set_xlabel("Net revenue")
ax.set_title("Net revenue by product category"); save(fig, "03_revenue_by_category")

# 4 Top 15 products — Q: which products earn most?
t = pd.read_csv(TABLES / "top_products.csv")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh("P" + t.product_id.astype(str), t.net_revenue, color="#4C72B0")
ax.invert_yaxis(); ax.set_xlabel("Net revenue")
ax.set_title("Top 15 products by net revenue"); save(fig, "04_top_products")

# 5 Funnel — Q: where is revenue lost?
f = pd.read_csv(TABLES / "funnel.csv")
fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(f.funnel_stage, f.sessions, color=["#999", "#DD8452", "#55A868"])
ax.bar_label(bars, labels=[f"{s:,}\n({p}%)" for s, p in zip(f.sessions, f.share_pct)])
ax.set_title("Session funnel: Browse → Cart → Purchase"); ax.set_ylabel("Sessions")
save(fig, "05_funnel")

# 6 Conversion by channel — Q: which channels convert?
ch = pd.read_csv(TABLES / "sales_by_channel.csv").sort_values("conversion_rate")
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(ch.channel_label, 100 * ch.conversion_rate, color="#8172B3")
for i, v in enumerate(100 * ch.conversion_rate):
    ax.text(v, i, f" {v:.1f}%", va="center")
ax.set_xlabel("Conversion rate (%)"); ax.set_xlim(0, 100 * ch.conversion_rate.max() * 1.2)
ax.set_title("Purchase conversion by marketing channel"); save(fig, "06_conversion_by_channel")

# 7 Conversion by device — Q: device gaps?
dv = pd.read_csv(TABLES / "sales_by_device.csv").sort_values("conversion_rate")
fig, ax = plt.subplots(figsize=(6, 3.5))
ax.bar(dv.device_label, 100 * dv.conversion_rate, color="#C44E52")
ax.set_ylabel("Conversion (%)"); ax.set_title("Conversion by device type")
save(fig, "07_conversion_by_device")

# 8 Discount band vs conversion & AOV — Q: do discounts associate with sales?
db = pd.read_csv(TABLES / "sales_by_discount_band.csv")
fig, ax = plt.subplots(figsize=(8, 4)); ax2 = ax.twinx(); ax2.grid(False)
ax.bar(db.discount_band.astype(str), 100 * db.conversion_rate, color="#64B5CD", label="conversion %")
ax2.plot(db.discount_band.astype(str), db.avg_order_value, color="black", marker="s", label="AOV")
ax.set_ylabel("Conversion (%)"); ax2.set_ylabel("Avg order value")
ax.set_title("Discount depth vs conversion & AOV (association, not causation)")
fig.legend(loc="upper right", bbox_to_anchor=(.9, .95)); save(fig, "08_discount_vs_conversion")

# 9 Price vs quantity (purchased) — Q: do expensive items sell in smaller baskets?
fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(pur.unit_price, pur.quantity, alpha=.25, s=14)
ax.set_xlabel("Unit price"); ax.set_ylabel("Quantity")
ax.set_yticks([1, 2, 3, 4])
ax.set_title("Unit price vs basket quantity (purchased sessions)")
save(fig, "09_price_vs_quantity")

# 10 Correlation heatmaps (behaviour / purchase economics)
beh = df[["purchased", "added_to_cart", "pages_viewed", "time_on_site_sec",
          "unit_price", "quantity", "discount_percent"]].corr()
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(beh, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(beh)), beh.columns, rotation=45, ha="right")
ax.set_yticks(range(len(beh)), beh.columns)
for i in range(len(beh)):
    for j in range(len(beh)):
        ax.text(j, i, f"{beh.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
fig.colorbar(im, shrink=.8); ax.set_title("Correlation — all sessions (behaviour)")
ax.grid(False); save(fig, "10_corr_behaviour")

eco = pur[["unit_price", "quantity", "discount_percent", "discount_amount",
           "revenue", "pages_viewed", "time_on_site_sec"]].corr()
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(eco, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(eco)), eco.columns, rotation=45, ha="right")
ax.set_yticks(range(len(eco)), eco.columns)
for i in range(len(eco)):
    for j in range(len(eco)):
        ax.text(j, i, f"{eco.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
fig.colorbar(im, shrink=.8); ax.set_title("Correlation — purchased sessions only (economics)")
ax.grid(False); save(fig, "11_corr_purchases")
save_table(beh.round(3).reset_index(), "corr_behaviour.csv")
save_table(eco.round(3).reset_index(), "corr_purchases.csv")

# 11 Pareto — Q: how concentrated is revenue?
pr = pd.read_csv(TABLES / "pareto_products.csv")
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(range(1, len(pr) + 1), pr.cum_share_pct, color="#4C72B0")
ax.axhline(80, ls="--", color="grey"); ax.set_xlabel("Products (ranked)")
ax.set_ylabel("Cumulative % of net revenue")
n80 = int((pr.cum_share_pct < 80).sum()) + 1
ax.axvline(n80, ls=":", color="crimson",
           label=f"{n80} products ≈ 80% of revenue ({100*n80/len(pr):.0f}% of catalog)")
ax.set_title("Revenue concentration (Pareto)"); ax.legend()
save(fig, "12_pareto_products")

# 12 Engagement vs conversion — Q: do engaged visitors convert more?
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, col, lab in zip(axes, ["pages_viewed", "time_on_site_sec"],
                        ["Pages viewed", "Time on site (sec)"]):
    data = [df.loc[df.purchased == 0, col], df.loc[df.purchased == 1, col]]
    ax.boxplot(data, tick_labels=["No purchase", "Purchased"], showfliers=False)
    ax.set_ylabel(lab)
fig.suptitle("Engagement by conversion outcome (association)"); save(fig, "13_engagement_vs_conversion")

# 13 Weekday pattern — Q: which days perform?
w = pd.read_csv(TABLES / "sales_by_weekday.csv")
order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
w["o"] = w.weekday_name.map({d: i for i, d in enumerate(order)}); w = w.sort_values("o")
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(w.weekday_name, w.net_revenue, color="#4C72B0")
ax.set_ylabel("Net revenue"); ax.set_title("Net revenue by weekday")
save(fig, "14_weekday_revenue")

print("all figures written to", FIGS)
