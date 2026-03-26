import pandas as pd

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading 'PRESTAMOS' from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='PRESTAMOS', header=None, engine='openpyxl')
    
    # Mostrar las primeras 50 filas y columnas relevantes
    print("--- FIRST 50 ROWS ---")
    print(df.iloc[0:50, 0:15].to_string())

except Exception as e:
    print(f"ERROR: {e}")
