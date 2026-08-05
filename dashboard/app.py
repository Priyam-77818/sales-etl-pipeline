"""
Streamlit Dashboard — Sales ETL Pipeline
Run: streamlit run dashboard/app.py
"""

import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Sales Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT         = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRANSFORMED  = os.path.join(ROOT, "data", "transformed")
CLEANED      = os.path.join(ROOT, "data", "cleaned")


# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    fact       = pd.read_csv(os.path.join(TRANSFORMED, "fact_sales.csv"))
    dim_cust   = pd.read_csv(os.path.join(TRANSFORMED, "dim_customer.csv"))
    dim_prod   = pd.read_csv(os.path.join(TRANSFORMED, "dim_product.csv"))
    dim_date   = pd.read_csv(os.path.join(TRANSFORMED, "dim_date.csv"))
    dim_seller = pd.read_csv(os.path.join(TRANSFORMED, "dim_seller.csv"))

    # Join dimensions onto fact
    df = fact.copy()
    df = df.merge(dim_cust[["customer_id", "customer_state", "customer_city"]], on="customer_id", how="left")
    df = df.merge(dim_prod[["product_id", "product_category_name"]], on="product_id", how="left")
    df = df.merge(dim_date[["date_id", "year", "month", "month_name", "quarter"]], on="date_id", how="left")
    df = df.merge(dim_seller[["seller_id", "seller_state"]], on="seller_id", how="left")

    # Clean up
    df["product_category_name"] = df["product_category_name"].fillna("unknown")
    df["customer_state"]        = df["customer_state"].fillna("unknown")
    df["revenue"]               = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)
    df["profit"]                = pd.to_numeric(df["profit"],  errors="coerce").fillna(0)
    df["review_score"]          = pd.to_numeric(df["review_score"], errors="coerce")
    df["delivery_time_days"]    = pd.to_numeric(df["delivery_time_days"], errors="coerce")
    df["late_delivery"]         = pd.to_numeric(df["late_delivery"], errors="coerce").fillna(0)

    return df

df = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png", width=60)
st.sidebar.title("Filters")

years = sorted(df["year"].dropna().unique().astype(int).tolist())
sel_years = st.sidebar.multiselect("Year", years, default=years)

states = sorted(df["customer_state"].dropna().unique().tolist())
sel_states = st.sidebar.multiselect("Customer State", states, default=states)

statuses = sorted(df["order_status"].dropna().unique().tolist())
sel_status = st.sidebar.multiselect("Order Status", statuses, default=statuses)

# Apply filters
mask = (
    df["year"].isin(sel_years) &
    df["customer_state"].isin(sel_states) &
    df["order_status"].isin(sel_status)
)
fdf = df[mask]

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🛒 E-Commerce Sales Analytics Dashboard")
st.caption("Olist Brazilian E-Commerce · Cloud-Native ETL Pipeline")
st.divider()

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)

total_revenue   = fdf["revenue"].sum()
total_orders    = fdf["order_id"].nunique()
aov             = total_revenue / total_orders if total_orders else 0
total_customers = fdf["customer_id"].nunique()
total_profit    = fdf["profit"].sum()
late_pct        = (fdf["late_delivery"].sum() / len(fdf) * 100) if len(fdf) else 0

k1.metric("💰 Total Revenue",   f"R$ {total_revenue:,.0f}")
k2.metric("📦 Total Orders",    f"{total_orders:,}")
k3.metric("🧾 Avg Order Value", f"R$ {aov:,.2f}")
k4.metric("👥 Customers",       f"{total_customers:,}")
k5.metric("📈 Total Profit",    f"R$ {total_profit:,.0f}")
k6.metric("⏰ Late Delivery %", f"{late_pct:.1f}%")

st.divider()

