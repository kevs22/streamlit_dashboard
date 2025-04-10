import streamlit as st
import pandas as pd

class ROICalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def render(self):
        st.markdown("### 🧮 ROI Estimator")

        boroughs = sorted(self.df["borough"].dropna().unique())

        with st.form("roi_form"):
            col1, col2 = st.columns(2)

            with col1:
                selected_borough = st.selectbox("Borough", boroughs)
                purchase_price = st.number_input("Estimated Purchase Price (£)", min_value=50000, step=10000, value=750000)

            with col2:
                hold_years = st.selectbox("Hold Period (Years)", [1, 3, 5, 10], index=2)

                prices = self.df[
                    (self.df["borough"] == selected_borough) &
                    self.df["history_price"].notna() &
                    self.df["history_date"].notna()
                ]

                if not prices.empty:
                    monthly_avg = (
                        prices
                        .set_index("history_date")
                        .resample("ME")["history_price"]
                        .mean()
                        .dropna()
                    )

                    if len(monthly_avg) >= 2:
                        first_price = monthly_avg.iloc[0]
                        last_price = monthly_avg.iloc[-1]
                        years = (monthly_avg.index[-1] - monthly_avg.index[0]).days / 365
                        annual_growth = ((last_price / first_price) ** (1 / years) - 1) * 100
                    else:
                        annual_growth = 3.0
                else:
                    annual_growth = 3.0

                appreciation_rate = st.slider(
                    "Annual Appreciation Rate (%)",
                    0.0,
                    15.0,
                    float(round(annual_growth, 1)),
                    step=0.1
                )

            submitted = st.form_submit_button("Calculate ROI")

        if submitted:
            rate = appreciation_rate / 100
            future_value = purchase_price * ((1 + rate) ** hold_years)
            roi = ((future_value - purchase_price) / purchase_price) * 100

            st.success(f"📈 **Projected Future Value:** £{future_value:,.0f}")
            st.info(f"💸 **ROI after {hold_years} years:** {roi:.2f}%")