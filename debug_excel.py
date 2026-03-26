import pandas as pd
import io

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading file: {file_path}")
    # Usar el motor openpyxl explícitamente y leer solo las primeras 100 filas
    df = pd.read_excel(file_path, sheet_name='D.U.', header=None, nrows=100, engine='openpyxl')
    print("Columns:", df.shape[1])
    print("Rows:", df.shape[0])
    
    # Buscar la cabecera SOCIOS
    for i, row in df.iterrows():
        # Ver si el valor en la columna B (index 1) es SOCIOS
        val = str(row[1]).strip() if pd.notna(row[1]) else ""
        if val == 'SOCIOS':
            print(f"FOUND SOCIOS at row {i}")
            # Mostrar las siguientes 5 filas de las primeras 10 columnas
            print(df.iloc[i:i+6, 0:10].to_string())
            break
except Exception as e:
    print(f"ERROR: {e}")
