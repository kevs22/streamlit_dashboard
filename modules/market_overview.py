import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from components.property_dialog import render_property_details


class MarketOverview:
    """
    Renders various market analytics and visual insights for the London housing dataset.

    This class is responsible for generating:
    - A borough-level leaderboard
    - Top expensive properties
    - Property trends (prices and percentage change)
    - Distribution of property types, prices, bedrooms, and bathrooms
    """

    def __init__(self, df: pd.DataFrame, google_api_key: str = None):
        """
        Initializes the MarketOverview with dataset and optional Google Maps API key.

        Args:
            df (pd.DataFrame): The cleaned housing dataset.
            google_api_key (str, optional): Key used for Google Street View thumbnails.
        """
        self.df = df
        self.google_api_key = google_api_key

    def render(self) -> None:
        """
        Renders the full market overview section in Streamlit.

        This includes:
        - Borough leaderboard
        - Top 5 expensive properties
        - Time series trends
        - Property type pie chart and price distribution
        - Bedroom and bathroom histograms
        """
        self._render_leaderboard()
        self._render_top_properties()

        st.markdown("### 📊 Market Overview")
        self._render_price_trends()
        self._render_property_type_and_price()
        self._render_bed_bath_histograms()

    def _render_leaderboard(self) -> None:
        """Displays a leaderboard of boroughs sorted by average sale price."""
        leaderboard_df = (
        self.df
        .dropna(subset=["saleEstimate_currentPrice", "borough"])
        .groupby("borough")
        .agg(avg_price=("saleEstimate_currentPrice", "mean"))
        .reset_index()
        )

        leaderboard_df = leaderboard_df.sort_values(by="avg_price", ascending=False).reset_index(drop=True)
        overall_avg = self.df["saleEstimate_currentPrice"].mean()
        leaderboard_df["vs_overall"] = ((leaderboard_df["avg_price"] - overall_avg) / overall_avg) * 100

        st.markdown("### 🏙️ Borough Leaderboard by Average Sale Price")

        with st.container(height=150):

            for i, row in leaderboard_df.iterrows():
                rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                delta = f"(+{row['vs_overall']:.1f}%)" if row["vs_overall"] > 0 else f"({row['vs_overall']:.1f}%)"
                delta_class = "leaderboard-delta-positive" if row["vs_overall"] > 0 else "leaderboard-delta-negative"

                st.markdown(
                f"""
                <div class="leaderboard-row">
                    <span style='font-weight: bold;'>{rank_emoji} {row["borough"]}</span>
                    <span>£{row["avg_price"]:,.0f} <span class="{delta_class}">{delta}</span></span>
                </div>
                """,
                unsafe_allow_html=True
                )

    def _render_top_properties(self) -> None:
        """Displays the top 5 most expensive properties with Street View thumbnails."""
        st.markdown("### 🏡 Top 5 Most Expensive Properties")
        top_5 = (
            self.df.dropna(subset=["saleEstimate_currentPrice", "latitude", "longitude"])
            .drop_duplicates(subset=["fullAddress"])
            .sort_values(by="saleEstimate_currentPrice", ascending=False)
            .head(5)
        )
        cols = st.columns(5)

        for i, (index, row) in enumerate(top_5.iterrows()):
            lat, lon = row["latitude"], row["longitude"]
            price = row["saleEstimate_currentPrice"]
            borough = row["borough"]

            img_url = (
                f"https://maps.googleapis.com/maps/api/streetview"
                f"?size=200x150&location={lat},{lon}&key={self.google_api_key}" # 
            )

            # Render tiles
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="top-property-tile">
                        <div>
                            <img src="{img_url}" alt="Street View" class="top-property-image">
                            <p class="top-property-price">£{price:,.0f}</p>
                            <p class="top-property-borough">{borough}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                button_key = f"details_btn_{index}"
                if st.button("View Details", key=button_key, use_container_width=True):
                    render_property_details(row, self.google_api_key)

    @st.fragment
    def _render_price_trends(self) -> None:
        """Plots time series charts for historical price and % change over time."""
        freq_map = {"Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}
        selected_freq = st.selectbox("Select Time Aggregation", list(freq_map.keys()), index=0)
        
        price_trend = (
            self.df
            .groupby(pd.Grouper(key="history_date", freq=freq_map[selected_freq]))["history_price"]
            .mean().dropna()
        )
        self.df["saleEstimate_valueChange.saleDate"] = pd.to_datetime(
            self.df["saleEstimate_valueChange.saleDate"], errors='coerce'
        )
        
        percentage_trend = (
            self.df
            .dropna(subset=["saleEstimate_valueChange.percentageChange", "saleEstimate_valueChange.saleDate"])
            .groupby(pd.Grouper(key="saleEstimate_valueChange.saleDate", freq=freq_map[selected_freq]))["saleEstimate_valueChange.percentageChange"]
            .mean().dropna()
        )

        col1, col2 = st.columns(2)

        with col1:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=price_trend.index, y=price_trend.values, mode='lines', line=dict(color='black')))
            fig1.update_layout(title="Avg. Historical Prices", height=350, xaxis_title="Date", yaxis_title="£")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=percentage_trend.index, y=percentage_trend.values, mode='lines', line=dict(color='darkred')))
            fig2.update_layout(title="Avg. % Price Change", height=350, xaxis_title="Date", yaxis_title="%")
            st.plotly_chart(fig2, use_container_width=True)

    def _render_property_type_and_price(self) -> None:
        """Renders a pie chart of property types and a histogram of sale prices."""
        col1, col2 = st.columns(2)

        # Property Type Pie Chart
        with col1:
            st.markdown("#### 🏘️ Property Type Distribution")
            if not self.df.empty and "propertyType" in self.df.columns:
                type_counts = (
                    self.df["propertyType"]
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

        # Sale Price Histogram
        with col2:
            st.markdown("#### 💷 Estimated Sale Price Distribution")
            if "saleEstimate_currentPrice" in self.df.columns and not self.df["saleEstimate_currentPrice"].isna().all():
                fig = px.histogram(
                    self.df.dropna(subset=["saleEstimate_currentPrice"]),
                    x="saleEstimate_currentPrice",
                    nbins=15,
                    labels={"saleEstimate_currentPrice": "Price (£)"},
                    color_discrete_sequence=["#d4a373"]
                )
                fig.update_layout(
                    bargap=0.1,
                    xaxis=dict(showgrid=False, zeroline=False, showline=False, ticks=""),
                    yaxis=dict(showgrid=False, zeroline=False, showline=False, ticks="")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No price data available.")

    def _render_bed_bath_histograms(self) -> None:
        """Displays side-by-side histograms for bedroom and bathroom counts."""
        col1, col2 = st.columns(2)

        self._render_histogram(
            column="bedrooms",
            label="🛏️ Number of Bedrooms",
            x_label="Bedrooms",
            color="#d4a373",
            col=col1
        )

        self._render_histogram(
            column="bathrooms",
            label="🛁 Number of Bathrooms",
            x_label="Bathrooms",
            color="#d4a373",
            col=col2
        )

    def _render_histogram(self, column: str, label: str, x_label: str, color: str, col: st.delta_generator.DeltaGenerator) -> None:
        """
        Generic histogram renderer used for bedroom/bathroom visualizations.

        Args:
            column (str): The DataFrame column to visualize.
            label (str): Title of the chart.
            x_label (str): X-axis label.
            color (str): Hex color used for the bars.
            col (st.delta_generator.DeltaGenerator): Streamlit column container to render the chart in.

        Returns:
            None.
        """
        with col:
            st.markdown(f"#### {label}")
            if column in self.df.columns and not self.df[column].isna().all():
                fig = px.histogram(
                    self.df.dropna(subset=[column]),
                    x=column,
                    nbins=10,
                    labels={column: x_label},
                    color_discrete_sequence=[color]
                )
                fig.update_layout(
                    bargap=0.1,
                    xaxis=dict(showgrid=False, zeroline=False, showline=False, ticks=""),
                    yaxis=dict(showgrid=False, zeroline=False, showline=False, ticks="")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No {column} data available.")
