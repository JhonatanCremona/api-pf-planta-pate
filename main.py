from typing import Union
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
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

from routers import equiposDatos

import logging
import asyncio
import socket

from dotenv import load_dotenv
import os

opc_ip = os.getenv("OPC_SERVER_IP")
opc_port = os.getenv("OPC_SERVER_PORT")

logger = logging.getLogger("uvicorn")

# ESTO ESTA HECHO PARA BORRAR EL ARCHIVO historial_cocinas.json
archivo_historial = "historial_cocinas.json"
if os.path.exists(archivo_historial):
    os.remove(archivo_historial)
    logger.info(f"Archivo {archivo_historial} eliminado al iniciar la aplicación.")

URL = f"opc.tcp://{opc_ip}:{opc_port}"
opc_client = OPCUAClient(URL)

db.Base.metadata.drop_all(bind=db.engine)
db.Base.metadata.create_all(bind=db.engine)

dGeneral = ObtenerNodosOpc(opc_client)

async def central_opc_render():
    while True:
        try:
            data = {
                "cocinas": dGeneral.buscarCocinas(),
                "enfriadores": dGeneral.buscarEnfriadores(),
                "home": dGeneral.datosEquiposHome(),
                "graficoscocinas": dGeneral.graficoCocinas(),
            }

            await ws_manager.send_message("datos-cocinas", data["cocinas"])
            await ws_manager.send_message("datos-enfriadores", data["enfriadores"])
            await ws_manager.send_message("datos-home", data["home"])
            await ws_manager.send_message("graficos-cocinas", data["graficoscocinas"])

            await asyncio.sleep(10.0)
        except Exception as e:
            logger.error(f"Error en el lector del OPC: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        opc_client.connect()
        logger.info("Conectado al servidor OPC UA.")
        asyncio.create_task(central_opc_render())
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

@app.get("/")
def read_root():
        return {"nodo id": 2, "value": "Hola Mundo- Levanto el server!!!!!!!!!"}