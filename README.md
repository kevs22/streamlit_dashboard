# 🏡 London Housing Market Dashboard

This interactive Streamlit dashboard visualizes and analyzes London’s residential housing market based on historical and estimated price data. It includes map-based exploration, borough leaderboards, ROI estimation, and price predictions.

<img width="1422" alt="dashboard_screen" src="https://github.com/user-attachments/assets/16b28eb4-49ba-4fca-8fd3-9094d70f5c4a" />

---

## 📦 Features

- 🗺️ Interactive map with borough-level choropleths
- 🏙️ Leaderboard of boroughs by average prices
- 🏡 Top 5 most expensive properties with street views
- 📈 Price trend explorer (monthly, quarterly, yearly)
- 🤖 Machine learning model (XGBoost) for price predictions
- 📊 Market overview: distribution by type, size, rooms
- 🧮 ROI calculator with historical growth insights

---

## 🔧 Setup Instructions

### 1. **Clone the repository**
```bash
git clone https://github.com/kevs22/streamlit_dashboard.git
cd streamlit_dashboard
```
### 2. Create & Activate a Virtual Environment

#### 💻 On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
#### 🖥️ On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### Download the Dataset
- Download the dataset from Kaggle: London House Price Dataset[🏡 London House Price Dataset]
- Move the CSV file to the following location
```bash
data/kaggle_london_house_price_data.csv
```






