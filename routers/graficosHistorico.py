from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from fastapi.responses import StreamingResponse

from services.opcService import datosGraficos
from config import db

import os
import json

from desp import user_dependency

RoutersGraficosH = APIRouter(prefix="/graficos-historico", tags=["Graficos Historico"]) 

@RoutersGraficosH.get("/productos-realizados/")
def red_lista_ciclos_productos(user: user_dependency, 
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"), 
    db : Session = Depends(db.get_db)):

    resupuesta = datosGraficos(db, fecha_inicio, fecha_fin)
    return resupuesta