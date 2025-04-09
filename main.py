from typing import Union
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from config.opc import OPCUAClient
from config.ws import ws_manager
from config import db

from services.opcService import ObtenerNodosOpc

from models.ciclo import Ciclo
from models.sensoresIO import SensoresIO
from models.sensoresAA import SensoresAA
from models.sensores import Sensores
from models.equipo import Equipo
from models.receta import Receta

from routers import equiposDatos, historicoGraficos

import logging
import asyncio
import socket

from dotenv import load_dotenv
import os

opc_ip = os.getenv("OPC_SERVER_IP")
opc_port = os.getenv("OPC_SERVER_PORT")

ruta_principal = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("uvicorn")

# ESTO ESTA HECHO PARA BORRAR EL ARCHIVO historial_cocinas.json
archivo_historial = "historial_cocinas.json"
if os.path.exists(archivo_historial):
    os.remove(archivo_historial)
    logger.info(f"Archivo {archivo_historial} eliminado al iniciar la aplicación.")

URL = f"opc.tcp://{opc_ip}:{opc_port}"
opc_client = OPCUAClient(URL)

#db.Base.metadata.drop_all(bind=db.engine)
db.Base.metadata.create_all(bind=db.engine)

dGeneral = ObtenerNodosOpc(opc_client)

ruta_sql_sensores = os.path.join(ruta_principal, 'query', 'insert_sensores.sql')
ruta_sql_recetas = os.path.join(ruta_principal, 'query', 'insert_recetas.sql')

def cargar_archivo_sql(file_path: str):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding="utf-8") as file:
                sql_cript_alarma = file.read()
            
            with db.engine.connect() as conn:
                conn.execute(text(sql_cript_alarma))  
                conn.commit()
                logger.info(f"Archivo SQL ejecutado correctamente desde {file_path}")
        else:
            logger.error(f"El archivo {file_path} no existe.")
    except Exception as e:
        logger.error(f"Error al cargar el archivo SQL: {e}")

async def central_opc_render():
    while True:
        try:
            data = {
                #"cocinas": dGeneral.buscarCocinas(),
                #"enfriadores": dGeneral.buscarEnfriadores(),
                #"datos": dGeneral.respuestaDatos(),
                "graficoscocinas": dGeneral.graficoCocinas(),
                "datosGenerales": dGeneral.datosGenerales(),
                "actualizarRecetas": await  dGeneral.actualizarRecetas(),
            }

            #await ws_manager.send_message("datos-cocinas", data["cocinas"])
            #await ws_manager.send_message("datos-enfriadores", data["enfriadores"])
            #await ws_manager.send_message("datos", data["datos"])
            await ws_manager.send_message("graficos-cocinas", data["graficoscocinas"])
            await ws_manager.send_message("datos-generales", data["datosGenerales"])
            await ws_manager.send_message("datos-recetas", data["actualizarRecetas"])

            await asyncio.sleep(10.0)
        except Exception as e:
            logger.error(f"Error en el lector del OPC: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    session = db.SessionLocal()
    try:
        opc_client.connect()
        logger.info("Conectado al servidor OPC UA.")
        asyncio.create_task(central_opc_render())

        if session.query(Sensores).count() == 0:
            logger.info(f"Cargar registros BDD [Sensores]")
            cargar_archivo_sql(ruta_sql_sensores)
            cargar_archivo_sql(ruta_sql_recetas)
        yield
    finally:
        opc_client.disconnect()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las solicitudes de cualquier dominio
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

app.include_router(historicoGraficos.RoutersGraficosH)


@app.websocket("/ws/{id}")
async def resumen_desmoldeo(websocket: WebSocket, id: str):
    await websocket.accept()
    await ws_manager.connect(id, websocket)
    try:
        while True:
            await websocket.receive_json()
            await ws_manager.send_message(id, "data")
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        await ws_manager.disconnect(id, websocket)

app.include_router(graficosHistorico.RoutersGraficosH)

@app.get("/")
def read_root():
        return {"nodo id": 2, "value": "Hola Mundo- Levanto el server!!!!!!!!!"}