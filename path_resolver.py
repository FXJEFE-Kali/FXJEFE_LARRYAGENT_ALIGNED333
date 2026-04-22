import os
import sys

MT5_ID = "AE2CC2E013FDE1E3CDF010AA51C60400"  # Only hardcoded (user-specific)

def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))  # Dynamic: script dir

def get_mt5_base():
    appdata = os.getenv('APPDATA')
    return os.path.join(appdata, 'MetaQuotes', 'Terminal', MT5_ID)

def get_mt5_files():
    return os.path.join(get_mt5_base(), 'MQL5', 'Files')

project_root = get_project_root()
marked_data = os.path.join(project_root, '..', 'marked data')  # Relative
models = os.path.join(project_root, '..', 'models')
config_dir = os.path.join(project_root, '..', 'config')
# etc. for others

if __name__ == '__main__':
    print(f"Project Root: {project_root}")
    print(f"MT5 Files: {get_mt5_files()}")
    print(f"Marked Data: {marked_data}")