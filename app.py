import streamlit as st
import pydeck as pdk
import joblib
from components.tiles import render_tile
from components.sidebar import sidebar_filters
from modules.utils import load_and_clean_data, load_local_css
from modules import BoroughMap, MarketOverview, ValuationSection

# Config
st.set_page_config(page_title="London Housing Market", layout="wide")
GOOGLE_API_KEY = st.secrets["google_maps_api_key"]
pdk.settings.mapbox_api_key = st.secrets["mapbox_key"]
model, feature_columns = joblib.load("model/xgb_estimator.pkl")
load_local_css()

# Load Data
df = load_and_clean_data()

# Sidebar filters
sidebar_data = sidebar_filters(df)
filtered_df = df[
    (df["history_date"] >= sidebar_data["selected_date_range"][0]) &
    (df["history_date"] <= sidebar_data["selected_date_range"][1])
]
if sidebar_data["selected_boroughs"]:
    filtered_df = filtered_df[filtered_df["borough"].isin(sidebar_data["selected_boroughs"])]

# Title 
st.title("London Housing Market Analysis")

# Render Map + KPI layout
left_col, right_col = st.columns([3, 1])
with left_col:
    map_section = BoroughMap(filtered_df)
    map_section.render()
with right_col:
    spacer_height_px = 146
    st.markdown(f'<div style="height: {spacer_height_px}px;"></div>', unsafe_allow_html=True)
    render_tile("Total Properties", f"{filtered_df['fullAddress'].nunique():,}")
    render_tile("Avg. Historical Sale Price", f"£{filtered_df['history_price'].mean():,.0f}")
    render_tile("Avg. Estimated Sale Price", f"£{filtered_df['saleEstimate_currentPrice'].mean():,.0f}")
    qm_df = filtered_df.dropna(subset=["saleEstimate_currentPrice", "floorAreaSqM"])
    render_tile("Avg. Price per m²", f"£{(qm_df['saleEstimate_currentPrice'] / qm_df['floorAreaSqM']).mean():,.0f}")

# Render Market Overview
market_overview = MarketOverview(filtered_df, GOOGLE_API_KEY)
market_overview.render()

# Render Valuation Section
valuation = ValuationSection(filtered_df, model, feature_columns)
valuation.render()