import pandas as pd
import io

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading CAJA from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='CAJA', header=None, engine='openpyxl')
    
    # Extraer la cabecera de las columnas 11 en adelante para egresos
    print("--- EGRESOS HEADER (Row 3, Col 11+) ---")
    header_row = df.iloc[3, 11:22]
    print(header_row.to_list())
    
    print("--- EGRESOS DATA (Rows 5-15, Col 11+) ---")
    data_rows = df.iloc[5:16, 11:22]
    print(data_rows.to_string())

except Exception as e:
    print(f"ERROR: {e}")
