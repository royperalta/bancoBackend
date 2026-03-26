import pandas as pd
import datetime
from fastapi import UploadFile
import io
import math

class ImportadorService:
    @staticmethod
    async def importar_excel_du(unica_id: str, anio: int, file: UploadFile):
        from repositories.base_repo import socio_repo, accion_repo, config_repo, caja_repo
        
        contents = await file.read()
        
        # 1. PROCESAR PESTAÑA D.U. (SOCIOS Y ACCIONES)
        try:
            df_du = pd.read_excel(io.BytesIO(contents), sheet_name='D.U.', header=None, engine='openpyxl')
        except Exception as e:
            raise Exception(f"No se pudo leer la pestaña 'D.U.'. Detalle: {str(e)}")
            
        config = await config_repo.get_one({"unica_id": unica_id})
        mes_inicio_ciclo = config.get("mes_inicio_ciclo", 1) if config else 1
        
        socios_importados = 0
        acciones_importadas = 0
        movimientos_caja = 0

        fila_inicio = -1
        for i in range(25, 45):
            if i >= len(df_du): break
            val_col_1 = str(df_du.iloc[i, 1]).strip() if pd.notna(df_du.iloc[i, 1]) else ""
            if val_col_1 == 'SOCIOS':
                fila_inicio = i + 1
                break
                
        if fila_inicio == -1:
            raise Exception("No se encontró la cabecera 'SOCIOS' en la pestaña D.U.")

        def clean_val(v):
            if pd.isna(v): return 0
            try:
                return float(v)
            except:
                return 0

        for i in range(fila_inicio, len(df_du), 2):
            nro = df_du.iloc[i, 0]
            nombre_completo = df_du.iloc[i, 1]
            
            if pd.isna(nombre_completo) or str(nombre_completo).strip() == "" or str(nombre_completo).strip() == "nan":
                if i + 2 < len(df_du) and pd.notna(df_du.iloc[i+2, 1]): continue
                else: break
                    
            nombres = str(nombre_completo).strip()
            dni_val = str(nro) if pd.notna(nro) else "X"
            dni_fake = f"IMP-{dni_val}-{nombres[:3].upper().replace(' ', '')}"
            
            socio_existente = await socio_repo.get_one({"unica_id": unica_id, "nombres": nombres})
            
            if not socio_existente:
                socio_data = {
                    "unica_id": unica_id,
                    "nombres": nombres,
                    "apellidos": "",
                    "dni": dni_fake,
                    "sexo": "N/A",
                    "fecha_nacimiento": "2000-01-01",
                    "estado": "Activo",
                    "fecha_ingreso": datetime.datetime.now()
                }
                socio_creado = await socio_repo.create(socio_data)
                socio_id_str = socio_creado["_id"]
                socios_importados += 1
            else:
                socio_id_str = str(socio_existente["_id"])
                
            fecha_ciclo_base = datetime.datetime(anio, mes_inicio_ciclo, 1)
            
            # Mes 0
            cant0 = clean_val(df_du.iloc[i, 3])
            if cant0 > 0:
                fecha0 = fecha_ciclo_base - datetime.timedelta(days=1)
                await accion_repo.create({
                    "unica_id": unica_id,
                    "socio_id": socio_id_str,
                    "cantidad": int(cant0),
                    "valor_unitario": 20.0,
                    "tipo": "COMPRA",
                    "fecha": fecha0,
                    "motivo": "Saldo Inicial (Importado)",
                    "estado": "ACTIVO"
                })
                acciones_importadas += int(cant0)

            # Meses del ciclo
            for m_offset in range(12): 
                col_idx = 4 + m_offset
                if col_idx >= df_du.shape[1]: break
                val_celda = df_du.iloc[i, col_idx]
                cant = clean_val(val_celda)
                if cant > 0:
                    mes_relativo = mes_inicio_ciclo + m_offset
                    mes_actual = ((mes_relativo - 1) % 12) + 1
                    anio_actual = anio + ((mes_relativo - 1) // 12)
                    fecha_compra = datetime.datetime(anio_actual, mes_actual, 7)
                    await accion_repo.create({
                        "unica_id": unica_id,
                        "socio_id": socio_id_str,
                        "cantidad": int(cant),
                        "valor_unitario": 20.0,
                        "tipo": "COMPRA",
                        "fecha": fecha_compra,
                        "motivo": f"Compra Mes {m_offset+1} (Importado)",
                        "estado": "ACTIVO"
                    })
                    acciones_importadas += int(cant)

        # 2. PROCESAR PESTAÑA PRESTAMOS
        prestamos_importados = 0
        try:
            df_p = pd.read_excel(io.BytesIO(contents), sheet_name='PRESTAMOS', header=None, engine='openpyxl')
            
            # Buscar cabecera de socios y fechas
            fila_fechas = -1
            fila_inicio_p = -1
            for i in range(2, 10):
                if "MES 0" in str(df_p.iloc[i, 2]).upper():
                    fila_fechas = i
                    fila_inicio_p = i + 1
                    break
            
            if fila_fechas != -1:
                from services.prestamo_service import PrestamoService
                from repositories.base_repo import prestamo_repo
                
                # Mapeo de columnas de fechas desde Col 3
                for i in range(fila_inicio_p, len(df_p)):
                    nombre_p = str(df_p.iloc[i, 1]).strip()
                    if nombre_p == "" or nombre_p == "nan" or "TOTAL" in nombre_p.upper(): break
                    
                    socio_p = await socio_repo.get_one({"unica_id": unica_id, "nombres": nombre_p})
                    if not socio_p: continue
                    socio_id_p = str(socio_p["_id"])
                    
                    # Saldo Inicial (Mes 0) en Columna 3 (según mi inspección deep anterior, las fechas empiezan en col 3)
                    # No, en debug_prestamos_deep: 
                    # Index 2: "MES 0" label
                    # Index 3: 2025-06-07 (Date)
                    # Zoila Row 5: Index 3 is 0, Index 7 is 500.
                    # Alicia Row 6: Index 5 is 9500.
                    
                    # Recorrer columnas desde la 3 en adelante
                    for col_idx in range(3, df_p.shape[1]):
                        val_m = clean_val(df_p.iloc[i, col_idx])
                        if val_m == 0: continue
                        
                        # Si es positivo: Nuevo Préstamo
                        if val_m > 0:
                            # 12 meses por defecto para importaciones masivas
                            await PrestamoService.crear_prestamo(socio_id_p, unica_id, val_m, 12, bypasar_liquidez=True)
                            prestamos_importados += 1
                        else:
                            # Si es negativo: Pago de Capital
                            monto_pago = abs(val_m)
                            p_activos = await prestamo_repo.get_all({"socio_id": socio_id_p, "estado": "ACTIVO"})
                            if p_activos:
                                # Aplicamos al préstamo que tenga saldo
                                p_id = str(p_activos[0]["_id"])
                                await PrestamoService.registrar_pago(p_id, 1, monto_pago)
        except Exception as e:
            print(f"Advertencia: No se pudo procesar la pestaña PRESTAMOS: {str(e)}")

        return {
            "status": "success",
            "message": f"Excel importado correctamente",
            "socios_creados": socios_importados,
            "acciones_compradas": acciones_importadas,
            "prestamos_creados": prestamos_importados,
            "movimientos_caja": movimientos_caja
        }
