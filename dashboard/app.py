"""
Streamlit Dashboard — E-Commerce Sales Analytics
Run: streamlit run dashboard/app.py
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #0f1117; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1400px; }

/* Hide streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* KPI Card */
.kpi-card {
    background: linear-gradient(135deg, #1e2130 0%, #252836 100%);
    border: 1px solid #2d3045;
    border-radius: 14px;
    padding: 20px 22px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    height: 110px;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(79,142,247,0.15);
}
.kpi-label {
    font-size: 11px; font-weight: 500;
    color: #8892a4; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 8px;
}
.kpi-value {
    font-size: 26px; font-weight: 700; color: #ffffff;
    line-height: 1;
}
.kpi-icon { font-size: 18px; margin-bottom: 4px; }

/* KPI accent colors */
.kpi-blue  { border-top: 3px solid #4F8EF7; }
.kpi-green { border-top: 3px solid #22c55e; }
.kpi-purple{ border-top: 3px solid #a855f7; }
.kpi-orange{ border-top: 3px solid #f97316; }
.kpi-teal  { border-top: 3px solid #14b8a6; }
.kpi-red   { border-top: 3px solid #ef4444; }

/* Section header */
.section-header {
    font-size: 15px; font-weight: 600; color: #e2e8f0;
    margin: 0 0 12px 0; padding-left: 10px;
    border-left: 3px solid #4F8EF7;
}

/* Chart container */
.chart-box {
    background: #1e2130;
    border: 1px solid #2d3045;
    border-radius: 14px;
    padding: 18px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161823;
    border-right: 1px solid #2d3045;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {
    color: #8892a4 !important; font-size: 12px !important;
    text-transform: uppercase; letter-spacing: 0.8px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1e2130;
    border-radius: 10px; padding: 4px; gap: 4px;
    border: 1px solid #2d3045;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; color: #8892a4;
    font-size: 13px; font-weight: 500;
    padding: 8px 18px;
}
.stTabs [aria-selected="true"] {
    background: #4F8EF7 !important;
    color: white !important;
}

/* Table */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Use bundled parquet files (dashboard/data/) for cloud deployment
# Falls back to data/transformed/ for local runs
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(os.path.join(DATA_DIR, "fact_sales.parquet")):
    DATA_DIR = os.path.join(ROOT, "data", "transformed")

def _read(name):
    parquet = os.path.join(DATA_DIR, f"{name}.parquet")
    csv     = os.path.join(DATA_DIR, f"{name}.csv")
    if os.path.exists(parquet):
        return pd.read_parquet(parquet)
    return pd.read_csv(csv)

# ── Chart theme ───────────────────────────────────────────────────────────────
CHART_THEME = dict(
    paper_bgcolor="#1e2130",
    plot_bgcolor="#1e2130",
    font=dict(family="Inter", color="#8892a4", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
)
# Applied separately via update_xaxes / update_yaxes to avoid duplicate key conflicts
_AXIS_STYLE = dict(gridcolor="#2d3045", zeroline=False, showline=False)

def styled(fig, height=300, **extra):
    """Apply CHART_THEME + axis styles to any figure, with optional overrides."""
    fig.update_layout(**{**CHART_THEME, **extra}, height=height)
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    return fig
COLORS = ["#4F8EF7","#22c55e","#a855f7","#f97316","#14b8a6","#ef4444","#eab308","#06b6d4"]

# ── Load & cache data ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data...")
def load_data():
    fact    = _read("fact_sales")
    d_cust  = _read("dim_customer")
    d_prod  = _read("dim_product")
    d_date  = _read("dim_date")
    d_sell  = _read("dim_seller")

    df = fact.copy()
    df = df.merge(d_cust[["customer_id","customer_state","customer_city"]], on="customer_id", how="left")
    df = df.merge(d_prod[["product_id","product_category_name"]], on="product_id", how="left")
    df = df.merge(d_date[["date_id","year","month","month_name","quarter"]], on="date_id", how="left")
    df = df.merge(d_sell[["seller_id","seller_state"]], on="seller_id", how="left")

    df["product_category_name"] = df["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    df["customer_state"]        = df["customer_state"].fillna("unknown").str.upper()
    df["revenue"]               = pd.to_numeric(df["revenue"],            errors="coerce").fillna(0)
    df["profit"]                = pd.to_numeric(df["profit"],             errors="coerce").fillna(0)
    df["review_score"]          = pd.to_numeric(df["review_score"],       errors="coerce")
    df["delivery_time_days"]    = pd.to_numeric(df["delivery_time_days"], errors="coerce")
    df["late_delivery"]         = pd.to_numeric(df["late_delivery"],      errors="coerce").fillna(0)
    df["payment_type"]          = df["payment_type"].fillna("unknown").str.replace("_"," ").str.title()
    df["order_status"]          = df["order_status"].fillna("unknown").str.title()
    return df

df = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    st.markdown("---")

    years = sorted(df["year"].dropna().unique().astype(int).tolist())
    sel_years = st.multiselect("📅 Year", years, default=years)

    states = sorted(df["customer_state"].dropna().unique().tolist())
    sel_states = st.multiselect("📍 State", states, default=states)

    statuses = sorted(df["order_status"].dropna().unique().tolist())
    sel_status = st.multiselect("📦 Order Status", statuses, default=["Delivered"])

    st.markdown("---")
    st.markdown("<small style='color:#555'>Cloud-Native ETL Pipeline<br>Olist Brazilian E-Commerce</small>", unsafe_allow_html=True)

# Apply filters
if not sel_years:   sel_years  = years
if not sel_states:  sel_states = states
if not sel_status:  sel_status = statuses

fdf = df[
    df["year"].isin(sel_years) &
    df["customer_state"].isin(sel_states) &
    df["order_status"].isin(sel_status)
]

# ── Header ─────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 11])
with col_logo:
    st.markdown("<div style='font-size:48px;margin-top:8px'>🛒</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("""
        <div style='padding-top:6px'>
            <h1 style='margin:0;font-size:28px;font-weight:700;color:#ffffff'>
                E-Commerce Sales Analytics
            </h1>
            <p style='margin:2px 0 0 0;color:#4F8EF7;font-size:13px;font-weight:500'>
                Olist Brazilian Dataset &nbsp;·&nbsp; Cloud-Native ETL Pipeline &nbsp;·&nbsp;
                {:,} order items &nbsp;·&nbsp; {:,} orders
            </p>
        </div>
    """.format(len(fdf), fdf["order_id"].nunique()), unsafe_allow_html=True)

st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_rev  = fdf["revenue"].sum()
total_ord  = fdf["order_id"].nunique()
aov        = total_rev / total_ord if total_ord else 0
total_cust = fdf["customer_id"].nunique()
total_prof = fdf["profit"].sum()
late_pct   = (fdf["late_delivery"].sum() / len(fdf) * 100) if len(fdf) else 0
avg_review = fdf["review_score"].mean()

kpis = [
    ("💰", "Total Revenue",    f"R$ {total_rev:,.0f}",   "kpi-blue"),
    ("📦", "Total Orders",     f"{total_ord:,}",          "kpi-green"),
    ("🧾", "Avg Order Value",  f"R$ {aov:,.2f}",          "kpi-purple"),
    ("👥", "Customers",        f"{total_cust:,}",          "kpi-orange"),
    ("📈", "Total Profit",     f"R$ {total_prof:,.0f}",   "kpi-teal"),
    ("⭐", "Avg Review",       f"{avg_review:.2f} / 5",   "kpi-red") if not pd.isna(avg_review)
        else ("⭐", "Avg Review", "N/A", "kpi-red"),
]

cols = st.columns(6)
for col, (icon, label, value, css) in zip(cols, kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card {css}">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Geography", "📦 Products", "👥 Customers"])

# ═══════════════════════════════════════════════════════════
# TAB 1 — Overview
# ═══════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Row 1: Monthly Revenue + Order Status
    c1, c2 = st.columns([3, 1])

    with c1:
        st.markdown("<p class='section-header'>Monthly Revenue Trend</p>", unsafe_allow_html=True)
        monthly = (
            fdf.groupby(["year","month"])
            .agg(revenue=("revenue","sum"), orders=("order_id","nunique"))
            .reset_index().sort_values(["year","month"])
        )
        monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["period"], y=monthly["revenue"],
            fill="tozeroy", mode="lines",
            line=dict(color="#4F8EF7", width=2.5),
            fillcolor="rgba(79,142,247,0.12)",
            name="Revenue",
            hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.0f}<extra></extra>",
        ))
        styled(fig, height=300)
        fig.update_xaxes(tickangle=-45, tickfont=dict(size=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("<p class='section-header'>Order Status</p>", unsafe_allow_html=True)
        sc = fdf.groupby("order_status")["order_id"].nunique().reset_index()
        sc.columns = ["status","count"]
        fig2 = go.Figure(go.Pie(
            labels=sc["status"], values=sc["count"],
            hole=0.55,
            marker=dict(colors=COLORS, line=dict(color="#1e2130", width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>Orders: %{value:,}<extra></extra>",
        ))
        fig2.add_annotation(text=f"<b>{total_ord:,}</b><br><span style='font-size:10px'>orders</span>",
                            x=0.5, y=0.5, showarrow=False,
                            font=dict(size=14, color="white"), align="center")
        styled(fig2, height=300, legend=dict(orientation="h", y=-0.15, font=dict(size=11)))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Row 2: Revenue by Quarter + Payment Types + Delivery dist
    c3, c4, c5 = st.columns(3)

    with c3:
        st.markdown("<p class='section-header'>Revenue by Quarter</p>", unsafe_allow_html=True)
        qdf = (
            fdf.groupby(["year","quarter"])["revenue"]
            .sum().reset_index().sort_values(["year","quarter"])
        )
        qdf["label"] = qdf["year"].astype(str) + " Q" + qdf["quarter"].astype(str)
        fig3 = px.bar(qdf, x="label", y="revenue",
                      color="revenue", color_continuous_scale=["#1a3a6b","#4F8EF7"],
                      labels={"label":"","revenue":"Revenue (R$)"},
                      text=qdf["revenue"].apply(lambda x: f"R${x/1e6:.1f}M"))
        fig3.update_traces(textposition="outside", textfont_size=10,
                           hovertemplate="<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>")
        styled(fig3, height=280, coloraxis_showscale=False, uniformtext_minsize=8)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with c4:
        st.markdown("<p class='section-header'>Payment Types</p>", unsafe_allow_html=True)
        pay = fdf.groupby("payment_type")["order_id"].nunique().reset_index()
        pay.columns = ["type","count"]
        pay = pay.dropna().sort_values("count", ascending=True)
        fig4 = px.bar(pay, x="count", y="type", orientation="h",
                      color="count", color_continuous_scale=["#1a3a6b","#a855f7"],
                      labels={"count":"Orders","type":""})
        fig4.update_traces(hovertemplate="<b>%{y}</b><br>Orders: %{x:,}<extra></extra>")
        styled(fig4, height=280, coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    with c5:
        st.markdown("<p class='section-header'>Delivery Time (Days)</p>", unsafe_allow_html=True)
        dtime = fdf["delivery_time_days"].dropna()
        dtime = dtime[dtime.between(1, 60)]
        fig5 = px.histogram(dtime, nbins=25,
                             color_discrete_sequence=["#14b8a6"],
                             labels={"value":"Days","count":"Orders"})
        fig5.update_traces(hovertemplate="<b>%{x} days</b><br>Orders: %{y}<extra></extra>")
        styled(fig5, height=280, showlegend=False, xaxis_title="Days", yaxis_title="Orders")
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    # Row 3: Review scores
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c6, c7 = st.columns([1, 2])

    with c6:
        st.markdown("<p class='section-header'>Review Score Distribution</p>", unsafe_allow_html=True)
        rev = fdf["review_score"].dropna().astype(int).value_counts().sort_index()
        colors_rev = ["#ef4444","#f97316","#eab308","#22c55e","#4F8EF7"]
        fig6 = px.bar(x=rev.index, y=rev.values,
                      color=rev.index.astype(str),
                      color_discrete_sequence=colors_rev,
                      labels={"x":"Score","y":"Count","color":"Score"})
        fig6.update_traces(hovertemplate="<b>⭐ %{x}</b><br>Count: %{y:,}<extra></extra>")
        styled(fig6, height=260, showlegend=False)
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

    with c7:
        st.markdown("<p class='section-header'>MoM Revenue Growth %</p>", unsafe_allow_html=True)
        mom = monthly.copy()
        mom["growth"] = mom["revenue"].pct_change() * 100
        mom = mom.dropna()
        colors_mom = ["#22c55e" if v >= 0 else "#ef4444" for v in mom["growth"]]
        fig7 = go.Figure(go.Bar(
            x=mom["period"], y=mom["growth"],
            marker_color=colors_mom,
            hovertemplate="<b>%{x}</b><br>Growth: %{y:.1f}%<extra></extra>",
        ))
        fig7.add_hline(y=0, line_color="#4d5568", line_width=1)
        styled(fig7, height=260)
        fig7.update_xaxes(tickangle=-45, tickfont=dict(size=9))
        fig7.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════
# TAB 2 — Geography
# ═══════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<p class='section-header'>Revenue by State</p>", unsafe_allow_html=True)
        state_rev = (
            fdf.groupby("customer_state")
            .agg(revenue=("revenue","sum"), orders=("order_id","nunique"))
            .reset_index().sort_values("revenue", ascending=True)
        )
        fig = px.bar(state_rev, x="revenue", y="customer_state", orientation="h",
                     color="revenue", color_continuous_scale=["#1a3a6b","#4F8EF7"],
                     labels={"revenue":"Revenue (R$)","customer_state":"State"},
                     custom_data=["orders"])
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>Revenue: R$ %{x:,.0f}<br>Orders: %{customdata[0]:,}<extra></extra>"
        )
        styled(fig, height=450, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("<p class='section-header'>Late Delivery Rate by State</p>", unsafe_allow_html=True)
        late_state = (
            fdf.groupby("customer_state")
            .agg(total=("order_id","count"), late=("late_delivery","sum"))
            .reset_index()
        )
        late_state["late_pct"] = (late_state["late"] / late_state["total"] * 100).round(1)
        late_state = late_state.sort_values("late_pct", ascending=True)
        fig2 = px.bar(late_state, x="late_pct", y="customer_state", orientation="h",
                      color="late_pct", color_continuous_scale=["#22c55e","#eab308","#ef4444"],
                      labels={"late_pct":"Late %","customer_state":"State"})
        fig2.update_traces(
            hovertemplate="<b>%{y}</b><br>Late: %{x:.1f}%<extra></extra>"
        )
        styled(fig2, height=450, coloraxis_showscale=False)
        fig2.update_xaxes(ticksuffix="%")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # State summary table
    st.markdown("<p class='section-header'>State Summary</p>", unsafe_allow_html=True)
    state_summary = (
        fdf.groupby("customer_state")
        .agg(
            Orders     = ("order_id",      "nunique"),
            Revenue    = ("revenue",       "sum"),
            Profit     = ("profit",        "sum"),
            Avg_Review = ("review_score",  "mean"),
            Late_Pct   = ("late_delivery", "mean"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    state_summary["Revenue"]    = state_summary["Revenue"].map("R$ {:,.0f}".format)
    state_summary["Profit"]     = state_summary["Profit"].map("R$ {:,.0f}".format)
    state_summary["Avg_Review"] = state_summary["Avg_Review"].map("{:.2f}".format)
    state_summary["Late_Pct"]   = state_summary["Late_Pct"].map("{:.1%}".format)
    state_summary.columns = ["State","Orders","Revenue","Profit","Avg Review","Late %"]
    st.dataframe(state_summary, use_container_width=True, hide_index=True, height=320)

# ═══════════════════════════════════════════════════════════
# TAB 3 — Products
# ═══════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<p class='section-header'>Top 15 Categories by Revenue</p>", unsafe_allow_html=True)
        cat = (
            fdf.groupby("product_category_name")
            .agg(revenue=("revenue","sum"), orders=("order_id","count"))
            .reset_index().sort_values("revenue", ascending=True).tail(15)
        )
        fig = px.bar(cat, x="revenue", y="product_category_name", orientation="h",
                     color="revenue", color_continuous_scale=["#064e3b","#22c55e"],
                     labels={"revenue":"Revenue (R$)","product_category_name":"Category"},
                     custom_data=["orders"])
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>Revenue: R$ %{x:,.0f}<br>Items: %{customdata[0]:,}<extra></extra>"
        )
        styled(fig, height=460, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("<p class='section-header'>Avg Review Score by Category (Top 15)</p>", unsafe_allow_html=True)
        cat_rev = (
            fdf.groupby("product_category_name")
            .agg(avg_review=("review_score","mean"), count=("review_score","count"))
            .reset_index()
            .dropna()
            .query("count >= 10")
            .sort_values("avg_review", ascending=True)
            .tail(15)
        )
        fig2 = px.bar(cat_rev, x="avg_review", y="product_category_name", orientation="h",
                      color="avg_review",
                      color_continuous_scale=["#7c3aed","#a855f7","#e879f9"],
                      range_color=[1,5],
                      labels={"avg_review":"Avg Score","product_category_name":"Category"})
        fig2.update_traces(
            hovertemplate="<b>%{y}</b><br>Avg: %{x:.2f} ⭐<extra></extra>"
        )
        styled(fig2, height=460, coloraxis_showscale=False)
        fig2.update_xaxes(range=[1, 5])
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Top products table
    st.markdown("<p class='section-header'>Top 20 Products</p>", unsafe_allow_html=True)
    top_prod = (
        fdf.groupby(["product_id","product_category_name"])
        .agg(
            Times_Sold = ("order_id",     "count"),
            Revenue    = ("revenue",      "sum"),
            Avg_Review = ("review_score", "mean"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(20)
    )
    top_prod["Revenue"]    = top_prod["Revenue"].map("R$ {:,.2f}".format)
    top_prod["Avg_Review"] = top_prod["Avg_Review"].map("{:.2f}".format)
    top_prod["product_id"] = top_prod["product_id"].str[:12] + "..."
    top_prod.columns = ["Product ID","Category","Times Sold","Revenue","Avg Review"]
    st.dataframe(top_prod, use_container_width=True, hide_index=True, height=340)

# ═══════════════════════════════════════════════════════════
# TAB 4 — Customers
# ═══════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    # Repeat vs one-time
    with c1:
        st.markdown("<p class='section-header'>Repeat vs One-Time Customers</p>", unsafe_allow_html=True)
        cust_orders = fdf.groupby("customer_id")["order_id"].nunique()
        repeat = (cust_orders > 1).sum()
        one_time = (cust_orders == 1).sum()
        fig = go.Figure(go.Pie(
            labels=["One-Time","Repeat"],
            values=[one_time, repeat],
            hole=0.55,
            marker=dict(colors=["#4F8EF7","#22c55e"],
                        line=dict(color="#1e2130", width=3)),
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{one_time+repeat:,}</b><br>total",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=13, color="white"), align="center")
        styled(fig, height=300, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # CLV distribution
    with c2:
        st.markdown("<p class='section-header'>Customer Lifetime Value Dist.</p>", unsafe_allow_html=True)
        clv = fdf.groupby("customer_id")["revenue"].sum()
        clv = clv[clv < clv.quantile(0.98)]
        fig2 = px.histogram(clv, nbins=30,
                             color_discrete_sequence=["#f97316"],
                             labels={"value":"CLV (R$)","count":"Customers"})
        fig2.update_traces(
            hovertemplate="<b>R$ %{x:.0f}</b><br>Customers: %{y}<extra></extra>"
        )
        styled(fig2, height=300, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Orders per customer
    with c3:
        st.markdown("<p class='section-header'>Orders per Customer</p>", unsafe_allow_html=True)
        opc = cust_orders.value_counts().reset_index()
        opc.columns = ["orders","customers"]
        opc = opc[opc["orders"] <= 5].sort_values("orders")
        fig3 = px.bar(opc, x="orders", y="customers",
                      color="customers",
                      color_continuous_scale=["#1a3a6b","#14b8a6"],
                      labels={"orders":"# Orders","customers":"Customers"})
        fig3.update_traces(
            hovertemplate="<b>%{x} order(s)</b><br>Customers: %{y:,}<extra></extra>"
        )
        styled(fig3, height=300, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # Top customers table
    st.markdown("<p class='section-header'>Top 20 Customers by Revenue</p>", unsafe_allow_html=True)
    top_cust = (
        fdf.groupby(["customer_id","customer_state","customer_city"])
        .agg(
            Orders     = ("order_id",      "nunique"),
            Revenue    = ("revenue",       "sum"),
            Profit     = ("profit",        "sum"),
            Avg_Review = ("review_score",  "mean"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(20)
    )
    top_cust["Revenue"]    = top_cust["Revenue"].map("R$ {:,.2f}".format)
    top_cust["Profit"]     = top_cust["Profit"].map("R$ {:,.2f}".format)
    top_cust["Avg_Review"] = top_cust["Avg_Review"].map("{:.2f}".format)
    top_cust["customer_id"] = top_cust["customer_id"].str[:14] + "..."
    top_cust.columns = ["Customer ID","State","City","Orders","Revenue","Profit","Avg Review"]
    st.dataframe(top_cust, use_container_width=True, hide_index=True, height=400)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; color:#3d4458; font-size:12px; padding:12px;
            border-top:1px solid #2d3045; margin-top:10px'>
    Cloud-Native ETL Pipeline &nbsp;·&nbsp;
    Python · Pandas · PostgreSQL · Apache Airflow · Docker · AWS S3 &nbsp;·&nbsp;
    <a href='https://github.com/Priyam-77818/sales-etl-pipeline'
       style='color:#4F8EF7; text-decoration:none'>GitHub ↗</a>
</div>
""", unsafe_allow_html=True)
