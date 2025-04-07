from opcua import Client
import time
import logging
import json
import os

logger = logging.getLogger("uvicorn")
class ObtenerNodosOpc:
    def __init__(self, conexion_servidor):
        self.conexion_servidor = conexion_servidor    

    def buscarCocinas(self):
        listaCocinas = []

        try:
            root_node = self.conexion_servidor.get_root_node().get_child(["0:Objects"]).get_child(["2:ServerInterfaces"])

            interfaces = {
                "2:Server interface_1": ["2:COCINA-1-L1", "2:COCINA-2-L1", "2:COCINA-3-L1"],
                "2:Server interface_2": ["2:COCINA-4-L2", "2:COCINA-5-L2", "2:COCINA-6-L2"]
            }

            for interface, cocinas in interfaces.items():
                try:
                    interface_node = root_node.get_child([interface])
                    for cocina in cocinas:
                        try:
                            cocina_node = interface_node.get_child([cocina])
                            children = cocina_node.get_children()
                            valores = [child.get_value() for child in children]

                            # Construcción de la estructura de salida
                            cocina_data = {
                                "num_cocina": valores[0],
                                "num_receta": valores[1],
                                "nom_receta": valores[2],
                                "estado": valores[3],
                                "cant_torres": valores[4],
                                "tipo_Fin": valores[5],
                                "pasos": [
                                    {
                                        "paso_actual": valores[6],
                                        "tiempo": valores[7],
                                        "temp_Agua": valores[8],
                                        "temp_Prod": valores[9],
                                        "temp_Ing": valores[10],
                                        "niv_Agua": valores[11]
                                    }
                                ],
                                "sector_io": [
                                    {
                                        "filtro_succion_agua": valores[12],
                                        "entrada_agua": valores[13],
                                        "bomba_recirculacion": valores[14],
                                        "vapor_serpentina": valores[15],
                                        "vapor_vivo": valores[16]
                                    }
                                ]
                            }
                            listaCocinas.append(cocina_data)
                        except Exception as e:
                            logger.error(f"Error al obtener datos de {cocina}: {e}")
                except Exception as e:
                    logger.error(f"Error al acceder a {interface}: {e}")

            #print(listaCocinas)

        except Exception as e:
            logger.error(f"Error al buscar nodos: {e}")

        return listaCocinas

    def buscarEnfriadores(self):
        listaEnfriadores = []

        try:
            root_node = self.conexion_servidor.get_root_node().get_child(["0:Objects"]).get_child(["2:ServerInterfaces"])

            interfaces = {
                "2:Server interface_1": ["2:ENFRIADOR-1-L1", "2:ENFRIADOR-2-L1", "2:ENFRIADOR-3-L1", "2:ENFRIADOR-4-L1"],
                "2:Server interface_2": ["2:ENFRIADOR-5-L2", "2:ENFRIADOR-6-L2", "2:ENFRIADOR-7-L2", "2:ENFRIADOR-8-L2"]
            }

            for interface, enfriadores in interfaces.items():
                try:
                    interface_node = root_node.get_child([interface])
                    for enfriador in enfriadores:
                        try:
                            enfriador_node = interface_node.get_child([enfriador])
                            children = enfriador_node.get_children()
                            valores = [child.get_value() for child in children]

                            # Construcción de la estructura de salida
                            enfriador_data = {
                                "num_enfriador": valores[0],
                                "num_receta": valores[1],
                                "nom_receta": valores[2],
                                "estado": valores[3],
                                "cant_torres": valores[4],
                                "tipo_Fin": valores[5],
                                "pasos": [
                                    {
                                        "paso_actual": valores[6],
                                        "tiempo": valores[7],
                                        "temp_Agua": valores[8],
                                        "temp_Prod": valores[9],
                                        "temp_Ing": valores[10],
                                        "niv_Agua": valores[11]
                                    }
                                ],
                                "sector_io": [
                                    {
                                        "filtro_succion_agua": valores[12],
                                        "entrada_agua": valores[13],
                                        "bomba_recirculacion": valores[14],
                                        "valvula_amoniaco": valores[15],
                                    }
                                ]
                            }
                            listaEnfriadores.append(enfriador_data)
                        except Exception as e:
                            logger.error(f"Error al obtener datos de {enfriador}: {e}")
                except Exception as e:
                    logger.error(f"Error al acceder a {interface}: {e}")

            #print(listaEnfriadores)

        except Exception as e:
            logger.error(f"Error al buscar nodos: {e}")

        return listaEnfriadores

    def datosEquiposHome(self):
        listaCocinas = []

        try:
            root_node = self.conexion_servidor.get_root_node().get_child(["0:Objects"]).get_child(["2:ServerInterfaces"])

            interfaces = {
                "2:Server interface_1": ["2:COCINA-1-L1", "2:COCINA-2-L1", "2:COCINA-3-L1", "2:ENFRIADOR-1-L1", "2:ENFRIADOR-2-L1", "2:ENFRIADOR-3-L1", "2:ENFRIADOR-4-L1"],
                "2:Server interface_2": ["2:COCINA-4-L2", "2:COCINA-5-L2", "2:COCINA-6-L2", "2:ENFRIADOR-5-L2", "2:ENFRIADOR-6-L2", "2:ENFRIADOR-7-L2", "2:ENFRIADOR-8-L2"]
            }

            for index, (interface, cocinas) in enumerate(interfaces.items(), 1):
                cocina_info = {"id": index, "equipos": []}

                try:
                    interface_node = root_node.get_child([interface])
                    for cocina in cocinas:
                        try:
                            cocina_node = interface_node.get_child([cocina])
                            children = cocina_node.get_children()
                            valores = [child.get_value() for child in children]

                            if "COCINA" in cocina:
                                equipo_data = {
                                    "tipo": "COCINA",
                                    "id": valores[0],
                                    "estado": valores[3],
                                    "tempAguaActual": valores[7],
                                    "tempProductoActual": valores[8],
                                    "receta": valores[2],
                                    "tiempoTranscurrido": valores[6]
                                }
                            elif "ENFRIADOR" in cocina:
                                equipo_data = {
                                    "tipo": "ENFRIADOR",
                                    "id": valores[0],
                                    "estado": valores[3],
                                    "tempAguaActual": valores[8],
                                    "tempProductoActual": valores[9],
                                    "receta": valores[2],
                                    "tiempoTranscurrido": valores[7]
                                }

                            cocina_info["equipos"].append(equipo_data)

                        except Exception as e:
                            logger.error(f"Error al obtener datos de {cocina}: {e}")

                except Exception as e:
                    logger.error(f"Error al acceder a {interface}: {e}")

                listaCocinas.append(cocina_info)

            resultado = {"lineas": listaCocinas}

            #print(resultado)

        except Exception as e:
            logger.error(f"Error al buscar nodos: {e}")

        return resultado 

    def graficoCocinas(self):
        if not hasattr(self, "verificacion_inicial_realizada"):
            self.verificacion_inicial_realizada = False  # Inicialmente, no se ha hecho la verificación

        archivos_cocinas = {
            "2:COCINA-1-L1": "cocina1.json",
            "2:COCINA-2-L1": "cocina2.json",
            "2:COCINA-3-L1": "cocina3.json",
            "2:COCINA-4-L2": "cocina4.json",
            "2:COCINA-5-L2": "cocina5.json",
            "2:COCINA-6-L2": "cocina6.json",
            "2:ENFRIADOR-1-L1": "enfriador1.json",
            "2:ENFRIADOR-2-L1": "enfriador2.json",
            "2:ENFRIADOR-3-L1": "enfriador3.json",
            "2:ENFRIADOR-4-L1": "enfriador4.json",
            "2:ENFRIADOR-5-L2": "enfriador5.json",
            "2:ENFRIADOR-6-L2": "enfriador6.json",
            "2:ENFRIADOR-7-L2": "enfriador7.json",
            "2:ENFRIADOR-8-L2": "enfriador8.json"
        }

        cocinas_data = {}

        # Cargar datos previos si existen
        for cocina, archivo in archivos_cocinas.items():
            if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
                with open(archivo, "r") as file:
                    try:
                        cocinas_data[cocina] = json.load(file)
                    except json.JSONDecodeError:
                        logging.error(f"Archivo JSON corrupto o vacío: {archivo}")
                        cocinas_data[cocina] = []
            else:
                cocinas_data[cocina] = []

        if not self.verificacion_inicial_realizada:
            for cocina, datos in cocinas_data.items():
                if datos:
                    datos[-1]["estado"] = "CICLO_INCOMPLETO"
                    self.guardarEnBaseDeDatos(cocina, datos)
                    cocinas_data[cocina] = []
            self.verificacion_inicial_realizada = True

        try:
            root_node = self.conexion_servidor.get_root_node().get_child(["0:Objects"]).get_child(["2:ServerInterfaces"])

            interfaces = {
                "2:Server interface_1": ["2:COCINA-1-L1", "2:COCINA-2-L1", "2:COCINA-3-L1", "2:ENFRIADOR-1-L1", "2:ENFRIADOR-2-L1", "2:ENFRIADOR-3-L1", "2:ENFRIADOR-4-L1"],
                "2:Server interface_2": ["2:COCINA-4-L2", "2:COCINA-5-L2", "2:COCINA-6-L2", "2:ENFRIADOR-5-L2", "2:ENFRIADOR-6-L2", "2:ENFRIADOR-7-L2", "2:ENFRIADOR-8-L2"]
            }

            for interface, cocinas in interfaces.items():
                try:
                    interface_node = root_node.get_child([interface])
                    for cocina in cocinas:
                        try:
                            cocina_node = interface_node.get_child([cocina])

                            children = cocina_node.get_children()
                            valores = [child.get_value() for child in children]

                            if len(valores) < 10:
                                logging.error(f"No se recibieron suficientes valores en {cocina}")
                                continue

                            estado = valores[3]

                            if estado == "FINALIZADO":
                                if cocinas_data[cocina]:  # Solo si hay datos, modificarlos antes de guardar
                                    cocinas_data[cocina][-1]["estado"] = "CICLO_COMPLETO"
                                    self.guardarEnBaseDeDatos(cocina, cocinas_data[cocina])
                                cocinas_data[cocina] = []  # Vaciar lista solo después de guardar

                            elif estado == "COCINANDO" or estado == "ENFRIANDO":
                                # Obtener el último ID correctamente
                                ultimo_id = max([paso["id"] for paso in cocinas_data[cocina]], default=0)
                                cocina_id = ultimo_id + 1

                                paso_data = {
                                    "id": cocina_id,
                                    "tiempo": valores[7],
                                    "temp_Agua": valores[8],
                                    "temp_Prod": valores[9],
                                    "estado": estado,
                                }

                                cocinas_data[cocina].append(paso_data)
                                print(f"✅ Paso registrado para {cocina} ({estado}): {paso_data}")

                            with open(archivos_cocinas[cocina], "w") as file:
                                json.dump(cocinas_data[cocina], file, indent=4)

                        except KeyError as e:
                            logging.error(f"Error: Clave no encontrada en cocinas_data -> {e}")
                        except Exception as e:
                            logging.error(f"Error al obtener datos de {cocina}: {e}")
                except Exception as e:
                    logging.error(f"Error al acceder a {interface}: {e}")

        except Exception as e:
            logging.error(f"Error al buscar nodos en graficoCocinas: {e}")

        return cocinas_data

    def guardarEnBaseDeDatos(self, cocina, datos):
        print(f"💾 Guardando en base de datos: {cocina} -> {datos}")
        return True  # Simulación de respuesta afirmativa