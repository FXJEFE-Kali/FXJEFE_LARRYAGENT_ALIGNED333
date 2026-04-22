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

# Read the features CSV
df = pd.read_csv("FXJEFE_Features.csv")
print(f"Number of rows in FXJEFE_Features.csv: {len(df)}")

# Check if 'signal' column exists
if 'signal' not in df.columns:
    print("Error: 'signal' column is missing in FXJEFE_Features.csv. Please ensure parse_log_to_csv.py ran successfully.")
    print("Available columns:", df.columns.tolist())
    exit(1)

# Map signals to labels
df['label'] = df['signal'].map({'buy': 1, 'sell': -1, 'hold': 0}).fillna(0)
df.to_csv("training_data.csv", index=False)
print("training_data.csv generated successfully.")