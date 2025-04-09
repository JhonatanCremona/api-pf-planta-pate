from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, date

from models.ciclo import Ciclo
from models.equipo import Equipo
from models.sensores import Sensores

from services.historico import obtener_datos_graficos

from config import db

#http://localhost/historico/<equipo>/<fecha_inicio>/<fecha_fin> 

RoutersGraficosH = APIRouter(prefix="/historico", tags=["Graficos Historico"]) 

@RoutersGraficosH.get("/{equipo}")
def obtener_lista_ciclos(
    equipo: str, 
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD HH:MM:SS)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    db : Session = Depends(db.get_db)):

    lista_ciclos = []

    equipo_actual = (
        db.query(Equipo)
        .filter(Equipo.nombre == equipo)
        .first()
    )
    if not equipo_actual:
        return {"error": "Equipo no encontrado"}

    ciclos = (
        db.query(Ciclo)
        .filter(
            Ciclo.idEquipo == equipo_actual.id,
            Ciclo.fechaFin.between(fecha_inicio, fecha_fin))
        .all()
        )

    if not fecha_inicio:
        raise HTTPException(status_code=400 , detail="Debe especificar una fecha de inicio.")
    if not fecha_fin:
        raise HTTPException(status_code=400, detail="Debe especificar una fecha de fin.")
    if not ciclos:
        raise HTTPException(status_code=500, detail="No se encontraron datos de ciclo en la BDD")

    for elem in ciclos:
        ciclo = {}
        if elem.estado == "Finalizado":
            ciclo["id_ciclo"] = elem.id
            ciclo["lote"] = elem.lote
            ciclo["fecha_inicio"] = elem.fechaInicio
            ciclo["fecha_fin"] = elem.fechaFin
            ciclo["tiempo_transcurrido"] = elem.tiempoTranscurrido
            lista_ciclos.append(ciclo)

    return lista_ciclos


@RoutersGraficosH.get("/{equipo}/{id_ciclo}")
def obtener_datos_sensores(
    equipo: str, 
    id_ciclo: int, 
    db : Session = Depends(db.get_db)
):
    return obtener_datos_graficos(db, id_ciclo)