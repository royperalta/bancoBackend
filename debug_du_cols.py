import pandas as pd
import io

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading 'D.U.' from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='D.U.', header=None, engine='openpyxl')
    
    # Ver las cabeceras de los meses (Fila 32 usualmente)
    print("--- HEADERS (Row 32) ---")
    print(df.iloc[31, 0:20].to_list())
    
    # Ver data del primer socio (Fila 33)
    print("--- FIRST SOCIO DATA (Row 33) ---")
    print(df.iloc[32, 0:20].to_list())

except Exception as e:
    print(f"ERROR: {e}")
