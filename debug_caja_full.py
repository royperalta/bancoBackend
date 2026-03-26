import pandas as pd
import io

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading complete sheet 'CAJA' from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='CAJA', header=None, engine='openpyxl')
    
    print("Row count:", len(df))
    # Imprimir bloques de 100 filas para ver donde termina la data real y empieza el resto
    for start in range(0, len(df), 100):
        print(f"--- ROWS {start} to {start+100} ---")
        # Solo mostrar si tiene alguna data
        chunk = df.iloc[start:start+20, 0:10]
        if not chunk.isna().all().all():
            print(chunk.to_string())

except Exception as e:
    print(f"ERROR: {e}")
