import pandas as pd
file_path = r'c:\Users\Roy\Documents\Desarrollo\banco2\UNICA MANOS A LA OBRA 2025- 20256).xlsx'
df = pd.read_excel(file_path, sheet_name='D.U.', header=None)
# Ver fila 33 (index 32)
row_headers = df.iloc[32, :]
for i, val in enumerate(row_headers):
    print(f"Index {i}: {val} (type: {type(val)})")
