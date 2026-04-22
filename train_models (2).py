import pandas as pd
import numpy as np
import joblib
import logging
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('C:\\Users\\Administrator\\Documents\\FXJEFE_Fresh\\Logs\\train_models.log'),
        logging.StreamHandler()
    ]
)

def load_config():
    config_path = 'C:\\Users\\Administrator\\Documents\\FXJEFE_Fresh\\config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config.json: {e}")
        exit(1)

def train_model(data, features, target='label'):
    try:
        X = data[features]
        y = data[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        score = model.score(X_test, y_test)
        logging.info(f"Model trained with test score: {score}")
        return model
    except Exception as e:
        logging.error(f"Error training model: {e}")
        return None

def main():
    config = load_config()
    data_path = os.path.join(config['data_output_path'], 'FXJEFE_Features_with_labels.csv')
    model_path = os.path.join(config['models_path'], 'ensemble_model.pkl')
    
    try:
        data = pd.read_csv(data_path)
        model = train_model(data, config['features'])
        if model:
            joblib.dump(model, model_path)
            logging.info(f"Model saved to {model_path}")
    except Exception as e:
        logging.error(f"Error processing data: {e}")

if __name__ == "__main__":
    main()