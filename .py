import json
import os
import logging

# Path to the config file
CONFIG_PATH = 'C:\\Users\\Administrator\\Documents\\FXJEFE_Project\\config.json'

# Load the config file safely
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: Could not find config file at {CONFIG_PATH}")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Config file has invalid format - {e}")
    exit(1)

# Set up logging
log_file = os.path.join(config['log_path'], 'script.log')  # Change 'script.log' to match the script’s name
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logging.info("Script started and configuration loaded successfully")

import json
import os
with open('C:\\Users\\Administrator\\Documents\\FXJEFE_Project\\config.json', 'r') as f:
    config = json.load(f)
import pandas as pd
from sklearn.ensemble import VotingClassifier
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv('C:\Users\Administrator\Documents\FXJEFE_Project\train_ensemble.py')
X_train = df[['price', 'atr', 'ema_diff', 'rsi', 'garch_vol', 'macd_diff', 'vwap', 'price_vwap_diff', 'bb_position']]
y_train = df['label']

xgb_model = XGBClassifier(n_estimators=100, max_depth=5)
rf_model = RandomForestClassifier(n_estimators=100, max_depth=5)
ensemble_model = VotingClassifier(estimators=[('xgb', xgb_model), ('rf', rf_model)], voting='soft')
ensemble_model.fit(X_train, y_train)
joblib.dump(ensemble_model, 'ensemble_model.pkl')