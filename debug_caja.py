import pandas as pd
import io

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading sheet 'CAJA' from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='CAJA', header=None, nrows=100, engine='openpyxl')
    print("Columns:", df.shape[1])
    
    # Mostrar las primeras 50 filas de las columnas relevantes para entender la estructura de ingresos/egresos
    print(df.iloc[0:50, 0:8].to_string())
except Exception as e:
    print(f"ERROR: {e}")