# ── Row 1: Revenue by Month + Order Status ────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📅 Monthly Revenue Trend")
    monthly = (
        fdf.groupby(["year", "month", "month_name"])["revenue"]
        .sum().reset_index()
        .sort_values(["year", "month"])
    )
    monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
    fig = px.area(
        monthly, x="period", y="revenue",
        labels={"period": "Month", "revenue": "Revenue (R$)"},
        color_discrete_sequence=["#4F8EF7"],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Order Status")
    status_counts = fdf.groupby("order_status")["order_id"].nunique().reset_index()
    status_counts.columns = ["status", "count"]
    fig2 = px.pie(
        status_counts, names="status", values="count",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300,
                       legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Revenue by State + Top Categories ─────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("🗺️ Revenue by State")
    state_rev = (
        fdf.groupby("customer_state")["revenue"]
        .sum().reset_index()
        .sort_values("revenue", ascending=True)
        .tail(15)
    )
    fig3 = px.bar(
        state_rev, x="revenue", y="customer_state",
        orientation="h",
        labels={"revenue": "Revenue (R$)", "customer_state": "State"},
        color="revenue",
        color_continuous_scale="Blues",
    )
    fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=350,
                       coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("🏷️ Top 10 Product Categories")
    cat_rev = (
        fdf.groupby("product_category_name")["revenue"]
        .sum().reset_index()
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    fig4 = px.bar(
        cat_rev, x="revenue", y="product_category_name",
        orientation="h",
        labels={"revenue": "Revenue (R$)", "product_category_name": "Category"},
        color="revenue",
        color_continuous_scale="Greens",
    )
    fig4.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=350,
                       coloraxis_showscale=False)
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Delivery + Review Score ───────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.subheader("🚚 Delivery Time Distribution")
    delivery = fdf["delivery_time_days"].dropna()
    delivery = delivery[delivery.between(0, 60)]
    fig5 = px.histogram(
        delivery, nbins=30,
        labels={"value": "Days", "count": "Orders"},
        color_discrete_sequence=["#F4A261"],
    )
    fig5.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.subheader("⭐ Review Score Distribution")
    reviews = fdf["review_score"].dropna().astype(int).value_counts().sort_index()
    fig6 = px.bar(
        x=reviews.index, y=reviews.values,
        labels={"x": "Review Score", "y": "Count"},
        color=reviews.index,
        color_continuous_scale="RdYlGn",
    )
    fig6.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280,
                       coloraxis_showscale=False)
    st.plotly_chart(fig6, use_container_width=True)

# ── Row 4: Payment Types + Quarterly Revenue ─────────────────────────────────
col7, col8 = st.columns(2)

with col7:
    st.subheader("💳 Payment Types")
    pay = fdf.groupby("payment_type")["order_id"].nunique().reset_index()
    pay.columns = ["payment_type", "count"]
    pay = pay.dropna()
    fig7 = px.pie(
        pay, names="payment_type", values="count",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.35,
    )
    fig7.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280,
                       legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.subheader("📆 Revenue by Quarter")
    qtr = (
        fdf.groupby(["year", "quarter"])["revenue"]
        .sum().reset_index()
        .sort_values(["year", "quarter"])
    )
    qtr["label"] = qtr["year"].astype(str) + " Q" + qtr["quarter"].astype(str)
    fig8 = px.bar(
        qtr, x="label", y="revenue",
        labels={"label": "Quarter", "revenue": "Revenue (R$)"},
        color="revenue",
        color_continuous_scale="Purples",
    )
    fig8.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280,
                       coloraxis_showscale=False)
    st.plotly_chart(fig8, use_container_width=True)

# ── Row 5: Top Customers Table ────────────────────────────────────────────────
st.divider()
st.subheader("🏆 Top 15 Customers by Revenue")
top_customers = (
    fdf.groupby(["customer_id", "customer_state"])
    .agg(
        total_orders   = ("order_id",      "nunique"),
        total_revenue  = ("revenue",       "sum"),
        avg_review     = ("review_score",  "mean"),
    )
    .reset_index()
    .sort_values("total_revenue", ascending=False)
    .head(15)
)
top_customers["total_revenue"] = top_customers["total_revenue"].map("R$ {:,.2f}".format)
top_customers["avg_review"]    = top_customers["avg_review"].map("{:.1f}".format)
top_customers.columns          = ["Customer ID", "State", "Orders", "Revenue", "Avg Review"]
st.dataframe(top_customers, use_container_width=True, hide_index=True)

# ── Row 6: Top Products Table ─────────────────────────────────────────────────
st.subheader("📦 Top 15 Products by Revenue")
top_products = (
    fdf.groupby(["product_id", "product_category_name"])
    .agg(
        times_sold    = ("order_id",     "count"),
        total_revenue = ("revenue",      "sum"),
        avg_review    = ("review_score", "mean"),
    )
    .reset_index()
    .sort_values("total_revenue", ascending=False)
    .head(15)
)
top_products["total_revenue"] = top_products["total_revenue"].map("R$ {:,.2f}".format)
top_products["avg_review"]    = top_products["avg_review"].map("{:.1f}".format)
top_products.columns          = ["Product ID", "Category", "Times Sold", "Revenue", "Avg Review"]
st.dataframe(top_products, use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Cloud-Native ETL Pipeline · Python · Pandas · PostgreSQL · "
    "Apache Airflow · Docker · AWS S3 · "
    f"Processing {len(df):,} order items from {df['order_id'].nunique():,} orders"
)
