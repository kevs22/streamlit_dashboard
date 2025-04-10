import sys
import os
import joblib
import pandas as pd
import xgboost as xgb

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import root_mean_squared_error, r2_score

# Append project root to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.utils.data_loader import load_and_clean_data

# -----------------------------
# 1. Load & Preprocess Data
# -----------------------------
df = load_and_clean_data("data/kaggle_london_house_price_data.csv")

# Drop rows with missing target or key features
required_cols = [
    "saleEstimate_currentPrice", "borough", "floorAreaSqM",
    "bedrooms", "bathrooms", "livingRooms", "propertyType"
]
df = df.dropna(subset=required_cols)

# Define features & target
X = df[["borough", "floorAreaSqM", "bedrooms", "bathrooms", "livingRooms", "propertyType"]]
y = pd.to_numeric(df["saleEstimate_currentPrice"], errors="coerce")

# One-hot encode categorical features
X_encoded = pd.get_dummies(X, columns=["borough", "propertyType"])

# -----------------------------
# 2. Train/Test Split
# -----------------------------
# First: train+val vs test
X_temp, X_test, y_temp, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)

# Second: train vs val (used for CV)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.25, random_state=42)

# Merge train and val for hyperparameter tuning
X_train_full = pd.concat([X_train, X_val])
y_train_full = pd.concat([y_train, y_val])

# -----------------------------
# 3. Define Search Space
# -----------------------------
param_dist = {
    "n_estimators": [100, 300, 500],
    "max_depth": [3, 5, 7, 10],
    "learning_rate": [0.01, 0.05, 0.1, 0.2],
    "subsample": [0.6, 0.8, 1.0],
    "colsample_bytree": [0.6, 0.8, 1.0],
    "gamma": [0, 1, 5],
}

# -----------------------------
# 4. Randomized Search with CV
# -----------------------------
xgb_model = xgb.XGBRegressor()

random_search = RandomizedSearchCV(
    estimator=xgb_model,
    param_distributions=param_dist,
    n_iter=20,
    scoring="neg_root_mean_squared_error",
    cv=3,
    verbose=1,
    random_state=42,
    n_jobs=-1,
)

random_search.fit(X_train_full, y_train_full)
best_model = random_search.best_estimator_

print(f"\n🔥 Best Parameters Found:")
for k, v in random_search.best_params_.items():
    print(f"  {k}: {v}")

# -----------------------------
# 5. Evaluate on Test Set
# -----------------------------
y_pred = best_model.predict(X_test)
rmse = root_mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n✅ FINAL TEST RESULTS (TUNED):")
print(f"RMSE: £{rmse:,.2f}")
print(f"R² Score: {r2:.4f}")

# -----------------------------
# 6. Save Model
# -----------------------------
joblib.dump((best_model, list(X_encoded.columns)), "model/xgb_estimator.pkl")
