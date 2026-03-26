import pandas as pd
import io

file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
try:
    print(f"Reading full sheet 'CAJA' from: {file_path}")
    df = pd.read_excel(file_path, sheet_name='CAJA', header=None, engine='openpyxl')
    
    # Buscar el inicio de EGRESOS
    print("Searching for 'EGRESOS' text...")
    for i, row in df.iterrows():
        line = " ".join([str(v) for v in row if pd.notna(v)])
        if 'EGRESOS' in line.upper() and i > 20: 
            print(f"POSSIBLE EGRESOS START at row {i}: {line}")
            print(df.iloc[i:i+30, 0:8].to_string())
            break
            
except Exception as e:
    print(f"ERROR: {e}")
