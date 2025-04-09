import streamlit as st
from .borough_mapper import BoroughMapper

@st.fragment
def display_interactive_map_with_filter(df):
    st.markdown("### 🔥 London Property Heatmap")
    metric = st.selectbox(
        "Color boroughs by:",
        options=[
            "Count",
            "Avg. Estimated Price",
            "Avg. History Price",
            "Avg. Size",
            "Avg. Price per m²"
        ],
        index=0,
        key="choropleth_metric_selector"
    )
    mapper = BoroughMapper("data/london_boroughs")
    st.pydeck_chart(mapper.plot_choropleth_pydeck(df, metric), use_container_width=True)
