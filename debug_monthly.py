import pandas as pd

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading 'JUL' sheet from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='JUL', header=None, engine='openpyxl')
    
    print("--- ROWS 0-40 ---")
    print(df.iloc[0:40, 0:15].to_string())

except Exception as e:
    print(f"ERROR: {e}")
