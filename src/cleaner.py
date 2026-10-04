


import csv
import json
from datetime import datetime


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# Una fila es inválida si falta order_id, si amount no es un número o es negativo, o si updated_at no es una fecha válida. Las inválidas van a una lista de cuarentena con el motivo.



def validate_row(row):
    if not (row.get("order_id") or "").strip():
        return "order_id vacío"

    try:
        amount = float(row.get("amount"))
    except (ValueError, TypeError):
        return "amount no es numero"

    if amount < 0:
        return "amount negativo"

    try:
        datetime.fromisoformat(row.get("updated_at"))
    except (ValueError, TypeError):
        return "updated_at no es una fecha válida"

    return None

# Una fila es inválida si falta order_id, si amount no es un número o es negativo, o si updated_at no es una fecha válida. Las inválidas van a una lista de cuarentena con el motivo.


def split_valid_invalid(rows):
    valid,querantine = [],[]
    for row in rows:
        reason=validate_row(row)
        if reason:
            querantine.append({**row,"reason":reason})
        else:
            valid.append({**row, "amount":float(row["amount"]),"updated_at":datetime.fromisoformat(row["updated_at"])})
    return valid, querantine

# Devuelve tres cosas: filas válidas, cuarentena y un resumen con el total de amount por marketplace y la cantidad de órdenes por status.


# Por cada order_id, conserva solo la fila con updated_at más reciente. Si hay empate, gana la última del archivo.

def latest_per_order(rows):
    latest={}
    for row in rows:
        current = latest.get(row["order_id"]) 
        if current is None or row["updated_at"] >= current["updated_at"]:
            latest[row["order_id"]] = row
    return list(latest.values())
           
           
 # Una función aparte, write_report(...), guarda el resumen en JSON.          
# Paso 4: resumen
def summarize(rows):
    total_by_marketplace = {}
    orders_by_status = {}
    for row in rows:
        marketplace = row["marketplace"]
        total_by_marketplace[marketplace] = (
            total_by_marketplace.get(marketplace, 0) + row["amount"]
        )
        status = row["status"]
        orders_by_status[status] = orders_by_status.get(status, 0) + 1
    return {
        "total_by_marketplace": total_by_marketplace,
        "orders_by_status": orders_by_status,
    }
            

    
def clean_orders(path):
   
    rows = read_rows(path)
    valid, quarantine = split_valid_invalid(rows)
    deduped = latest_per_order(valid)

    return deduped, quarantine, summarize(deduped)


# Paso 6: guardar el resumen como JSON
def write_report(summary, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
 
 
if __name__ == "__main__":
    valid, quarantine, summary = clean_orders("orders.csv")
    print("Válidas:", [(r["order_id"], r["status"]) for r in valid])
    print("Cuarentena:", [(r["order_id"] or "(vacío)", r["reason"]) for r in quarantine])
    print("Resumen:", summary)
    write_report(summary, "report.json")
 