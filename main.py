from typing import Union
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from config.opc import OPCUAClient
from config.ws import ws_manager
from services.opcService import ObtenerNodosOpc

import logging
import asyncio
import socket

from dotenv import load_dotenv
import os

opc_ip = os.getenv("OPC_SERVER_IP")
opc_port = os.getenv("OPC_SERVER_PORT")

logger = logging.getLogger("uvicorn")

URL = f"opc.tcp://{opc_ip}:{opc_port}"
opc_client = OPCUAClient(URL)



async def central_opc_render():
    listaDatosOpc = ObtenerNodosOpc(opc_client)
    while True:
        try:
            data = {
                "configuraciones": listaDatosOpc.leer_lista_recetario(10),
            }

            await ws_manager.send_message("", data["configuraciones"])

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
            await websocket.receive_json()  # Aquí puedes hacer validaciones si e
            await ws_manager.send_message(id, "data")
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        await ws_manager.disconnect(id, websocket)

@app.get("/")
def read_root():
        return {"nodo id": 2, "value": "Hola Mundo- Levanto el server!!!!!!!!!"}