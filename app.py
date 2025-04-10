import streamlit as st
import pydeck as pdk
import pandas as pd
import joblib
import plotly.express as px
from modules.data_loader import load_and_clean_data
from modules.map_section import display_interactive_map_with_filter
from modules.kpi_tiles import render_tile
from components.property_dialog import render_property_details
from components.sidebar import sidebar_filters
from modules.trends import plot_trends
from modules.css_loader import load_local_css

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

# 📊 Market Overview Section
st.markdown("### 📊 Market Overview")

# Property Type Pie + Price Histogram side by side
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🏘️ Property Type Distribution")
    if not filtered_df.empty and "propertyType" in filtered_df.columns:
        type_counts = (
            filtered_df["propertyType"]
            .dropna()
            .value_counts()
            .reset_index()
            .rename(columns={"index": "Property Type", "propertyType": "Count"})
        )
        fig = px.pie(
            type_counts,
            names="Count",
            values="count",
            hole=0.4,
            color_discrete_sequence=[
                "#e6d4b7", "#d4a373", "#b47b5a", "#8f5e3b", "#f3ede5"
            ]

        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No property type data available.")

with col2:
    st.markdown("#### 💷 Estimated Sale Price Distribution")
    if "saleEstimate_currentPrice" in filtered_df.columns and not filtered_df["saleEstimate_currentPrice"].isna().all():
        fig = px.histogram(
            filtered_df.dropna(subset=["saleEstimate_currentPrice"]),
            x="saleEstimate_currentPrice",
            nbins=15,
            title="",
            labels={"saleEstimate_currentPrice": "Price (£)"},
            color_discrete_sequence=["#d4a373"]  
        )
        fig.update_layout(
            bargap=0.1,
            xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks=""
            ),
            yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks=""
            ))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No price data available.")

# Bedrooms + Bathrooms Histogram
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 🛏️ Number of Bedrooms")
    if "bedrooms" in filtered_df.columns and not filtered_df["bedrooms"].isna().all():
        fig = px.histogram(
            filtered_df.dropna(subset=["bedrooms"]),
            x="bedrooms",
            nbins=10,
            title="",
            labels={"bedrooms": "Bedrooms"},
            color_discrete_sequence=["#d4a373"]
        )
        fig.update_layout(
            bargap=0.1,
            xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks=""
            ),
            yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks=""
            ))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bedroom data available.")

with col4:
    st.markdown("#### 🛁 Number of Bathrooms")
    if "bathrooms" in filtered_df.columns and not filtered_df["bathrooms"].isna().all():
        fig = px.histogram(
            filtered_df.dropna(subset=["bathrooms"]),
            x="bathrooms",
            nbins=10,
            title="",
            labels={"bathrooms": "Bathrooms"},
            color_discrete_sequence=["#d4a373"]  
        )
        fig.update_layout(
            bargap=0.05,
            xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks=""
            ),
            yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks=""
            ))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bathroom data available.")

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

st.markdown("### 🧮 ROI Estimator")

# Get available boroughs from your data
available_boroughs = sorted(df["borough"].dropna().unique())

with st.form("roi_form"):
    col1, col2 = st.columns(2)

    with col1:
        selected_borough = st.selectbox("Borough", available_boroughs)
        purchase_price = st.number_input("Estimated Purchase Price (£)", min_value=50000, step=10000, value=750000)

    with col2:
        hold_years = st.selectbox("Hold Period (Years)", [1, 3, 5, 10], index=2)

        # Filter valid history data for the selected borough
        borough_prices = df[
            (df["borough"] == selected_borough) &
            (df["history_price"].notna()) &
            (df["history_date"].notna())
        ]

        # Use monthly average to get a stable growth rate
        if not borough_prices.empty:
            monthly_avg = (
                borough_prices
                .set_index("history_date")
                .resample("ME")["history_price"]
                .mean()
                .dropna()
            )

            if len(monthly_avg) >= 2:
                first_price = monthly_avg.iloc[0]
                last_price = monthly_avg.iloc[-1]
                years = (monthly_avg.index[-1] - monthly_avg.index[0]).days / 365

                annual_growth = ((last_price / first_price) ** (1 / years) - 1) * 100
            else:
                annual_growth = 3.0  # fallback if not enough monthly data
        else:
            annual_growth = 3.0  # fallback if no data at all

        appreciation_rate = st.slider(
            "Annual Appreciation Rate (%)",
            0.0,
            15.0,
            float(round(annual_growth, 1)),
            step=0.1
        )

    submitted = st.form_submit_button("Calculate ROI")

if submitted:
    rate_decimal = appreciation_rate / 100
    future_value = purchase_price * ((1 + rate_decimal) ** hold_years)
    roi = ((future_value - purchase_price) / purchase_price) * 100

    st.success(f"📈 **Projected Future Value:** £{future_value:,.0f}")
    st.info(f"💸 **ROI after {hold_years} years:** {roi:.2f}%")
