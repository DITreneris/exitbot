import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Print the Python path for debugging
print("Python path:")
for p in sys.path:
    print(f"  - {p}")

# Run the Streamlit app
os.system("streamlit run exitbot/frontend/refactored_hr_app.py") 