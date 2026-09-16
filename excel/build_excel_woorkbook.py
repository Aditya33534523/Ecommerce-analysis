"""Builds excel/Ecommerce_Analytics.xlsx from the cleaned data:
Raw_Data, Cleaned_Data (with live formulas), KPIs (SUMIFS/COUNTIFS/...),
Aggregates, Dashboard (native charts), Data_Quality, Lookup_Demo, Pivot_Guide."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
from project_utils import CLEANED, RAW, load_json, TABLES

OUT = Path(__file__).resolve().parent / "Ecommerce_Analytics.xlsx"
df = pd.read_csv(CLEANED, parse_dates=["visit_date"])
df["visit_date"] = df.visit_date.dt.date

COLS = ["source_row_number","customer_id","session_id","visit_date","device_label","user_type_label",
        "channel_label","product_id","category_label","unit_price","quantity","discount_percent",
        "discount_amount","revenue","pages_viewed","time_on_site_sec","added_to_cart","purchased",
        "cart_abandoned","rating","review_helpful_votes","payment_label","location","season_name","year_month"]
d = df[COLS].copy()
N = len(d)
LAST = N + 1                      # last data row on the sheet (header = row 1)
wb = Workbook()

def style_header(ws, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(1, c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"

# ---------------- Raw_Data ----------------
raw = pd.read_csv(RAW)
ws = wb.active; ws.title = "Raw_Data"
for r in dataframe_to_rows(raw, index=False, header=True): ws.append(r)
style_header(ws, raw.shape[1])

# ---------------- Cleaned_Data + row-level formulas ----------------
ws = wb.create_sheet("Cleaned_Data")
for r in dataframe_to_rows(d, index=False, header=True): ws.append(r)
style_header(ws, len(COLS))
# Z..AE appended formula columns (letters fixed by COLS order):
ws.cell(1, 26, "Gross_Revenue");  ws.cell(1, 27, "Net_Check")
ws.cell(1, 28, "Diff");           ws.cell(1, 29, "Stage")
ws.cell(1, 30, "Month_Name");     ws.cell(1, 31, "Weekend_Flag")
for r in range(2, LAST + 1):
    ws.cell(r, 26, f"=ROUND(J{r}*K{r},2)")                          # unit_price*qty
    ws.cell(r, 27, f"=ROUND(Z{r}*(1-L{r}/100),2)")                  # *(1-discount%)
    ws.cell(r, 28, f"=ROUND(AA{r}-N{r},2)")                         # audit vs file revenue
    ws.cell(r, 29, f'=IF(R{r}=1,"Purchased",IF(Q{r}=1,"Cart Abandoned","Browse Only"))')
    ws.cell(r, 30, f'=TEXT(D{r},"mmm")')
    ws.cell(r, 31, f'=IF(WEEKDAY(D{r},2)>=6,1,0)')
    for c, fmt in [(10, "#,##0.00"), (13, "#,##0.00"), (14, "#,##0.00"),
                   (26, "#,##0.00"), (27, "#,##0.00"), (28, "0.00")]:
        ws.cell(r, c).number_format = fmt
ws.auto_filter.ref = f"A1:AE{LAST}"
ws.conditional_formatting.add(f"N2:N{LAST}",
    ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="63BE7B"))
for col, w in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "AA", [10,11,10,11,11,12,11,10,11,11,9,11,13,11,9,10,9,10,10,8,10,11,9,16,10,13,11,8,14,11,10]):
    ws.column_dimensions[col].width = w

CD = "Cleaned_Data!"
# ---------------- KPIs (all live formulas) ----------------
ws = wb.create_sheet("KPIs")
ws["A1"] = "KPI"; ws["B1"] = "Value"; ws["A1"].font = ws["B1"].font = Font(bold=True, size=12)
kpis = [
 ("Total sessions",            f"=COUNT({CD}C2:C{LAST})", "0"),
 ("Orders (purchased)",        f"=COUNTIF({CD}R2:R{LAST},1)", "0"),
 ("Conversion rate",           "=IFERROR(B3/B2,0)", "0.00%"),
 ("Units sold",                f"=SUMIF({CD}R2:R{LAST},1,{CD}K2:K{LAST})", "0"),
 ("Gross revenue",             f"=SUMIF({CD}R2:R{LAST},1,{CD}Z2:Z{LAST})", "#,##0.00"),
 ("Discounts given",           f"=SUMIF({CD}R2:R{LAST},1,{CD}M2:M{LAST})", "#,##0.00"),
 ("Net revenue",               f"=SUMIF({CD}R2:R{LAST},1,{CD}N2:N{LAST})", "#,##0.00"),
 ("Average order value (AOV)", "=IFERROR(B8/B3,0)", "#,##0.00"),
 ("Median order value",        f'=MEDIAN(IF({CD}R2:R{LAST}=1,{CD}N2:N{LAST}))', "#,##0.00"),
 ("Avg unit price (sold)",     f"=AVERAGEIF({CD}R2:R{LAST},1,{CD}J2:J{LAST})", "#,##0.00"),
 ("Cart adds",                 f"=COUNTIF({CD}Q2:Q{LAST},1)", "0"),
 ("Cart abandonment rate",     f"=IFERROR(COUNTIFS({CD}Q2:Q{LAST},1,{CD}R2:R{LAST},0)/B12,0)", "0.00%"),
 ("Revenue per session",       "=IFERROR(B8/B2,0)", "#,##0.00"),
 ("Max order value",           f"=MAXIFS({CD}N2:N{LAST},{CD}R2:R{LAST},1)", "#,##0.00"),
 ("Weekend sessions",          f"=SUM({CD}AE2:AE{LAST})", "0"),
]
for i, (label, formula, fmt) in enumerate(kpis, start=2):
    ws.cell(i, 1, label); ws.cell(i, 2, formula).number_format = fmt
ws["A17"] = "Median formula: array formula — confirm with Ctrl+Shift+Enter in older Excel."
ws.column_dimensions["A"].width = 26; ws.column_dimensions["B"].width = 16

# ---------------- Aggregates (feeds charts; SUMIFS/COUNTIFS by label) ----------------
ws = wb.create_sheet("Aggregates")
def block(start_col, title, keys, key_col_letter, extra=""):
    c0 = start_col
    ws.cell(1, c0, title).font = Font(bold=True)
    headers = ["Group", "Sessions", "Orders", "Net revenue", "Conversion"]
    for j, h in enumerate(headers): ws.cell(2, c0 + j, h).font = Font(bold=True)
    for i, klabel in enumerate(keys):
        r = 3 + i
        ws.cell(r, c0, klabel)
        ws.cell(r, c0+1, f'=COUNTIF({CD}{key_col_letter}2:{key_col_letter}{LAST},A{r})' if c0 == 1
                else f'=COUNTIF({CD}{key_col_letter}2:{key_col_letter}{LAST},{get_column_letter(c0)}{r})')
        ws.cell(r, c0+2, f'=COUNTIFS({CD}{key_col_letter}2:{key_col_letter}{LAST},{get_column_letter(c0)}{r},{CD}R2:R{LAST},1)')
        ws.cell(r, c0+3, f'=SUMIFS({CD}N2:N{LAST},{CD}{key_col_letter}2:{key_col_letter}{LAST},{get_column_letter(c0)}{r},{CD}R2:R{LAST},1)')
        ws.cell(r, c0+3).number_format = "#,##0.00"
        ws.cell(r, c0+4, f'=IFERROR({get_column_letter(c0+2)}{r}/{get_column_letter(c0+1)}{r},0)').number_format = "0.0%"
    return 3 + len(keys)

cats = sorted(d.category_label.unique()); chans = sorted(d.channel_label.unique())
months = sorted(d.year_month.unique())
end_cat  = block(1,  "By category", cats, "I")
end_mon  = block(7,  "By month",    months, "Y")
end_chan = block(13, "By channel",  chans, "G")
ws.conditional_formatting.add(f"D3:D{end_cat-1}",
    DataBarRule(start_type="num", start_value=0, end_type="max", color="63BE7B"))

# ---------------- Dashboard (native Excel charts on real aggregates) ----------------
ws = wb.create_sheet("Dashboard")
ws["A1"] = "E-Commerce Analytics Dashboard"; ws["A1"].font = Font(bold=True, size=16)
ws["A2"] = f"Data: {N:,} sessions · all values live from Cleaned_Data/Aggregates"

bar = BarChart(); bar.title = "Net revenue by category"; bar.height, bar.width = 8, 16
bar.add_data(Reference(wb["Aggregates"], min_col=4, min_row=2, max_row=end_cat-1), titles_from_data=True)
bar.set_categories(Reference(wb["Aggregates"], min_col=1, min_row=3, max_row=end_cat-1))
ws.add_chart(bar, "A4")

line = LineChart(); line.title = "Monthly net revenue"; line.height, line.width = 8, 16
line.add_data(Reference(wb["Aggregates"], min_col=4, min_row=2, max_row=end_mon-1), titles_from_data=True)
line.set_categories(Reference(wb["Aggregates"], min_col=7, min_row=3, max_row=end_mon-1))
ws.add_chart(line, "K4")

pie = PieChart(); pie.title = "Sessions share by channel"; pie.height, pie.width = 8, 12
pie.add_data(Reference(wb["Aggregates"], min_col=14, min_row=2, max_row=end_chan-1), titles_from_data=True)
pie.set_categories(Reference(wb["Aggregates"], min_col=13, min_row=3, max_row=end_chan-1))
ws.add_chart(pie, "A22")

top = pd.read_csv(TABLES / "top_products.csv").head(10)
ws["K22"] = "Top 10 products by net revenue (computed in Python from the same data)"
for j, h in enumerate(["Product", "Category", "Orders", "Net revenue"]):
    ws.cell(23, 11 + j, h).font = Font(bold=True)
for i, row in enumerate(top.itertuples(), start=24):
    ws.cell(i, 11, f"P{row.product_id}"); ws.cell(i, 12, row.category)
    ws.cell(i, 13, row.orders); ws.cell(i, 14, row.net_revenue).number_format = "#,##0.00"

# ---------------- Data_Quality ----------------
ws = wb.create_sheet("Data_Quality")
v = load_json("validation.json")
ws.append(["Check", "Status", "Detail"])
for c in range(1, 4): ws.cell(1, c).font = Font(bold=True)
for res in v["results"]: ws.append([res["check"], res["status"], res["detail"][:120]])
ws.column_dimensions["A"].width = 34; ws.column_dimensions["C"].width = 90

# ---------------- Lookup_Demo (XLOOKUP + INDEX/MATCH on real columns) ----------------
ws = wb.create_sheet("Lookup_Demo")
ws["A1"] = "Enter a product_id:"; ws["B1"] = int(d.product_id.iloc[0])
ws["A2"] = "Category (XLOOKUP)";  ws["B2"] = f"=XLOOKUP(B1,{CD}H2:H{LAST},{CD}I2:I{LAST},\"not found\")"
ws["A3"] = "Category (INDEX/MATCH)"; ws["B3"] = f"=INDEX({CD}I2:I{LAST},MATCH(B1,{CD}H2:H{LAST},0))"
ws["A4"] = "Avg unit price for that product"; ws["B4"] = f'=IFERROR(AVERAGEIF({CD}H2:H{LAST},B1,{CD}J2:J{LAST}),0)'
ws["B4"].number_format = "#,##0.00"
ws.column_dimensions["A"].width = 30

# ---------------- Pivot_Guide ----------------
ws = wb.create_sheet("Pivot_Guide")
steps = ["PIVOT TABLES — 2-minute setup (openpyxl cannot embed pivot caches, Excel builds them instantly):",
 "1. Click any cell in Cleaned_Data → Insert → PivotTable → New sheet.",
 "2. Pivot 1 — Revenue by category & month: Rows=category_label, Columns=year_month, Values=Sum of revenue.",
 "3. Pivot 2 — Conversion by channel: Rows=channel_label, Values=Average of purchased (format as %).",
 "4. Pivot 3 — AOV by discount depth: Rows=discount_band is not in this sheet? Use discount_percent; Values=Average of revenue, filter purchased=1.",
 "5. Add Slicers: device_label, channel_label, season_name → connect to all pivots (Report Connections).",
 "6. Insert → Timeline on visit_date for month/quarter scrubbing.",
 "",
 "POWER QUERY — load/refresh raw data without code:",
 "Data → Get Data → From File → From Text/CSV → data/raw/Ecommerce.csv.",
 "In the editor: use 'Change Type' → 'Using Locale…' → Date, locale en-English (United Kingdom) so DD-MM-YYYY parses correctly.",
 "Remove duplicates on session_id, set types, Close & Load to a table.",
 "",
 "REFRESH: replace data/raw/Ecommerce.csv → Data → Refresh All, or re-run this builder.",
 "",
 "NOTE: integer-coded columns (device/channel/category/payment/user_type/location) have no codebook in",
 "the source file and are labelled generically on purpose — rename labels only if the provider documents them."]
for i, s in enumerate(steps, 1): ws.cell(i, 1, s)
ws.column_dimensions["A"].width = 110

wb.save(OUT)
print(f"workbook → {OUT}  ({N:,} cleaned rows, live formulas on {N:,} rows)")
