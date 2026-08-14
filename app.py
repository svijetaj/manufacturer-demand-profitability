"""
Main Streamlit Application: Enterprise Demand & Profit Intelligence Platform
"""

import streamlit as st
import datetime
from src.db import query_df
from src.components.overview import render_overview
from src.components.demand import render_demand
from src.components.profit import render_profit
from src.components.budget_opex import render_budget_opex

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="Finance & Demand Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium look & feel
st.markdown("""
    <style>
        .main {
            background-color: #0b0f19;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
            color: #38bdf8;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.9rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 48px;
            white-space: pre-wrap;
            border-radius: 8px 8px 0px 0px;
            font-size: 15px;
            font-weight: 600;
            padding: 0 16px;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar Global Filters
st.sidebar.title("🎛️ Filters & Controls")
st.sidebar.caption("Filter data across all analytical pages.")

# Date Range Picker
min_date = datetime.date(2025, 1, 1)
max_date = datetime.date(2026, 12, 31)

date_range = st.sidebar.date_input(
    "📅 Date Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) < 2:
    date_range = (date_range[0], date_range[0])

# Product Categories Filter
categories = query_df("SELECT DISTINCT Product_Category FROM Dim_Product ORDER BY 1;")['Product_Category'].tolist()
selected_categories = st.sidebar.multiselect("📦 Product Categories:", options=categories, default=[])

# Customer Segment Filter
segments = query_df("SELECT DISTINCT Customer_Segment FROM Dim_Customer ORDER BY 1;")['Customer_Segment'].tolist()
selected_segments = st.sidebar.multiselect("👥 Customer Segments:", options=segments, default=[])

# Sales Region Filter
regions = query_df("SELECT DISTINCT Sales_Region FROM Dim_Customer ORDER BY 1;")['Sales_Region'].tolist()
selected_regions = st.sidebar.multiselect("🌍 Sales Regions:", options=regions, default=[])

st.sidebar.markdown("---")
st.sidebar.info("💡 **DuckDB Engine Active**\nConnecting to `finance.duckdb`.\nSpanning 5,000 transactions (2025–2026).")

# 3. Main Navigation Header & Tabs
st.title("💼 Enterprise Demand & Profit Intelligence Platform")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Overview",
    "📦 Demand Analytics",
    "💰 Profit Waterfall & Margins",
    "🏢 OpEx & Budget Targets"
])

with tab1:
    render_overview(date_range, selected_categories, selected_segments, selected_regions)

with tab2:
    render_demand(date_range, selected_categories, selected_segments, selected_regions)

with tab3:
    render_profit(date_range, selected_categories, selected_segments, selected_regions)

with tab4:
    render_budget_opex(date_range)
