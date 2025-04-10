import streamlit as st
import pandas as pd

def sidebar_filters(df: pd.DataFrame):
    """
    """
    with st.sidebar:
        st.image("assets/london_company_logo.png")

        # Define default date range
        default_min_date = pd.to_datetime(df["history_date"].min()).to_pydatetime()
        default_max_date = pd.to_datetime(df["history_date"].max()).to_pydatetime()

        # Handle reset
        if st.session_state.get("reset_filters", False):
            st.session_state["borough_filter"] = []
            st.session_state["date_filter"] = (default_min_date, default_max_date)
            st.session_state["reset_filters"] = False

        # Widgets
        st.multiselect(
            "Select Borough(s)",
            options=sorted(df["borough"].dropna().unique()),
            key="borough_filter"
        )

        st.slider(
            "Select Date Range",
            min_value=default_min_date,
            max_value=default_max_date,
            value=(default_min_date, default_max_date),
            key="date_filter",
            format="YYYY-MM"
        )

        if st.button("🔄 Reset Filters"):
            st.session_state["reset_filters"] = True
            st.rerun()

    return {
        "selected_boroughs": st.session_state["borough_filter"],
        "selected_date_range": st.session_state["date_filter"]
    }
