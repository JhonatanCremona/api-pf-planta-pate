from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, date

from models.ciclo import Ciclo
from models.equipo import Equipo
from models.sensores import Sensores

from services.historicoServices import obtener_datos_graficos, generar_informe_ciclo

from config import db

#http://localhost/historico/<equipo>/<fecha_inicio>/<fecha_fin> 

RoutersGraficosH = APIRouter(prefix="/historico-graficos", tags=["Graficos Historico"]) 

@RoutersGraficosH.get("/{equipo}")
def obtener_lista_ciclos(
    equipo: str, 
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD HH:MM:SS)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    db : Session = Depends(db.get_db)):

    if not fecha_inicio or not fecha_fin:
        return None

    lista_ciclos = []

    try:
        equipo_actual = (
            db.query(Equipo)
            .filter(Equipo.nombre == equipo)
            .first()
        )
        if not equipo_actual:
            return None

        ciclos = (
            db.query(Ciclo)
            .filter(
                Ciclo.idEquipo == equipo_actual.id,
                Ciclo.fecha_fin.between(fecha_inicio, fecha_fin))
            .all()
            )
        
        if not ciclos:
            return None

        for elem in ciclos:
            ciclo = {}
            if elem.estadoMaquina == "FINALIZADO":
                ciclo["id_ciclo"] = elem.id
                ciclo["lote"] = elem.lote
                ciclo["fecha_inicio"] = elem.fecha_inicio
                ciclo["fecha_fin"] = elem.fecha_fin
                ciclo["tiempo_transcurrido"] = elem.tiempoTranscurrido
                lista_ciclos.append(ciclo)

        return lista_ciclos if lista_ciclos else None

    except Exception:
        return None


@RoutersGraficosH.get("/{equipo}/{id_ciclo}")
def obtener_datos_sensores(
    equipo: str, 
    id_ciclo: int, 
    db : Session = Depends(db.get_db)
):
    return obtener_datos_graficos(db, id_ciclo)

@RoutersGraficosH.get("/{equipo}/descargar/{id_ciclo}")
def descargar_archivo_xlms(
    id_ciclo:int, 
    equipo: str,
    db: Session = Depends(db.get_db)
):
    xlms_stream = generar_informe_ciclo(db, id_ciclo, equipo)
    fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nombreArchivo = f"informe_ciclo_{id_ciclo}_{fecha_actual}.xlsx"

    return StreamingResponse(
        xlms_stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": f"attachment; filename={nombreArchivo}"}
    )
