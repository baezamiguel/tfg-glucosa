import os
import csv
from datetime import datetime
from pydexcom import Dexcom

# Leer credenciales guardadas en los Secrets de GitHub
username = os.getenv("DEXCOM_USER")
password = os.getenv("DEXCOM_PASS")
archivo_csv = "historial_y_directo.csv"

if not username or not password:
    print("Error: No se encontraron las credenciales en los Secrets de GitHub.")
    exit(1)

print("Conectando a Dexcom (Servidor Europeo)...")
try:
    dexcom = Dexcom(username=username, password=password, region="ous")
except Exception as e:
    print(f"Error al conectar con Dexcom: {e}")
    exit(1)

# Comprobar la última fecha guardada en el CSV si existe
ultima_fecha_guardada = None
filas_existentes = []

if os.path.exists(archivo_csv):
    with open(archivo_csv, mode='r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        filas_existentes = reader
        for fila in reversed(reader):
            if len(fila) >= 2:
                try:
                    ultima_fecha_guardada = datetime.fromisoformat(fila[1])
                    break
                except ValueError:
                    continue

# Si el archivo no existe, creamos la cabecera e intentamos descargar 24h
if not os.path.exists(archivo_csv) or len(filas_existentes) == 0:
    print("Archivo CSV no encontrado. Creando e iniciando con las últimas 24 horas...")
    lecturas_iniciales = dexcom.get_glucose_readings()
    with open(archivo_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Origen", "Fecha_Hora", "Glucosa_mgdL", "Tendencia"])
        for l in lecturas_iniciales:
            writer.writerow(["Historial_24h", l.datetime.isoformat(), l.value, l.trend_description])
    print("Archivo inicial creado con éxito.")
else:
    # Si ya existe, descargamos la lectura más reciente
    lectura_reciente = dexcom.get_current_glucose_reading()
    if lectura_reciente:
        fecha_nueva = lectura_reciente.datetime.isoformat()
        
        if ultima_fecha_guardada is None or lectura_reciente.datetime.replace(tzinfo=None) > ultima_fecha_guardada.replace(tzinfo=None):
            with open(archivo_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Directo_GitHub", fecha_nueva, lectura_reciente.value, lectura_reciente.trend_description])
            print(f"Nueva lectura guardada: {fecha_nueva} - {lectura_reciente.value} mg/dL")
        else:
            print("No hay lecturas nuevas en Dexcom por ahora.")
    else:
        print("No se pudo obtener la lectura actual.")
