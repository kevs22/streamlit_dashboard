import streamlit as st

def load_local_css(file_path: str = "./assets/css/style.css"):
    with open(file_path) as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
