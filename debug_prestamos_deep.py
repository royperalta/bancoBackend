import pandas as pd

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    df = pd.read_excel(file_path, sheet_name='PRESTAMOS', header=None, engine='openpyxl')
    
    print("--- HEADERS AND FIRST SOCIO ---")
    # Row 3 contains general headers
    # Row 4 contains Mes 0, Mes 1... labels or dates
    print(df.iloc[3:7, 0:15].to_string())
    
    # Check if there are other columns for interest in this sheet
    print("--- COLUMNS 15-25 ---")
    print(df.iloc[3:7, 15:25].to_string())

except Exception as e:
    print(f"ERROR: {e}")
