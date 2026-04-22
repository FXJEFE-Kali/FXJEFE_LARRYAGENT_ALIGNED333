import sys
import os
import importlib.util

# Dynamic paths
project_root = os.path.dirname(os.path.abspath(__file__))
pipeline_path = os.path.join(project_root, 'run_pipeline.py')
deps_path = os.path.join(project_root, '..', 'deps', 'COMBINED_REQUIREMENTS.txt')
sample_input = os.path.join(project_root, '..', 'marked data', 'EURUSD.r_M1_202503112315_202506160942.csv')  # Mock input

# Check deps (install if missing)
os.system(f"pip install -r {deps_path} --quiet")

# Load/validate run_pipeline.py
spec = importlib.util.spec_from_file_location("run_pipeline", pipeline_path)
module = importlib.util.module_from_spec(spec)
sys.modules["run_pipeline"] = module
spec.loader.exec_module(module)
print("run_pipeline loaded")

# Test run (mock args; adjust per script)
try:
    # Assume run_pipeline.main(input_csv, output_dir)
    output_dir = os.path.join(project_root, 'test_output')
    os.makedirs(output_dir, exist_ok=True)
    module.main(sample_input, output_dir)  # Or your entry function
    print("Pipeline ran OK - check test_output/")
except Exception as e:
    print(f"Pipeline failed: {e}")

# Validate outputs (e.g., check if processed CSV exists)
test_output = os.path.join(output_dir, 'processed_EURUSD.csv')
if os.path.exists(test_output):
    df = pd.read_csv(test_output)
    print(f"Output valid (rows: {len(df)}, cols: {len(df.columns)})")
else:
    print("No output - check script")