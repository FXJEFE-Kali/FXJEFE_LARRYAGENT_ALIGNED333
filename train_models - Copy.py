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
import numpy as np
import joblib
import lightgbm as lgb
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os
import logging
from datetime import datetime

# Setup logging
log_file = f"train_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Define paths
PROJECT_DIR = r"C:\Users\Administrator\Documents\FXJEFE_Project"
DATA_PATH = os.path.join(PROJECT_DIR, "data", "training_data_updated.csv")
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
SEQUENCE_LENGTH = 10  # For LSTM, ensure this matches config.json

# Create models directory if it doesn't exist
os.makedirs(MODELS_DIR, exist_ok=True)

# Load training data
logging.info(f"Loading data from {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
logging.info(f"Loaded data with shape {df.shape}")

if df.shape[0] < 100:
    logging.error("Not enough data for training. Minimum 100 rows required.")
    exit(1)

# Feature columns (including 'price' to match config.json)
feature_cols = [col for col in df.columns if col not in ['time', 'symbol', 'signal']]
logging.info(f"Using features: {feature_cols}")

# Label column - assuming 'signal' is your target
target_col = 'signal'

# Map signals to numerical values if needed
if df[target_col].dtype == 'object':
    signal_mapping = {'sell': 0, 'hold': 1, 'buy': 2}
    df[target_col] = df[target_col].map(signal_mapping)
elif df[target_col].isin([-1, 0, 1]).all():
    df[target_col] = df[target_col] + 1  # Convert -1,0,1 to 0,1,2

# Prepare data for LightGBM
X = df[feature_cols]
y = df[target_col]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train LightGBM model
logging.info("Training LightGBM model...")
lgb_params = {
    'objective': 'multiclass',
    'num_class': 3,
    'metric': 'multi_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9
}
lgb_train = lgb.Dataset(X_train, y_train)
lgb_model = lgb.train(lgb_params, lgb_train, num_boost_round=100)
lgb_model_path = os.path.join(MODELS_DIR, "lightgbm_model.txt")
lgb_model.save_model(lgb_model_path)
logging.info(f"LightGBM model saved to {lgb_model_path}")

# Evaluate LightGBM
lgb_pred = np.argmax(lgb_model.predict(X_test), axis=1)
lgb_accuracy = (lgb_pred == y_test).mean()
logging.info(f"LightGBM accuracy on test set: {lgb_accuracy:.2f}")

# Prepare data for LSTM (sequence-based)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))

# Create sequences for LSTM
def create_sequences(data, seq_length):
    X_seq, y_seq = [], []
    for i in range(len(data) - seq_length):
        X_seq.append(data[i:i + seq_length])
        y_seq.append(y.iloc[i + seq_length])
    return np.array(X_seq), np.array(y_seq)

X_seq, y_seq = create_sequences(X_scaled, SEQUENCE_LENGTH)
X_train_seq, X_test_seq, y_train_seq, y_test_seq = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42)

# Train LSTM model
logging.info("Training LSTM model...")
lstm_model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(SEQUENCE_LENGTH, X_scaled.shape[1])),
    Dropout(0.2),
    LSTM(50),
    Dropout(0.2),
    Dense(3, activation='softmax')
])
lstm_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
lstm_model.fit(X_train_seq, y_train_seq, epochs=10, batch_size=32, validation_split=0.2, verbose=1)
lstm_model_path = os.path.join(MODELS_DIR, "lstm_model.h5")
lstm_model.save(lstm_model_path)
logging.info(f"LSTM model saved to {lstm_model_path}")

# Evaluate LSTM
lstm_loss, lstm_accuracy = lstm_model.evaluate(X_test_seq, y_test_seq, verbose=0)
logging.info(f"LSTM accuracy on test set: {lstm_accuracy:.2f}")