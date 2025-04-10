import pandas as pd
import streamlit as st
from xgboost import XGBRegressor

class PriceEstimator:
    """
    A Streamlit component for estimating property sale prices using a trained model,
    and displaying similar properties based on user input.

    Attributes:
        df (pd.DataFrame): The dataset used for similarity comparison.
        model: The trained machine learning model for predicting prices.
        feature_columns (list): List of columns used by the model.
    """

    def __init__(self, df: pd.DataFrame, model: XGBRegressor, feature_columns: list[str]):
        """
        Initializes the PriceEstimator.

        Args:
            df (pd.DataFrame): Dataset used for finding similar properties.
            model (XGBRegressor): Trained XGBoost regression model for predicting prices.
            feature_columns (List[str]): List of feature names used for prediction.
        """
        self.df = df
        self.model = model
        self.feature_columns = feature_columns

    def render(self) -> None:
        """
        Renders the prediction form and displays predicted price along with similar properties.
        """
        st.markdown("### 🧠 Predict Sale Price")

        with st.form("prediction_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                borough_input = st.selectbox("Borough", sorted(self.df["borough"].dropna().astype(str).unique()))
                property_type_input = st.selectbox("Property Type", sorted(self.df["propertyType"].dropna().astype(str).unique()))

            with col2:
                floor_area_input = st.number_input("Floor Area (m²)", min_value=10, max_value=500, value=80)
                bedrooms_input = st.number_input("Bedrooms", min_value=0, max_value=10, value=2)

            with col3:
                bathrooms_input = st.number_input("Bathrooms", min_value=0, max_value=10, value=1)
                living_rooms_input = st.number_input("Living Rooms", min_value=0, max_value=8, value=1)

            submitted = st.form_submit_button("Predict Price")

        if submitted:
            input_data = pd.DataFrame([{
                "borough": borough_input,
                "floorAreaSqM": floor_area_input,
                "bedrooms": bedrooms_input,
                "bathrooms": bathrooms_input,
                "livingRooms": living_rooms_input,
                "propertyType": property_type_input
            }])

            input_encoded = pd.get_dummies(input_data)
            for col in self.feature_columns:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[self.feature_columns]

            predicted_price = self.model.predict(input_encoded)[0]
            st.success(f"💰 **Estimated Sale Price: £{predicted_price:,.0f}**")

            st.markdown("### 🔍 Similar Properties")
            similar_props = self._find_similar_properties(input_data)
            st.dataframe(similar_props[[
                "fullAddress", "borough", "floorAreaSqM", "bedrooms",
                "bathrooms", "livingRooms", "propertyType", "saleEstimate_currentPrice"
            ]])

    def _find_similar_properties(self, input_row: pd.DataFrame, n: int=5) -> pd.DataFrame:
        """
        Finds the top N most similar properties based on input criteria.

        Args:
            input_row (pd.DataFrame): A single-row DataFrame with user inputs.
            n (int, optional): Number of similar properties to return. Defaults to 5.

        Returns:
            pd.DataFrame: A DataFrame containing the most similar properties.
        """
        df_sim = self.df.copy()
        borough = input_row["borough"].iloc[0]
        property_type = input_row["propertyType"].iloc[0]

        df_sim = df_sim[df_sim["borough"] == borough]
        df_sim_type_match = df_sim[df_sim["propertyType"] == property_type]
        if not df_sim_type_match.empty:
            df_sim = df_sim_type_match

        if df_sim.empty:
            return pd.DataFrame()

        df_sim["similarity"] = (
            abs(df_sim["floorAreaSqM"] - input_row["floorAreaSqM"].iloc[0]) +
            abs(df_sim["bedrooms"] - input_row["bedrooms"].iloc[0]) * 10 +
            abs(df_sim["bathrooms"] - input_row["bathrooms"].iloc[0]) * 10 +
            abs(df_sim["livingRooms"] - input_row["livingRooms"].iloc[0]) * 5
        )

        return df_sim.sort_values("similarity").head(n)