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
    print(f"El servidor de Dexcom ha bloqueado la conexión (Error 504). Reintentando en el próximo ciclo.")
    exit(0)

try:
    # Comprobar la última fecha guardada en el CSV si existe
    ultima_fecha_guardada = None
    filas_existentes = []

    if os.path.exists(archivo_csv):
        with open(archivo_csv, mode='r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            filas_existentes = reader
            for fila in reversed(reader):
                if len(fila) >= 2 and fila[1] != "Fecha_Hora":
                    try:
                        ultima_fecha_guardada = datetime.fromisoformat(fila[1])
                        break
                    except ValueError:
                        continue

    # Si el archivo no existe, creamos la cabecera
    if not os.path.exists(archivo_csv) or len(filas_existentes) == 0:
        print("Archivo CSV no encontrado. Creando e iniciando con las últimas 24 horas...")
        lecturas = dexcom.get_glucose_readings()
        lecturas.sort(key=lambda x: x.datetime) # Ordenar cronológicamente
        
        with open(archivo_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Origen", "Fecha_Hora", "Glucosa_mgdL", "Tendencia"])
            for l in lecturas:
                writer.writerow(["Historial_24h", l.datetime.isoformat(), l.value, l.trend_description])
        print("Archivo inicial creado con éxito.")
    else:
        # AQUÍ ESTÁ LA MAGIA: En vez de pedir la actual, pedimos el historial reciente entero
        lecturas = dexcom.get_glucose_readings()
        nuevas_lecturas = []
        
        # Filtramos solo las que sean más nuevas que la última que tenemos guardada
        for l in lecturas:
            if ultima_fecha_guardada is None or l.datetime.replace(tzinfo=None) > ultima_fecha_guardada.replace(tzinfo=None):
                nuevas_lecturas.append(l)
        
        if nuevas_lecturas:
            # Las ordenamos de más antigua a más nueva para que el CSV quede perfecto
            nuevas_lecturas.sort(key=lambda x: x.datetime)
            
            with open(archivo_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for l in nuevas_lecturas:
                    writer.writerow(["Directo_GitHub", l.datetime.isoformat(), l.value, l.trend_description])
            print(f"¡Rescate exitoso! Se han recuperado y guardado {len(nuevas_lecturas)} lecturas nuevas.")
        else:
            print("No hay lecturas nuevas en Dexcom por ahora.")
except Exception as e:
    print(f"Error al obtener los datos. Se reintentará luego.")
    exit(0)
