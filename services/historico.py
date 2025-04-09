from datetime import date, datetime
from collections import defaultdict

from models.ciclo import Ciclo
from models.sensoresAA import SensoresAA
from models.sensores import Sensores
from models.estadoCiclo import EstadoCiclo

import logging

logger = logging.getLogger("uvicorn")

def obtener_datos_graficos(db, id_ciclo:int):
    lista_sensores_data = {}
    ciclo = db.query(Ciclo).filter(Ciclo.id == id_ciclo).first()

    if not ciclo:
        logger.info(f"No se encontro el ciclo en la BDD")

    lista_sensores = (
        db.query(Sensores)
    ).all()

    estado_ciclo = (
        db.query(EstadoCiclo)
        .filter(EstadoCiclo.idCiclo == ciclo.id)
    )

    lista_sensores_data["Id_ciclo"] = ciclo.id

    for sensor in lista_sensores:
        if sensor.nombre == "Temperatura agua":
            temp_agua = (
                db.query(SensoresAA)
                .filter(SensoresAA.idSensor == sensor.id)
                .filter(SensoresAA.idCiclo == ciclo.id)
                .all()
            )
            lista_sensores_data[sensor.nombre] = temp_agua
        
        if sensor.nombre == "Temperatura producto":
            temp_producto = (
                db.query(SensoresAA)
                .filter(SensoresAA.idSensor == sensor.id)
                .filter(SensoresAA.idCiclo == ciclo.id)
                .all()
            )
            lista_sensores_data[sensor.nombre] = temp_producto
        if sensor.nombre == "Nivel agua":
            nivel_agua = (
                db.query(SensoresAA)
                .filter(SensoresAA.idSensor == sensor.id)
                .filter(SensoresAA.idCiclo == ciclo.id)
                .all()
            )
            lista_sensores_data[sensor.nombre] = nivel_agua
    print(f"Datos de la lista: {lista_sensores_data}")

    return lista_sensores_data

def generar_informe_ciclo(db, id_ciclo:int):
    ciclo = (db.query(Ciclo)
             .filter(Ciclo.id == id_ciclo)
             .first()
             )
    if not ciclo:
        logger(f"No se encontro el ciclo en la BDD")

    lista_sensores = (
        db.query(Sensores)
    ).all()

    estado_ciclo = (
        db.query(EstadoCiclo)
        .filter(EstadoCiclo.idCiclo == ciclo.id)
    )

    for sensor in lista_sensores:
        if sensor.nombre == "Temperatura agua":
            temp_agua = (
                db.query(SensoresAA)
                .filter(SensoresAA.idSensor == sensor.id)
                .filter(SensoresAA.idCiclo == ciclo.id)
                .all()
            )
        
        if sensor.nombre == "Temperatura producto":
            temp_producto = (
                db.query(SensoresAA)
                .filter(SensoresAA.idSensor == sensor.id)
                .filter(SensoresAA.idCiclo == ciclo.id)
                .all()
            )
        if sensor.nombre == "Nivel agua":
            nivel_agua = (
                db.query(SensoresAA)
                .filter(SensoresAA.idSensor == sensor.id)
                .filter(SensoresAA.idCiclo == ciclo.id)
                .all()
            )

    

    #CONSTRUCCION DEL ARCHIVO XLMS
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Informe de Ciclo de Coccion"
    logoPath = "cremona.png"
    img = Image(logoPath)
    img.width = 280
    img.height = 70
    sheet.add_image(img, 'D1')

    sheet.append(["LISTA PRODUCTOS"])
    producto_cell = sheet.cell(row=sheet.max_row, column=1)
    producto_cell.font = Font(bold= True, size=20)

    headers = [
        "ID_CICLO", "EQUIPO", "LOTE", "ESTADO CICLO", "NOMBRE RECETA",
        "TEMPERARURA AGUA  [°C]", "TEMPERATURA PRODUCTO [°C]", "NIVEL AGUA [mm]", "FECHA REGISTRO"
    ]
    header_fill = PatternFill(start_color="145f82", end_color="145f82", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)  

    for col in range(1, len(headers) + 1):
        cell = sheet.cell(row=sheet.max_row, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    
    start_row = sheet.max_row + 1

    resultado_fila = []

