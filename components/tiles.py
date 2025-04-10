import streamlit as st

def render_tile(label: str, value: str) -> None:
    """
    Renders a KPI tile displaying a label and value with custom styling.

    This function outputs a styled HTML block that resembles a summary tile,
    typically used for KPIs such as total properties, average prices, etc.

    Args:
        label (str): The descriptive text shown above the value (e.g. "Avg. Price").
        value (str): The formatted value to be displayed (e.g. "£450,000").
    
    Returns:
        None.
    """
    st.markdown(
        f"""
        <div class="tile">
            <p class="tile-label">{label}</p>
            <h3 class="tile-value">{value}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
