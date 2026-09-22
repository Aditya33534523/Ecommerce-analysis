# 📊 E-Commerce Funnel Analytics & Revenue Optimization

An end-to-end e-commerce analytics portfolio project spanning **data auditing, cleaning, feature engineering, statistical modeling, cohort & RFM segmentation, SQL querying, automated reporting, and interactive Excel dashboarding**.

---

## 🎯 Executive Summary & The "Why"

Operational e-commerce systems generate vast volumes of raw interaction logs. However, **raw operational data inherently suffers from incompleteness and false signals**:
- Categorical attributes are logged as cryptic integer codes without semantic labels.
- Satisfaction scores frequently carry synthetic defaults (e.g., non-purchasing visitors defaulting to a 4-star review).
- Marketing spend and promotional discounting are often distributed without verifying whether price cuts drive incremental conversion or simply cannibalize revenue.

**This project exists to resolve that incompleteness:** taking 25,000 raw, unverified session logs and transforming them into an audited, mathematically verified commercial analytics engine that drives revenue strategy.

---

## 📈 Key Business Outcomes & Findings

| Business Metric | Value | Strategic Takeaway |
| :--- | :--- | :--- |
| **Total Sessions Analyzed** | **25,000** | Full-year session-grain activity (2024-01-01 to 2024-12-30). |
| **Gross / Net Revenue** | **$11.11M / $10.12M** | **$991.6K** in promotional discounts granted (8.93% of gross revenue). |
| **Conversion Rate (CR)** | **22.46%** | 5,616 purchased sessions out of 25,000 total visits. |
| **Cart Abandonment Rate** | **65.15%** | Primary funnel leak is between cart addition and final checkout. |
| **Average Order Value (AOV)** | **$1,801.31** | Average items per order: 2.50. |
| **Discount Elasticity** | **+0.31% CR lift** for **-18.5% AOV** | 11–20% discount band conversion (22.74%) vs. 0% discount (22.43%) showed near-zero lift (p-value 0.644) while degrading AOV from $1,992 to $1,624. |
| **Pareto Concentration** | **Top 20% = 35.75% Rev** | Top 20% of products generate ~36% of net revenue; top 20% categories generate 39.23%. |
| **Customer Retention** | **27.75% Repeat Rate** | 1,159 repeat purchasers out of 4,176 buyers; top-10 customers account for 1.25% of revenue. |
| **Top Acquisition Channel** | **Channel 5 ($1.82M)** | Channel 5 produced highest net revenue and top conversion rate (23.6%). |

---

## 🔬 Project Architecture & Pipeline

```mermaid
flowchart LR
    A["Raw Data (Ecommerce.csv)"] --> B["01: 37-Check Validation Suite"]
    B --> C["02 & 03: Data Cleaning & Feature Eng"]
    C --> D["04-09: Deep-Dive Analytics & RFM"]
    D --> E["10 & 11: Figures & Executive Markdown"]
    C --> F["SQL: Window Functions & CTEs"]
    C --> G["Excel: Dynamic Workbook Generator"]
```

### Script Execution Flow
1. **`python/01_data_validation.py`**: Executes a 37-point programmatic audit checking primary key uniqueness, funnel consistency (`purchased ⇒ added_to_cart`), formula integrity, date sequencing, and non-purchaser review defaults.
2. **`python/02_data_cleaning.py`**: Cleans and types data, creates consistent date representations, and exports validated baseline records.
3. **`python/03_feature_engineering.py`**: Derives behavioral stage indicators, gross revenue, discount flags, seasonality tags, and standardized labels.
4. **`python/04_exploratory_analysis.py`**, **`05_statistical_analysis.py`** & **`05b_hypothesis_tests.py`**: Computes parametric & non-parametric metrics (skewness, kurtosis, IQR) on commercial variables and performs hypothesis testing (Chi-square, A/B testing).
5. **`python/06_sales_analysis.py`** & **`07_product_analysis.py`**: Calculates monthly run-rates, channel conversion, and product/category Pareto cumulative distributions.
6. **`python/08_customer_analysis.py`**: Builds an **RFM (Recency, Frequency, Monetary)** quintile scoring model segmenting 4,176 buyers into 5 lifecycle clusters: *Champions, At-Risk Loyalists, Core, Hibernating, and New/Low-Frequency*.
7. **`python/09_time_series_analysis.py`**: Evaluates 7-day rolling revenue averages and quarter-over-quarter momentum (peak Q3: $2.62M).
8. **`python/10_visualization.py`** & **`11_report_automation.py`**: Generates 14 publication-grade figures and automated Markdown executive summaries.
9. **`excel/build_excel_woorkbook.py`**: Programmatically generates a formatted multi-sheet Excel workbook with live formulas (`SUMIFS`, `COUNTIFS`, `XLOOKUP`), conditional formatting, and native charts.
10. **`verify.py`**: Independent reconciliation script comparing pandas results against SQLite for headline metrics, top products, segment rules, and grouping integrity.

---

## 🔍 The "Weak Spots" & Roadmap (Where We Work More)

A vital dimension of this project is acknowledging its analytical boundaries and defining the engineering roadmap to resolve remaining incompleteness:

1. **Unlabeled Categorical Dimensions:**
   - *Limitation:* Channels, categories, devices, and payment methods are encoded as integers without an enterprise codebook.
   - *Solution / Next Step:* Integrate with enterprise Master Data Management (MDM) / product taxonomy APIs rather than assuming arbitrary business labels.
2. **Product Taxonomy Inconsistencies:**
   - *Limitation:* Validation flagged 899 products mapped to multiple categories across different sessions.
   - *Solution / Next Step:* Implement primary category vs. auxiliary tag schemas upstream in the relational catalog.
3. **Session Granularity vs. Multi-Item Baskets:**
   - *Limitation:* Data is logged at the session grain (one product per visit, quantity 1–4). It does not capture multi-item shopping baskets.
   - *Solution / Next Step:* Ingest true multi-line transaction logs to perform **Market Basket Analysis (Apriori / Association Rule Mining)** for cross-sell recommendations.
4. **Observational Association vs. Causal Pricing:**
   - *Limitation:* The flat conversion across discount tiers is correlational and prone to customer self-selection bias.
   - *Solution / Next Step:* Run controlled **A/B Experiments** across promotional campaigns to establish true causal price elasticity curves.
5. **Modern Data Stack Migration:**
   - *Limitation:* Pipeline executes via local batch scripts.
   - *Solution / Next Step:* Transition transformations into **dbt**, orchestrate via **Airflow / Prefect**, and store in **Snowflake / BigQuery** for live BI consumption in Power BI / Tableau.



## 🛠️ Technology Stack
- **Languages & Libraries:** Python (Pandas, NumPy, Matplotlib, OpenPyXL), SQL (SQLite, CTEs, Window Functions)
- **Techniques:** Data Quality Auditing, RFM Quintile Segmentation, Pareto Distribution (80/20 Rule), Funnel Diagnostics, Discount Elasticity Modeling, Rolling Time-Series
- **Outputs:** Interactive Excel Workbook, Automated Executive Markdown, 14 Publication Visualizations, Comprehensive Data Quality Documentation
