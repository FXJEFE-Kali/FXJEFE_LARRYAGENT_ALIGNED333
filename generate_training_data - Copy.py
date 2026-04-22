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

df = pd.read_csv('C:\Users\Administrator\Documents\FXJEFE_Project')
print("Columns in CSV:", df.columns.tolist())  # Add this to see whatâ€™s missing
df['label'] = 0  # Default to 'hold'
for i in range(1, len(df)):
    if df['price'].iloc[i] > df['price'].iloc[i-1] + df['atr'].iloc[i-1]:
        df.loc[i, 'label'] = 1  # 'buy'
    elif df['price'].iloc[i] < df['price'].iloc[i-1] - df['atr'].iloc[i-1]:
        df.loc[i, 'label'] = -1  # 'sell'
df = df[['price', 'atr', 'ema_diff', 'rsi', 'garch_vol', 'macd_diff', 'vwap', 'price_vwap_diff', 'bb_position', 'label']]
df.to_csv('training_data.csv', index=False)