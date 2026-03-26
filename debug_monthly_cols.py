import pandas as pd

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    df = pd.read_excel(file_path, sheet_name='JUL', header=None, engine='openpyxl')
    
    print("--- JUL SHEET COLUMNS (Row 3) ---")
    headers = df.iloc[3, :].tolist()
    for i, h in enumerate(headers):
        print(f"Col {i}: {h}")

except Exception as e:
    print(f"ERROR: {e}")
