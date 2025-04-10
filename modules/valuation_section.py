from modules.price_estimator import PriceEstimator
from modules.roi_caculator import ROICalculator
import streamlit as st

class ValuationSection:
    def __init__(self, df, model, feature_columns):
        self.df = df
        self.model = model
        self.feature_columns = feature_columns

    def render(self):
        PriceEstimator(self.df, self.model, self.feature_columns).render()
        ROICalculator(self.df).render()
