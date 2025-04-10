import streamlit as st

def render_tile(label: str, value: str):
    """
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
