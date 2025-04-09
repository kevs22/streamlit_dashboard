import streamlit as st
import pydeck as pdk
import pandas as pd
import joblib
from modules.data_loader import load_and_clean_data
from modules.map_section import display_interactive_map_with_filter
from modules.kpi_tiles import render_tile
from components.property_dialog import render_property_details
from modules.trends import plot_trends

# Config
st.set_page_config(page_title="London Housing Market", layout="wide")
GOOGLE_API_KEY = st.secrets["google_maps_api_key"]
pdk.settings.mapbox_api_key = st.secrets["mapbox_key"]
model, feature_columns = joblib.load("model/xgb_estimator.pkl")

df = load_and_clean_data()

# Filters
with st.sidebar:
    st.image("assets/london_company_logo.png")

    selected_boroughs = st.multiselect("Select Borough(s)", sorted(df["borough"].dropna().unique()))
    min_date = pd.to_datetime(df['history_date'].min()).to_pydatetime()
    max_date = pd.to_datetime(df['history_date'].max()).to_pydatetime()
    selected_date_range = st.slider("Select Date Range", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM")

# Filtered data
filtered_df = df[(df["history_date"] >= selected_date_range[0]) & (df["history_date"] <= selected_date_range[1])]
if selected_boroughs:
    filtered_df = filtered_df[filtered_df["borough"].isin(selected_boroughs)]

# Title 
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)
st.title("London Housing Market Analysis")

# Map + KPI layout
left_col, right_col = st.columns([3, 1])
with left_col:
    display_interactive_map_with_filter(filtered_df)
with right_col:
    spacer_height_px = 146
    st.markdown(f'<div style="height: {spacer_height_px}px;"></div>', unsafe_allow_html=True)

    render_tile("Total Properties", f"{filtered_df['fullAddress'].nunique():,}")
    render_tile("Avg. Historical Sale Price", f"£{filtered_df['history_price'].mean():,.0f}")
    render_tile("Avg. Estimated Sale Price", f"£{filtered_df['saleEstimate_currentPrice'].mean():,.0f}")
    qm_df = filtered_df.dropna(subset=["saleEstimate_currentPrice", "floorAreaSqM"])
    render_tile("Avg. Price per m²", f"£{(qm_df['saleEstimate_currentPrice'] / qm_df['floorAreaSqM']).mean():,.0f}")

# Borough Leaderboard: average sale price
leaderboard_df = (
    filtered_df
    .dropna(subset=["saleEstimate_currentPrice", "borough"])
    .groupby("borough")
    .agg(avg_price=("saleEstimate_currentPrice", "mean"))
    .reset_index()
)

# Sort by price descending
leaderboard_df = leaderboard_df.sort_values(by="avg_price", ascending=False).reset_index(drop=True)

# Compute comparison to overall avg (optional)
overall_avg = filtered_df["saleEstimate_currentPrice"].mean()
leaderboard_df["vs_overall"] = ((leaderboard_df["avg_price"] - overall_avg) / overall_avg) * 100

st.markdown("### 🏙️ Borough Leaderboard by Average Sale Price")

with st.container(height=150):

    for i, row in leaderboard_df.iterrows():
        rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        delta = f"(+{row['vs_overall']:.1f}%)" if row["vs_overall"] > 0 else f"({row['vs_overall']:.1f}%)"

        st.markdown(
            f"""
            <div style='
                background-color: #f3ede5;
                padding: 8px 12px;
                margin-bottom: 6px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            '>
                <span style='font-weight: bold;'>{rank_emoji} {row["borough"]}</span>
                <span>£{row["avg_price"]:,.0f} <span style='color: {"green" if row["vs_overall"] > 0 else "red"};'>{delta}</span></span>
            </div>
            """,
            unsafe_allow_html=True
        )

# Top 5 properties
st.markdown("### 🏡 Top 5 Most Expensive Properties")
top_5 = (
    filtered_df.dropna(subset=["saleEstimate_currentPrice", "latitude", "longitude"])
    .drop_duplicates(subset=["fullAddress"])
    .sort_values(by="saleEstimate_currentPrice", ascending=False)
    .head(5)
)

cols = st.columns(5)


