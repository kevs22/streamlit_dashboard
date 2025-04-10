import pandas as pd
import streamlit as st
from modules import BoroughMap

@st.cache_data
def load_and_clean_data(filepath: str="data/kaggle_london_house_price_data.csv") -> pd.DataFrame:
    """
    Loads, cleans, and enriches the London housing dataset.

    This function performs the following steps:
    - Reads the dataset from a CSV file.
    - Converts date columns to datetime.
    - Sorts rows by address and history timestamps.
    - Assigns boroughs based on latitude and longitude using BoroughMap.
    - Removes duplicate address-date entries, keeping the most recent ingestion.

    Args:
        filepath (str): Path to the CSV file containing the housing data.
            Defaults to "data/kaggle_london_house_price_data.csv".

    Returns:
        pd.DataFrame: A cleaned and enriched DataFrame with borough information.
    """

    df = pd.read_csv(filepath)
    df["history_date"] = pd.to_datetime(df["history_date"])
    df["saleEstimate_ingestedAt"] = pd.to_datetime(df["saleEstimate_ingestedAt"], errors="coerce")
    df_sorted = df.sort_values(by=["fullAddress", "history_date", "saleEstimate_ingestedAt"], ascending=[True, True, False])

    mapper = BoroughMap(df_sorted)
    df_sorted = mapper.assign_boroughs()

    return df_sorted.drop_duplicates(subset=["fullAddress", "history_date"], keep="first")
