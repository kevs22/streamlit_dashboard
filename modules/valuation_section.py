from modules.price_estimator import PriceEstimator
from modules.roi_caculator import ROICalculator
import pandas as pd
from xgboost import XGBRegressor

class ValuationSection:
    """
    Combines components related to property valuation, including price prediction
    and ROI estimation.

    Attributes:
        df (pd.DataFrame): The housing dataset.
        model (XGBRegressor): Trained XGBoost model for price prediction.
        feature_columns (List[str]): Feature names used in the model.
    """

    def __init__(self, df: pd.DataFrame, model: XGBRegressor, feature_columns: list[str]):
        """
        Initializes the ValuationSection.

        Args:
            df (pd.DataFrame): DataFrame with housing data.
            model (XGBRegressor): Trained model used for estimating sale prices.
            feature_columns (list[str]): Columns used for prediction.
        """
        self.df = df
        self.model = model
        self.feature_columns = feature_columns

    def render(self) -> None:
        """
        Renders the full valuation section, including the price estimator
        and ROI calculator components.
        """
        PriceEstimator(self.df, self.model, self.feature_columns).render()
        ROICalculator(self.df).render()
