import pandas as pd

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    df = pd.read_excel(file_path, sheet_name='PRESTAMOS', header=None, engine='openpyxl')
    
    print("--- HEADERS (Rows 0-10) ---")
    print(df.iloc[0:10, 0:20].to_string())
    
    # Buscar donde empiezan los datos reales
    for i in range(len(df)):
        if "SOCIOS" in str(df.iloc[i, 1]):
            print(f"SOCIOS found at row {i}")
            print(df.iloc[i:i+10, 0:20].to_string())
            break

except Exception as e:
    print(f"ERROR: {e}")
