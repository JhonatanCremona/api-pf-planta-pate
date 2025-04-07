from opcua import Client
import logging
import time

logger = logging.getLogger("uvicorn")

class OPCUAClient:
    def __init__(self, server_url, max_retries=5, retry_delay=10):
        self.server_url = server_url
        self.client = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.client = Client(self.server_url)
                self.client.connect()
                logger.info("✅ Conectado al servidor OPC UA.")
                return True
            except Exception as e:
                retries += 1
                logger.error(f"🔄 Error al conectar al servidor OPC UA. Intento {retries}/{self.max_retries}: {e}")
                time.sleep(self.retry_delay)

        logger.warning("⚠️ No se pudo conectar al servidor después de varios intentos.")
        return False  # Retorna False si no pudo conectar

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            logger.warning("⚠️ Conexión cerrada.")
            self.client = None

    def is_connected(self):
        return self.client is not None  # Retorna True si el cliente está conectado

    def read_node(self, node_id):
        if not self.is_connected():
            raise Exception("Cliente OPC no conectado.")
        try:
            node = self.client.get_node(node_id)
            return node.get_value()
        except Exception as e:
            logger.error(f"⚠️ Error al leer el nodo {node_id}: {e}")
            return None  # Devuelve None si falla la lectura

    def get_objects_node(self):
        if not self.is_connected():
            raise Exception("Cliente OPC no conectado.")
        return self.client.get_objects_node()

    def get_root_node(self):
        if not self.is_connected():
            raise Exception("Cliente OPC no conectado.")
        return self.client.get_root_node()