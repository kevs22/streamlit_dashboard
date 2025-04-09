import streamlit as st

def render_tile(label, value):
    st.markdown(
        f"""
        <style>
        h3.centered {{
            text-align: center;
            position: relative;
        }}
        h3.centered a {{
            display: none;  /* hide the anchor/paperclip */
        }}
        </style>

        <div style="
            background-color: #ebe3db;
            padding: 10px 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <p style="font-size: 14px; color: #555; text-align: center; margin: 0 0 4px;">{label}</p>
            <h3 class="centered" style="margin: 0; color: black;">{value}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
