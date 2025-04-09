from datetime import datetime, timedelta

# Configuración inicial
id_ciclo = 1
inicio_ciclo = datetime.now().replace(hour=11, minute=19, second=0, microsecond=0)
duracion_total = timedelta(hours=3)

# Tramos por nombre
tramos = [
    {
        "nombre": "Pre Calentamiento",
        "inicio": inicio_ciclo,
        "fin": inicio_ciclo + timedelta(hours=1)
    },
    {
        "nombre": "Operativo",
        "inicio": inicio_ciclo + timedelta(hours=1),
        "fin": inicio_ciclo + timedelta(hours=3)
    },
    {
        "nombre": "Finalizado",
        "inicio": inicio_ciclo + timedelta(hours=3),
        "fin": inicio_ciclo + timedelta(hours=3, minutes=1)  # solo un minuto de estado final
    }
]

# Generar archivo SQL
with open("estado_ciclo.sql", "w") as file:
    file.write("INSERT INTO estadociclo (id, nombre, fechaInicio, fechaFin, idCiclo) VALUES\n")

    valores = []
    for i, tramo in enumerate(tramos):
        fecha_inicio_str = tramo["inicio"].strftime('%Y-%m-%d %H:%M:%S')
        fecha_fin_str = tramo["fin"].strftime('%Y-%m-%d %H:%M:%S')
        valores.append(f"({i + 1}, '{tramo['nombre']}', '{fecha_inicio_str}', '{fecha_fin_str}', {id_ciclo})")

    file.write(",\n".join(valores) + ";\n")

print("Archivo 'estado_ciclo.sql' generado correctamente.")
