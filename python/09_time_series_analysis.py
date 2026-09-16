"""Daily / weekly / monthly / quarterly series with growth and rolling stats."""
import pandas as pd
from project_utils import CLEANED, save_table, save_json

df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
pur = df[df.purchased == 1]

daily = (pur.groupby(pur.visit_date.dt.date)
            .agg(orders=("session_id", "count"), revenue=("revenue", "sum")))
sessions = df.groupby(df.visit_date.dt.date).size().rename("sessions")
daily = daily.join(sessions).rename_axis("date").reset_index()
daily["date"] = pd.to_datetime(daily["date"])
full = pd.DataFrame({"date": pd.date_range(daily.date.min(), daily.date.max())})
daily = full.merge(daily, on="date", how="left").fillna(0)   # zero-fill calendar
daily["conversion_rate"] = (daily.orders / daily.sessions).round(4)
daily["revenue_7d_rolling"] = daily.revenue.rolling(7, min_periods=1).mean().round(2)
save_table(daily.assign(date=daily["date"]).round({c: 2 for c in daily.columns if c != "date"}), "daily_series.csv")

monthly = (pur.assign(ym=pur.visit_date.dt.strftime("%Y-%m"))
              .groupby("ym").agg(orders=("session_id", "count"), revenue=("revenue", "sum")))
monthly["sessions"] = df.assign(ym=df.visit_date.dt.strftime("%Y-%m")).groupby("ym").size()
monthly["conversion_rate"] = (monthly.orders / monthly.sessions).round(4)
monthly["aov"] = (monthly.revenue / monthly.orders).round(2)
monthly["revenue_mom_growth_pct"] = (100 * monthly.revenue.pct_change()).round(2)
save_table(monthly.round(2).reset_index(), "monthly_series.csv")

quarterly = (pur.assign(q=pur.visit_date.dt.to_period("Q").astype(str))
                .groupby("q").agg(orders=("session_id", "count"), revenue=("revenue", "sum")))
save_table(quarterly.reset_index(), "quarterly_series.csv")

best = monthly.revenue.idxmax(); worst = monthly.revenue.idxmin()
save_json({"best_month": best, "best_month_revenue": round(float(monthly.loc[best, "revenue"]), 2),
           "worst_month": worst, "worst_month_revenue": round(float(monthly.loc[worst, "revenue"]), 2),
           "best_month_growth_pct": float(monthly.loc[best, "revenue_mom_growth_pct"]),
           "peak_quarter": quarterly.revenue.idxmax(),
           "peak_quarter_revenue": round(float(quarterly.revenue.max()), 2)},
          "time_series_kpis.json")
print(monthly.to_string())
