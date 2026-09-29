import csv
import os
import requests
from datetime import datetime, timezone

NIGHTSCOUT_URL = "https://nightscout-tfg.onrender.com"
API_SECRET = os.environ["NIGHTSCOUT_API_SECRET"]  # el mismo que pusiste en Render
CSV_PATH = "historial_nightscout.csv"

def obtener_ultima_fecha_guardada():
    if not os.path.exists(CSV_PATH):
        return None
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        filas = list(csv.reader(f))
        for fila in reversed(filas):
            if len(fila) >= 2 and fila[1] != "Fecha_Hora":
                try:
                    return datetime.fromisoformat(fila[1])
                except ValueError:
                    continue
    return None

ultima_fecha = obtener_ultima_fecha_guardada()

headers = {"api-secret": API_SECRET}
params = {"count": 300}  # trae bastantes por si hay hueco grande que rellenar

resp = requests.get(f"{NIGHTSCOUT_URL}/api/v1/entries.json", headers=headers, params=params)
lecturas = resp.json()  # viene ordenado de más reciente a más antigua

nuevas = []
for l in lecturas:
    fecha = datetime.fromtimestamp(l["date"] / 1000, tz=timezone.utc)
    if ultima_fecha is None or fecha.replace(tzinfo=None) > ultima_fecha.replace(tzinfo=None):
        nuevas.append((fecha.isoformat(), l["sgv"], l.get("direction", "")))

if nuevas:
    nuevas.sort()  # de más antigua a más nueva
    escribir_cabecera = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if escribir_cabecera:
            writer.writerow(["Origen", "Fecha_Hora", "Glucosa_mgdL", "Tendencia"])
        for fecha, valor, tendencia in nuevas:
            writer.writerow(["Nightscout", fecha, valor, tendencia])
    print(f"Guardadas {len(nuevas)} lecturas nuevas.")
else:
    print("Sin lecturas nuevas.")
