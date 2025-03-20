from opcua import Client
import logging

logger = logging.getLogger("uvicorn")
class ObtenerNodosOpc:
    def __init__(self, conexion_servidor):
        self.conexion_servidor = conexion_servidor