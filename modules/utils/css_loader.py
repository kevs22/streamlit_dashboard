import streamlit as st

def load_local_css(file_path: str = "./assets/css/style.css") -> None:
    """
    Loads and applies a local CSS file to the Streamlit app.

    This function reads the contents of a CSS file and injects it
    into the Streamlit app using `st.markdown()` with unsafe HTML.

    Args:
        file_path (str): Path to the CSS file. Defaults to './assets/css/style.css'.

    Returns:
        None.
    """
    with open(file_path) as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