for i, (index, row) in enumerate(top_5.iterrows()):
    lat, lon = row["latitude"], row["longitude"]
    price = row["saleEstimate_currentPrice"]
    borough = row["borough"]

    # Generate Street View image URL (smaller size for tile)
    img_url = (
        f"https://maps.googleapis.com/maps/api/streetview"
        f"?size=200x150&location={lat},{lon}&key={GOOGLE_API_KEY}" # 
    )

    # Render tile in respective column
    with cols[i]:
        st.markdown(
            f"""
            <div style="
                background-color: #ebe3db;
                padding: 5px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                min-height: 160px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                margin-bottom: 0px;
            ">
                 <div> <img src="{img_url}" alt="Street View" style="width: 100%; border-radius: 6px; margin-bottom: 5px;">
                    <p style="margin: 0 0 4px; font-weight: bold;">£{price:,.0f}</p>
                    <p style="margin: 0; font-size: 12px; color: #444;">{borough}</p>
                 </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        button_key = f"details_btn_{index}"
        if st.button("View Details", key=button_key, use_container_width=True):
            # Call the dialog function, passing the data for THIS row
            render_property_details(row, GOOGLE_API_KEY)


# Trends
st.markdown("### 🕒 Price Trends Over Time")
freq_map = {"Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}
selected_freq = st.selectbox("Select Time Aggregation", list(freq_map.keys()), index=0)
plot_trends(filtered_df, freq_map, selected_freq)

# Price Estimate
st.markdown("### 🧠 Predict Sale Price")

with st.form("prediction_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        borough_input = st.selectbox("Borough", sorted(df["borough"].dropna().astype(str).unique()))
        property_type_input = st.selectbox("Property Type", sorted(df["propertyType"].dropna().astype(str).unique()))
    with col2:
        floor_area_input = st.number_input("Floor Area (m²)", min_value=10, max_value=500, value=80)
        bedrooms_input = st.number_input("Bedrooms", min_value=0, max_value=10, value=2)
    with col3:
        bathrooms_input = st.number_input("Bathrooms", min_value=0, max_value=10, value=1)
        living_rooms_input = st.number_input("Living Rooms", min_value=0, max_value=8, value=1)

    submit = st.form_submit_button("Predict Price")

if submit:
    input_data = pd.DataFrame([{
        "borough": borough_input,
        "floorAreaSqM": floor_area_input,
        "bedrooms": bedrooms_input,
        "bathrooms": bathrooms_input,
        "livingRooms": living_rooms_input,
        "propertyType": property_type_input
    }])

    input_encoded = pd.get_dummies(input_data)
    for col in feature_columns:
        if col not in input_encoded.columns:
            input_encoded[col] = 0
    input_encoded = input_encoded[feature_columns]

    predicted_price = model.predict(input_encoded)[0]
    st.success(f"💰 **Estimated Sale Price: £{predicted_price:,.0f}**")

    # Find similar properties
    st.markdown("### 🔍 Similar Properties")

    def find_similar(df, input_row, n=5):
        df_sim = df.copy()
        borough = input_row["borough"].iloc[0]
        property_type = input_row["propertyType"].iloc[0]

        # Step 1: Filter by borough
        df_sim = df_sim[df_sim["borough"] == borough]

        # Step 2: Further filter by property type
        df_sim_type_match = df_sim[df_sim["propertyType"] == property_type]

        # If no exact matches, fallback to just borough matches
        if not df_sim_type_match.empty:
            df_sim = df_sim_type_match

        if df_sim.empty:
            return pd.DataFrame()  # Nothing to show

        # Step 3: Calculate similarity score
        df_sim["similarity"] = (
            abs(df_sim["floorAreaSqM"] - input_row["floorAreaSqM"].iloc[0]) +
            abs(df_sim["bedrooms"] - input_row["bedrooms"].iloc[0]) * 10 +
            abs(df_sim["bathrooms"] - input_row["bathrooms"].iloc[0]) * 10 +
            abs(df_sim["livingRooms"] - input_row["livingRooms"].iloc[0]) * 5
        )

        return df_sim.sort_values("similarity").head(n)


    similar_props = find_similar(df, input_data)
    st.dataframe(similar_props[["fullAddress", "borough", "floorAreaSqM", "bedrooms", "bathrooms", "livingRooms", "propertyType", "saleEstimate_currentPrice"]])
