# Power BI Dashboard — Setup Guide

## Prerequisites
- Power BI Desktop (free): https://powerbi.microsoft.com/desktop/
- PostgreSQL running (via Docker or local install)
- Pipeline has been run (`python run_pipeline.py` or via Airflow)

---

## Option A — Connect directly to PostgreSQL

1. Open Power BI Desktop
2. Click **Get Data** → **More** → search **PostgreSQL**
3. Enter connection details:
   - **Server**: `localhost:5432`
   - **Database**: `sales_db`
4. Click **OK** → enter credentials:
   - **Username**: `postgres`
   - **Password**: `postgres`
5. In the Navigator, select these tables:
   - `fact_sales`
   - `dim_customer`
   - `dim_product`
   - `dim_seller`
   - `dim_date`
6. Click **Load**

---

## Option B — Import from CSV (no PostgreSQL needed)

1. Open Power BI Desktop
2. Click **Get Data** → **Text/CSV**
3. Import these files from `data/transformed/`:
   - `fact_sales.csv`
   - `dim_customer.csv`
   - `dim_product.csv`
   - `dim_seller.csv`
   - `dim_date.csv`

---

## Set Up Relationships (Model View)

Go to **Model view** (left sidebar) and create these relationships:

| From Table | From Column | To Table | To Column | Cardinality |
|---|---|---|---|---|
| fact_sales | customer_id | dim_customer | customer_id | Many → One |
| fact_sales | product_id | dim_product | product_id | Many → One |
| fact_sales | seller_id | dim_seller | seller_id | Many → One |
| fact_sales | date_id | dim_date | date_id | Many → One |

---

## KPI Cards

Add Card visuals for:

| KPI | DAX Measure |
|---|---|
| Total Revenue | `Total Revenue = SUM(fact_sales[revenue])` |
| Total Orders | `Total Orders = DISTINCTCOUNT(fact_sales[order_id])` |
| Avg Order Value | `AOV = DIVIDE([Total Revenue], [Total Orders])` |
| Customer Count | `Customers = DISTINCTCOUNT(fact_sales[customer_id])` |
| Total Profit | `Total Profit = SUM(fact_sales[profit])` |
| Late Delivery % | `Late % = DIVIDE(SUM(fact_sales[late_delivery]), [Total Orders]) * 100` |

---

## Visuals to Build

### 1. Revenue by Month (Line Chart)
- X-axis: `dim_date[year]` + `dim_date[month]`
- Y-axis: `[Total Revenue]`
- Legend: none

### 2. Revenue by State (Filled Map)
- Location: `dim_customer[customer_state]`
- Color saturation: `[Total Revenue]`

### 3. Top 10 Products (Bar Chart)
- Y-axis: `dim_product[product_category_name]`
- X-axis: `[Total Revenue]`
- Filter: Top N = 10

### 4. Top Categories (Treemap)
- Group: `dim_product[product_category_name]`
- Values: `[Total Revenue]`

### 5. Top 10 Customers (Table)
- Columns: `dim_customer[customer_unique_id]`, `dim_customer[customer_state]`, `[Total Revenue]`, `[Total Orders]`
- Sort by Total Revenue descending

### 6. Sales Trend (Area Chart)
- X-axis: `dim_date[full_date]`
- Y-axis: `[Total Revenue]`

### 7. Order Status Breakdown (Donut Chart)
- Legend: `fact_sales[order_status]`
- Values: `COUNT(fact_sales[order_id])`

### 8. Average Review Score by Category (Column Chart)
- X-axis: `dim_product[product_category_name]`
- Y-axis: `AVERAGE(fact_sales[review_score])`

### 9. Late Delivery Rate by State (Bar Chart)
- Y-axis: `dim_customer[customer_state]`
- X-axis: `[Late %]`

### 10. Payment Type Distribution (Pie Chart)
- Legend: `fact_sales[payment_type]`
- Values: `COUNT(fact_sales[order_id])`

---

## Slicers (Filters)

Add slicers for:
- `dim_date[year]`
- `dim_date[quarter]`
- `dim_customer[customer_state]`
- `dim_product[product_category_name]`
- `fact_sales[order_status]`

---

## Publish to Power BI Service (optional)

1. Click **File** → **Publish** → **Publish to Power BI**
2. Sign in with your Microsoft account
3. Select your workspace
4. After publishing, set up **Scheduled Refresh** to pull fresh data daily

---

## DAX Measures Reference

```dax
Total Revenue = SUM(fact_sales[revenue])

Total Orders = DISTINCTCOUNT(fact_sales[order_id])

AOV = DIVIDE([Total Revenue], [Total Orders], 0)

Total Profit = SUM(fact_sales[profit])

Customer Count = DISTINCTCOUNT(fact_sales[customer_id])

Late % = 
DIVIDE(
    CALCULATE(SUM(fact_sales[late_delivery])),
    [Total Orders],
    0
) * 100

Avg Review Score = AVERAGE(fact_sales[review_score])

MoM Growth % = 
VAR CurrentMonth = [Total Revenue]
VAR PrevMonth = CALCULATE(
    [Total Revenue],
    DATEADD(dim_date[full_date], -1, MONTH)
)
RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth, 0) * 100
```
