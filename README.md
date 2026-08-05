# Cloud-Native ETL Pipeline for E-Commerce Sales Analytics

An end-to-end Data Engineering project that extracts, validates, cleans, transforms, and loads 100K+ Brazilian e-commerce records into a PostgreSQL star-schema data warehouse — orchestrated by Apache Airflow, backed up to AWS S3, and visualised in Power BI.

---

## Architecture

```
Raw CSVs (Kaggle Olist)
        │
        ▼
   [ Extract ]  ──→  extract_orders.py / extract_customers.py / extract_products.py
        │
        ▼
  [ Validate ]  ──→  validate_orders.py / validate_customers.py  ──→  validation_report.csv
        │
        ▼
   [ Clean ]    ──→  clean_orders.py  ──→  data/cleaned/*.csv
        │
        ▼
 [ Transform ]  ──→  feature_engineering.py + star_schema.py  ──→  data/transformed/*.csv
        │
        ▼
   [ Load ]     ──→  postgres_loader.py  ──→  PostgreSQL (sales_db)
        │
        ▼
  [ Backup ]    ──→  s3_backup.py  ──→  AWS S3
        │
        ▼
[ Power BI Dashboard ]  ←── DirectQuery / CSV export
```

**Orchestration:** Apache Airflow DAG (`sales_pipeline`) runs daily at 08:00 UTC.  
**Containerisation:** Docker Compose spins up PostgreSQL + Airflow (webserver + scheduler) + Python ETL app.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Data Processing | Pandas, NumPy |
| Database | PostgreSQL 16 |
| ORM / Loader | SQLAlchemy, Psycopg2 |
| Orchestration | Apache Airflow 2.9 |
| Cloud Storage | AWS S3 (Boto3) |
| Containerisation | Docker, Docker Compose |
| Visualisation | Power BI |
| Testing | Pytest |
| Version Control | Git / GitHub |

---

## Folder Structure

```
sales-etl-pipeline/
├── data/
│   ├── raw/              ← Place Kaggle CSVs here
│   ├── cleaned/          ← Output of clean step
│   └── transformed/      ← Star-schema CSVs
├── extract/
│   ├── extract_orders.py
│   ├── extract_customers.py
│   └── extract_products.py
├── validation/
│   ├── validate_orders.py
│   └── validate_customers.py
├── transform/
│   ├── clean_orders.py
│   ├── feature_engineering.py
│   └── star_schema.py
├── load/
│   ├── postgres_loader.py
│   └── s3_backup.py
├── airflow/
│   └── dags/
│       └── sales_pipeline.py
├── sql/
│   ├── schema.sql        ← DDL for all tables + indexes
│   └── analytics.sql     ← 15 analytics queries + views
├── tests/
│   ├── test_extract.py
│   ├── test_validation.py
│   ├── test_transform.py
│   └── test_load.py
├── docker/
│   ├── Dockerfile
│   └── init-multiple-dbs.sh
├── docker-compose.yml
├── run_pipeline.py       ← Run pipeline locally without Airflow
├── requirements.txt
└── .gitignore
```

---

## Installation

### Prerequisites

- Python 3.12+
- Docker Desktop
- Git

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/sales-etl-pipeline.git
cd sales-etl-pipeline
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the dataset

Download the [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle and place all CSV files inside `data/raw/`:

```
data/raw/
├── olist_customers_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_order_items_dataset.csv
└── olist_sellers_dataset.csv
```

### 5. Configure environment variables

Create a `.env` file in the project root (never commit this):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sales_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET=sales-etl-pipeline
```

---

## How to Run

### Option A — Run locally (no Docker)

```bash
# Run full pipeline (skips DB and S3 if not configured)
python run_pipeline.py

# Skip S3 backup
python run_pipeline.py --skip-s3

# Skip PostgreSQL load
python run_pipeline.py --skip-db
```

### Option B — Docker Compose (recommended)

```bash
docker compose up --build
```

This starts:
- `sales_postgres` — PostgreSQL on port 5432
- `airflow_webserver` — Airflow UI on http://localhost:8080 (admin/admin)
- `airflow_scheduler` — DAG scheduler
- `etl_app` — Runs the pipeline once on startup

### Option C — Airflow only

After `docker compose up`, navigate to http://localhost:8080, enable the `sales_etl_pipeline` DAG, and trigger it manually or wait for the 08:00 UTC schedule.

---

## Running Tests

```bash
pytest tests/ -v
```

Test coverage includes:
- Empty CSV / missing file handling
- Wrong column names
- Invalid dates and negative prices
- PostgreSQL connection failure
- AWS S3 credential failure

---

## Database Schema

### Star Schema

```
dim_customer ──┐
dim_product  ──┤
dim_seller   ──┼──→  fact_sales
dim_date     ──┘
```

**fact_sales** grain: one row per order item.  
Key measures: `price`, `freight_value`, `payment_value`, `revenue`, `profit`, `delivery_time_days`, `review_score`.

See [`sql/schema.sql`](sql/schema.sql) for full DDL.

---

## SQL Analytics

15 production-grade queries in [`sql/analytics.sql`](sql/analytics.sql):

1. Top 10 customers by revenue
2. Monthly revenue
3. Revenue by state
4. Top selling products
5. Average order value
6. Customer retention breakdown
7. Repeat customer count
8. Top sellers
9. Late deliveries by state
10. Month-over-month growth (window function)
11. Revenue by category
12. Customer revenue rank (RANK + DENSE_RANK)
13. Running total revenue (cumulative window)
14. Average review score by category
15. Reusable views: `vw_monthly_revenue`, `vw_top_products`, `vw_customer_summary`

---

## Power BI Dashboard

Connect Power BI to PostgreSQL (`localhost:5432 / sales_db`) or import the transformed CSVs from `data/transformed/`.

**KPIs:**
- Total Revenue
- Total Orders
- Average Order Value
- Customer Count

**Charts:**
- Revenue by Month (line chart)
- Revenue by State (map)
- Top 10 Products (bar chart)
- Top Categories (treemap)
- Top Customers (table)
- Late Delivery Rate (gauge)

---

## Airflow DAG

DAG ID: `sales_etl_pipeline`  
Schedule: `0 8 * * *` (daily at 08:00 UTC)  
Retries: 2 with 5-minute delay

```
extract → validate → clean → transform → load → backup → notify
```

---

## Future Improvements

- Add dbt for SQL transformations and data lineage
- Stream real-time data via Apache Kafka
- Deploy to AWS (RDS, MWAA, Glue)
- Add Great Expectations for declarative data quality
- Build a Streamlit dashboard as a lightweight alternative to Power BI
- Implement CI/CD with GitHub Actions

---

## Resume Bullets

- Built a cloud-native ETL pipeline using Python, Pandas, PostgreSQL, Apache Airflow, Docker, and AWS S3 to process 100K+ e-commerce records.
- Designed a star schema data warehouse with fact and dimension tables and implemented automated data validation, cleaning, transformation, and loading workflows.
- Developed advanced SQL analytics using joins, CTEs, window functions, and indexes, and created an interactive Power BI dashboard to visualise business KPIs.
