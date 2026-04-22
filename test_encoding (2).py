import pandas as pd
import os

files = [
    'log.txt',
    'FXJEFE_Features.csv',
    'FXJEFE_trades_outcomes.csv',
    'FXJEFE_trades.csv'
]

base_dir = 'C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Files'

for file in files:
    try:
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(base_dir, file), encoding='utf-8')
            print(f'Successfully read {file} as UTF-8')
        else:
            with open(os.path.join(base_dir, file), 'r', encoding='utf-8') as f:
                content = f.read()
            print(f'Successfully read {file} as UTF-8')
    except Exception as e:
        print(f'Error reading {file}: {str(e)}')