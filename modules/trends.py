import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def plot_trends(filtered_df, freq_map, selected_freq):
    # Group 1: History
    price_trend = (
        filtered_df
        .groupby(pd.Grouper(key="history_date", freq=freq_map[selected_freq]))["history_price"]
        .mean().dropna()
    )

    # Group 2: %
    filtered_df["saleEstimate_valueChange.saleDate"] = pd.to_datetime(filtered_df["saleEstimate_valueChange.saleDate"], errors='coerce')
    percentage_trend = (
        filtered_df
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