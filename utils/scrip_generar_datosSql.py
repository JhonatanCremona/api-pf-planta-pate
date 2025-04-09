from datetime import datetime, timedelta

# Parámetros del ciclo
id_sensor = 1
id_ciclo = 1
valor_inicio = 80
valor_fin = 90
inicio_ciclo = datetime(2025, 4, 9, 8, 0, 0)
minutos_totales = 3 * 60  # 3 horas

# Calcular incremento por minuto
incremento = (valor_fin - valor_inicio) / minutos_totales

# Abrimos el archivo .sql
with open("datos_sensor.sql", "w") as file:
    file.write("INSERT INTO sensoresaa (idSensor, valor, idCiclo, fechaRegistro) VALUES\n")

    valores = []
    for i in range(minutos_totales):
        tiempo = inicio_ciclo + timedelta(minutes=i)
        valor = round(valor_inicio + incremento * i)
        fecha_str = tiempo.strftime('%Y-%m-%d %H:%M:%S')  # Corrección acá
        valores.append(f"({id_sensor}, {valor}, {id_ciclo}, '{fecha_str}')")

    # Escribir todo junto con comas y cerrar con punto y coma
    file.write(",\n".join(valores) + ";\n")

print("Archivo 'datos_sensor.sql' generado correctamente.")

