import pandas as pd

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    df = pd.read_excel(file_path, sheet_name='JUL', header=None, engine='openpyxl')
    print("--- HEADERS (Row 3-4) ---")
    print(df.iloc[2:5, :].to_string())
except Exception as e:
    print(f"ERROR: {e}")
