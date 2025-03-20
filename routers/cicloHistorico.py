from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from fastapi.responses import StreamingResponse

from service.cicloService import get_lista_productos, generarDocumentoXLMSGraficos, get_lista_total_ciclos_productos
from config import db
from desp import user_dependency

RoutersGraficosH = APIRouter(prefix="/graficos-historico", tags=["Graficos Historico"]) 