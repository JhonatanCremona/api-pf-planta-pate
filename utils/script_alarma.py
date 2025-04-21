from datetime import datetime, timedelta
import random

# Generador de alarmas de prueba
tipos_alarma = ["informe", "seguridad"]
estados_equipo = ["ACTIVO", "INACTIVO"]
recetas = ["Jamon tipo 1", "Jamon tipo 2"]
ciclo_estados = ["Pre Calentamiento", "Operativo", "Finalizado", "Pausa", "Cancelado"]

def generar_alarmas_sql(n=50):
    sql_lines = ["-- Inserción de datos de prueba para la tabla alarma"]
    for i in range(1, n+1):
        tipo = random.choice(tipos_alarma)
        estado = random.choice(ciclo_estados)
        receta = random.choice(recetas)
        equipo = random.choice(estados_equipo)
        peso = random.choice([450, 500, 550])
        tiempo = random.randint(180, 360)
        temp_agua = round(random.uniform(24, 90), 1)
        temp_producto = round(random.uniform(48, 78), 1)
        descripcion = f"Alarma de tipo {tipo.upper()} - Estado del ciclo: {estado}, Receta: {receta}, Temp Agua: {temp_agua}°C, Temp Producto: {temp_producto}°C, Peso: {peso}kg, Tiempo: {tiempo}min, Equipo: {equipo}"
        fecha = datetime.now() - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 1440))
        fecha_str = fecha.strftime('%Y-%m-%d %H:%M:%S')
        sql_lines.append(
            f"INSERT INTO alarma (id, tipoAlarma, descripcion, fechaRegistro) VALUES ({i}, '{tipo}', '{descripcion}', '{fecha_str}');"
        )
    return "\n".join(sql_lines)

# Generar el contenido SQL
sql_content = generar_alarmas_sql()

# Guardar en archivo
file_path = "/mnt/data/insert_alarmas.sql"
with open(file_path, "w") as f:
    f.write(sql_content)

file_path
