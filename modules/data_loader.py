import pandas as pd
import streamlit as st
from .borough_mapper import BoroughMapper

@st.cache_data
def load_and_clean_data(filepath: str="data/kaggle_london_house_price_data.csv"):

    df = pd.read_csv(filepath)
    df["history_date"] = pd.to_datetime(df["history_date"])
    df["saleEstimate_ingestedAt"] = pd.to_datetime(df["saleEstimate_ingestedAt"], errors="coerce")
    df_sorted = df.sort_values(by=["fullAddress", "history_date", "saleEstimate_ingestedAt"], ascending=[True, True, False])

    mapper = BoroughMapper("data/london_boroughs")
    df_sorted = mapper.assign_boroughs(df_sorted)

    return df_sorted.drop_duplicates(subset=["fullAddress", "history_date"], keep="first")
