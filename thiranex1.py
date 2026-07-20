import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Sales & Revenue Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Mock Data Generator (Fallback if no file is uploaded)
@st.cache_data
def load_mock_data():
    data = {
        "Date": pd.date_range(start="2025-01-01", periods=100, freq="D"),
        "Product": ["Laptop", "Smartphone", "Tablet", "Headphones", "Smartwatch"] * 20,
        "Category": ["Electronics", "Electronics", "Electronics", "Accessories", "Accessories"] * 20,
        "Quantity": [2, 5, 3, 10, 4] * 20,
        "Unit_Price": [1000, 800, 400, 150, 250] * 20,
    }
    df = pd.DataFrame(data)
    df["Revenue"] = df["Quantity"] * df["Unit_Price"]
    # Introduce some randomness/variance for realistic visuals
    df["Quantity"] = df["Quantity"] * df["Date"].dt.day.apply(lambda x: (x % 3) + 1)
    df["Revenue"] = df["Quantity"] * df["Unit_Price"]
    return df

# 3. Sidebar: File Uploader & Data Ingestion
st.sidebar.header("📁 Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload your Sales Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.sidebar.success("File uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
        df = load_mock_data()
else:
    st.sidebar.info("💡 Using demo dataset. Upload your own CSV/Excel to analyze your data!")
    df = load_mock_data()

# Ensure standard column naming and datetime format
df.columns = [col.strip().title().replace(" ", "_") for col in df.columns]

# Standardize date column if it exists
date_col = next((col for col in df.columns if 'Date' in col or 'Time' in col), None)
if date_col:
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(by=date_col)
else:
    # Synthesize a date column if missing
    df['Date'] = pd.date_range(start="2026-01-01", periods=len(df), freq="D")
    date_col = 'Date'

# Ensure Revenue column exists
if 'Revenue' not in df.columns:
    if 'Quantity' in df.columns and 'Unit_Price' in df.columns:
        df['Revenue'] = df['Quantity'] * df['Unit_Price']
    elif 'Sales' in df.columns:
        df['Revenue'] = df['Sales']
    else:
        st.error("Dataset must contain a 'Revenue', 'Sales', or 'Quantity' & 'Unit_Price' columns.")
        st.stop()

# 4. Sidebar: Interactive Filters & Slicers
st.sidebar.header("🔍 Filters & Slicers")

# Date Range Filter
min_date = df[date_col].min().to_pydatetime()
max_date = df[date_col].max().to_pydatetime()
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Category Filter (dynamically loaded if present, else fallback)
cat_col = next((col for col in df.columns if 'Category' in col or 'Type' in col), None)
if cat_col:
    categories = ['All'] + list(df[cat_col].unique())
    selected_cat = st.sidebar.selectbox("Select Category", categories)
else:
    selected_cat = 'All'

# Product Filter
prod_col = next((col for col in df.columns if 'Product' in col or 'Item' in col), None)
if prod_col:
    products = st.sidebar.multiselect("Filter by Specific Products", options=df[prod_col].unique(), default=[])

# Apply filters to Dataframe
filtered_df = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]

if selected_cat != 'All' and cat_col:
    filtered_df = filtered_df[filtered_df[cat_col] == selected_cat]

if prod_col and len(products) > 0:
    filtered_df = filtered_df[filtered_df[prod_col].isin(products)]

# 5. Main Dashboard Layout
st.title("📊 Sales & Revenue Analysis Dashboard")
st.markdown("Gain actionable insights into your business performance at a glance.")
st.markdown("---")

# 6. Top-Level KPIs Row
total_revenue = filtered_df['Revenue'].sum()
total_units = filtered_df['Quantity'].sum() if 'Quantity' in filtered_df.columns else 0
avg_order_value = total_revenue / len(filtered_df) if len(filtered_df) > 0 else 0

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(label="💰 Total Revenue", value=f"${total_revenue:,.2f}")
with kpi2:
    st.metric(label="📦 Total Units Sold", value=f"{int(total_units):,}" if total_units > 0 else "N/A")
with kpi3:
    st.metric(label="📈 Average Transaction Value", value=f"${avg_order_value:,.2f}")

st.markdown("---")

# 7. Visualization Row 1: Revenue Trends Over Time
st.subheader("📈 Revenue Trend Analysis")
trend_df = filtered_df.groupby(filtered_df[date_col].dt.to_period("M")).sum(numeric_only=True).reset_index()
trend_df[date_col] = trend_df[date_col].dt.to_timestamp()

fig_trend = px.line(
    trend_df, 
    x=date_col, 
    y='Revenue', 
    title="Monthly Revenue Growth Performance",
    labels={date_col: "Timeline", "Revenue": "Revenue ($)"},
    template="plotly_white"
)
fig_trend.update_traces(line_color="#2b5c8f", line_width=3, mode="lines+markers")
st.plotly_chart(fig_trend, use_container_width=True)

# 8. Visualization Row 2: Breakdown Graphs
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏆 Top Performing Products by Revenue")
    if prod_col:
        top_prod = filtered_df.groupby(prod_col)['Revenue'].sum().reset_index().sort_values(by='Revenue', ascending=False).head(10)
        fig_prod = px.bar(
            top_prod, 
            x='Revenue', 
            y=prod_col, 
            orientation='h', 
            title="Top 10 Products",
            labels={'Revenue': 'Total Revenue ($)', prod_col: 'Product Name'},
            color='Revenue',
            color_continuous_scale=px.colors.sequential.Blues,
            template="plotly_white"
        )
        fig_prod.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("No Product column detected to generate breakdown.")

with col_right:
    st.subheader("🥧 Category Contribution")
    if cat_col:
        cat_pie = filtered_df.groupby(cat_col)['Revenue'].sum().reset_index()
        fig_pie = px.pie(
            cat_pie, 
            values='Revenue', 
            names=cat_col, 
            title="Revenue Distribution by Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No Category column detected to generate breakdown.")

st.markdown("---")

# 9. Raw Data Preview Table
st.subheader("📋 Raw Filtered Transaction Ledger")
st.dataframe(filtered_df, use_container_width=True)