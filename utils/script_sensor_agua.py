from datetime import datetime, timedelta
import random

# Parámetros generales
id_sensor = 5
id_ciclo = 1
inicio_ciclo = datetime.now().replace(hour=11, minute=19, second=0, microsecond=0)
minutos_totales = 3 * 60  # 3 horas

# Abrimos archivo de salida
with open("datos_sensor_torres.sql", "w") as file:
    file.write("INSERT INTO sensoresaa (idSensor, valor, idCiclo, fechaRegistro) VALUES\n")

    valores = []
    for i in range(minutos_totales):
        tiempo = inicio_ciclo + timedelta(minutes=i)

        if i < 60:
            # Hora 1: oscilación entre 1550 y 1650
            valor = random.randint(1550, 1650)
        elif i < 120:
            # Hora 2: incremento progresivo por inserción de torres
            if i < 65:
                # Torre 1 insertada (0 a 5 min): 1550 → 1700
                valor = 1550 + int((i - 60) * (150 / 5))
            elif i < 70:
                # Torre 2 insertada (5 a 10 min): 1700 → 1800
                valor = 1700 + int((i - 65) * (100 / 5))
            elif i < 75:
                # Torre 3 insertada (10 a 15 min): 1800 → 1950
                valor = 1800 + int((i - 70) * (150 / 5))
            else:
                # Estabilización entre 1950 y 1950+30
                valor = random.randint(1950, 1980)
        else:
            # Hora 3: oscilación entre 1950 y 2050
            valor = random.randint(1950, 2050)

        fecha_str = tiempo.strftime('%Y-%m-%d %H:%M:%S')
        valores.append(f"({id_sensor}, {valor}, {id_ciclo}, '{fecha_str}')")

    file.write(",\n".join(valores) + ";\n")

print("Archivo 'datos_sensor_torres.sql' generado correctamente.")
