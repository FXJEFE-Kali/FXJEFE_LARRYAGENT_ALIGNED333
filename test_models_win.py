import pandas as pd
import xgboost as xgb
import joblib
import numpy as np
import os

# Dynamic paths
project_root = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(project_root, '..', 'models')
csv_sample = os.path.join(project_root, '..', 'marked data', 'EURUSD.r_M1_202503112315_202506160942.csv')  # Sample CSV

xgb_path = os.path.join(models_dir, 'xgboost_model.json')
pkl_path = os.path.join(models_dir, 'my_model.pkl')

# Standard 43 feats (from config; sync by filling missing)
standard_feats = ["price", "atr", "ema_diff", "rsi", "garch_vol", "macd_diff", "vwap", "price_vwap_diff", "bb_position", "roc", "stochastic", "cci", "williams", "momentum", "realized_vol", "chaikin_vol", "adx", "rvi", "obv", "volume_delta", "ad_line", "vol_osc", "supertrend", "hma", "ichimoku_tenkan", "sar", "dpo", "spread", "sentiment", "rsi_m5", "rsi_h1", "macd_diff_m5", "macd_diff_h1", "atr_m5", "atr_h1", "vwap_m5", "vwap_h1", "roc_m5", "roc_h1", "stochastic_m5", "stochastic_h1", "cci_m5", "cci_h1"]

# Load sample data
df = pd.read_csv(csv_sample, nrows=100)  # Test 100 rows
available_feats = df.columns.tolist()
print(f"Available feats in CSV: {len(available_feats)} - {available_feats}")

# Sync: Add missing feats (fill 0)
for feat in standard_feats:
    if feat not in df.columns:
        df[feat] = 0.0
print(f"Synced to {len(df.columns)} feats")

# Load models
try:
    xgb_model = xgb.XGBClassifier()
    xgb_model.load_model(xgb_path)
    print("XGBoost loaded")
except Exception as e:
    print(f"XGBoost load failed: {e}")

try:
    pkl_model = joblib.load(pkl_path)
    print(f"PKL loaded (expected feats: {getattr(pkl_model, 'n_features_in_', 'unknown')})")
except Exception as e:
    print(f"PKL load failed: {e}")

# Test predict (first row)
test_row = df[standard_feats].iloc[0:1]
xgb_pred = xgb_model.predict(test_row)[0]
pkl_pred = pkl_model.predict(test_row)[0]
print(f"XGBoost pred: {xgb_pred}")
print(f"PKL pred: {pkl_pred}")

# Validate (if 'label' col; else mock)
if 'label' in df.columns:
    preds = xgb_model.predict(df[standard_feats])
    acc = np.mean(preds == df['label'])
    print(f"Validation Acc: {acc:.2%} (on 100 rows)")
else:
    print("No 'label' col - add for full validation")