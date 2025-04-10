from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
from models.ciclo import Ciclo
from models.receta import Receta

from collections import defaultdict

from typing import List

from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

from io import BytesIO
import os
import json

from config import db
from config.db import get_db

import logging

logger = logging.getLogger("uvicorn")

def datosGraficos(db: Session, fecha_inicio: date, fecha_fin: date) -> List[dict]:
    fecha_inicio = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin = datetime.combine(fecha_fin, datetime.max.time())

    ciclos = (
        db.query(Ciclo.estado, Ciclo.lote, Ciclo.peso)
        .filter(Ciclo.fecha_fin.between(fecha_inicio, fecha_fin))
        .all()
    )

    resultado = []
    for estado, lote, peso in ciclos:
        resultado.append({
            "estado": estado,
            "lote": lote,
            "peso": peso
        })

    return resultado

class ObtenerNodosOpc:
    PANTALLA_ENCENDIDA = True
    ULTIMO_ESTADO_PANTALLA = False

    def __init__(self, conexion_servidor):
        self.conexion_servidor = conexion_servidor
        self.estados_previos = {}
        self.lotes_actuales = {}   

    def datosGenerales(self):
        resultado = {
            "datos-cocinas": [],
            "datos-enfriadores": [],
        }

        datos_json = {}

        try:
            root_node = self.conexion_servidor.get_root_node().get_child(["0:Objects"]).get_child(["2:ServerInterfaces"])

            interfaces = {
                "2:Server interface_1": [
                    "2:COCINA-1-L1", "2:COCINA-2-L1", "2:COCINA-3-L1",
                    "2:ENFRIADOR-1-L1", "2:ENFRIADOR-2-L1", "2:ENFRIADOR-3-L1", "2:ENFRIADOR-4-L1"
                ],
                "2:Server interface_2": [
                    "2:COCINA-4-L2", "2:COCINA-5-L2", "2:COCINA-6-L2",
                    "2:ENFRIADOR-5-L2", "2:ENFRIADOR-6-L2", "2:ENFRIADOR-7-L2", "2:ENFRIADOR-8-L2"
                ]
            }

            cocina_id = 1
            enfriador_id = 7

            for interface, equipos in interfaces.items():
                try:
                    interface_node = root_node.get_child([interface])
                    for equipo in equipos:
                        try:
                            equipo_node = interface_node.get_child([equipo])
                            children = equipo_node.get_children()
                            valores = [child.get_value() for child in children]

                            estado_actual = valores[3]
                            id_equipo = valores[0]
                            id_receta = valores[2]
                            cantidad_torres = valores[4]
                            estado_previo = self.estados_previos.get(equipo)

                            if not hasattr(self, "lotes_actuales"):
                                self.lotes_actuales = {}

                            if not equipo in datos_json:
                                datos_json[equipo] = {
                                    "historialTemperaturaAgua": [],
                                    "historialTemperaturaProducto": []
                                }

                            if estado_previo != estado_actual:
                                logger.info(f"🔄 Cambio detectado en {equipo}: {estado_previo} -> {estado_actual}")
                                self.estados_previos[equipo] = estado_actual

                                # Guardar historial solo cuando cambia el estado
                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                datos_json[equipo]["historialTemperaturaAgua"].append({
                                    "tiempo": now_str,
                                    "valor": valores[8] if "COCINA" in equipo else valores[9]
                                })
                                datos_json[equipo]["historialTemperaturaProducto"].append({
                                    "tiempo": now_str,
                                    "valor": valores[9] if "COCINA" in equipo else valores[10]
                                })

                            # Obtener lote actual o generar uno nuevo
                            if equipo not in self.lotes_actuales:
                                self.lotes_actuales[equipo] = f"LOTE-{os.urandom(4).hex().upper()}"

                            lote = self.lotes_actuales[equipo]

                            if estado_actual in ["PRE-CALENTAMIENTO", "PRE-ENFRIAMIENTO"] and estado_previo in ["CANCELADO", "FINALIZADO"]:
                                lote = f"LOTE-{os.urandom(4).hex().upper()}"
                                datos_json[equipo] = {
                                    "historialTemperaturaAgua": [],
                                    "historialTemperaturaProducto": []
                                }

                                db: Session = next(get_db())
                                receta = db.query(Receta).filter(Receta.nombre == id_receta).first()
                                if not receta:
                                    logger.error(f"No se encontró la receta con nombre {id_receta}")
                                    continue

                                tipo_fin = receta.tipoFin

                                nuevo_ciclo = Ciclo(
                                    estadoMaquina=estado_actual,
                                    cantidadTorres=cantidad_torres,
                                    lote=lote,
                                    cantidadPausas=0,
                                    tiempoTranscurrido="00:00:00",
                                    fecha_inicio=datetime.now(),
                                    fecha_fin=None,
                                    peso=1,
                                    idEquipo=id_equipo,
                                    idReceta=receta.id
                                )

                                db.add(nuevo_ciclo)
                                db.commit()
                                logger.info(f"✅ Nuevo ciclo creado para {equipo} con estado {estado_actual}")

                            self.lotes_actuales[equipo] = lote

                            if "COCINA" in equipo:
                                equipo_general = {
                                    "tipo": "COCINA",
                                    "id": cocina_id,
                                    "estado": valores[3],
                                    "temp_Agua": valores[7],
                                    "temp_Prod": valores[8],
                                    "temp_Ingreso": valores[9],
                                    "temp_Chiller": valores[10],
                                    "niv_Agua": valores[11],
                                    "receta": valores[2],
                                    "receta_paso_actual": valores[12],
                                    "tiempoTranscurrido": valores[6],
                                }
                                equipo_detalle = {
                                    "num_cocina": valores[0],
                                    "num_receta": valores[1],
                                    "nom_receta": valores[2],
                                    "cant_torres": valores[4],
                                    "tipo_fin": valores[5],
                                    "sector_io": [{
                                        "filtro_succion_agua": valores[13],
                                        "entrada_agua": valores[14],
                                        "bomba_recirculacion": valores[15],
                                        "vapor_serpentina": valores[16],
                                        "vapor_serpentina_acc": valores[17],
                                        "vapor_vivo": valores[18],
                                        "vapor_vivo_acc": valores[19],
                                        "tapa_estado": valores[20],
                                        "tapa_estado_acc": valores[21],
                                    }],
                                    "historial": datos_json.get(equipo, [])
                                }
                                resultado["datos-cocinas"].append([equipo_general, equipo_detalle])
                                cocina_id += 1

                            elif "ENFRIADOR" in equipo:
                                equipo_general = {
                                    "tipo": "ENFRIADOR",
                                    "id": enfriador_id,
                                    "estado": valores[3],
                                    "temp_Agua": valores[8],
                                    "temp_Prod": valores[9],
                                    "temp_Ingreso": valores[10],
                                    "temp_Chiller": valores[11],
                                    "niv_Agua": valores[12],
                                    "receta": valores[2],
                                    "receta_paso_actual": valores[6],
                                    "tiempoTranscurrido": valores[7],
                                }
                                equipo_detalle = {
                                    "num_enfriador": valores[0],
                                    "num_receta": valores[1],
                                    "nom_receta": valores[2],
                                    "cant_torres": valores[4],
                                    "tipo_fin": valores[5],
                                    "sector_io": [{
                                        "filtro_succion_agua": valores[13],
                                        "entrada_agua": valores[14],
                                        "bomba_recirculacion": valores[15],
                                        "valvula_amoniaco": valores[16],
                                        "vapor_serpentina_acc": valores[17],
                                        "vapor_vivo_lim": valores[18],
                                        "vapor_vivo_lim_acc": valores[19],
                                        "tapa_estado": valores[20],
                                        "tapa_estado_acc": valores[21],
                                    }],
                                    "historial": datos_json.get(equipo, [])
                                }
                                resultado["datos-enfriadores"].append([equipo_general, equipo_detalle])
                                enfriador_id += 1

                        except Exception as e:
                            logger.error(f"Error al procesar equipo {equipo}: {e}")

                except Exception as e:
                    logger.error(f"Error al acceder a {interface}: {e}")

        except Exception as e:
            logger.error(f"Error al buscar nodos: {e}")

        return resultado

    def graficoCocinas(self):
        if not hasattr(self, "verificacion_inicial_realizada"):
            self.verificacion_inicial_realizada = False

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
                    datos[-1]["tipoFin"] = "CANCELADO"
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
                        lote = self.lotes_actuales.get(cocina, "LOTE-DESCONOCIDO")
                        try:
                            cocina_node = interface_node.get_child([cocina])
                            children = cocina_node.get_children()
                            valores = [child.get_value() for child in children]

                            if len(valores) < 10:
                                logging.error(f"No se recibieron suficientes valores en {cocina}")
                                continue

                            estado = valores[3]

                            if estado == "FINALIZADO":
                                if cocinas_data[cocina]:
                                    cocinas_data[cocina][-1]["tipoFin"] = "CICLO COMPLETO"
                                    self.guardarEnBaseDeDatos(cocina, cocinas_data[cocina])
                                cocinas_data[cocina] = []

                            elif estado in ["COCINANDO", "ENFRIANDO", "PRE-CALENTAMIENTO", "PRE-ENFRIAMIENTO"]:
                                ultimo_id = max([paso["id"] for paso in cocinas_data[cocina]], default=0)
                                cocina_id = ultimo_id + 1

                                paso_data = {
                                    "id": cocina_id,
                                    "tiempo": valores[7],
                                    "temp_Agua": valores[8],
                                    "temp_Ingreso": valores[10],
                                    "estado": estado,
                                    "lote": lote
                                }

                                cocinas_data[cocina].append(paso_data)
                                #print(f"✅ Paso registrado para {cocina} ({estado}): {paso_data}")

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

    def guardarEnBaseDeDatos(self, cocina: str, datos: list):
        try:
            db: Session = next(get_db())

            if not datos:
                logger.warning(f"No hay datos para guardar en la base de datos para {cocina}")
                return

            # Obtener el último paso
            ultimo_paso = datos[-1]

            # Asignar el estado CANCELADO
            estado_map = {
                "CANCELADO": "CANCELADO"
            }
            estado_valor = estado_map["CANCELADO"]

            # Crear un nuevo ciclo con los datos del último paso
            nuevo_ciclo = Ciclo(
                estadoMaquina=estado_valor,
                cantidadTorres=1,  # Ajustar según los datos del nodo OPC
                lote=123,  # Ajustar según los datos del nodo OPC
                cantidadPausas=0,
                tiempoTranscurrido=ultimo_paso.get("tiempo", 0),
                fecha_inicio=int(datetime.now().timestamp()),
                fecha_fin=int(datetime.now().timestamp()),
                peso=1,
                idEquipo=int(cocina.split("-")[-1].replace("L", "")),
                idReceta=int(cocina.split("-")[-1].replace("L", ""))
            )

            db.add(nuevo_ciclo)
            db.commit()
            logger.info(f"✅ Último paso guardado como CANCELADO en la base de datos para {cocina}")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error al guardar el último paso en la base de datos: {e}")

        finally:
            db.close()

    async def actualizarRecetas(self):
        lista_recetas = {}

        try:
            root_node = await self.conexion_servidor.get_objects_nodos()  # ESTA SÍ ES ASYNC

            # A partir de aquí, todo lo demás es síncrono
            objects_node = root_node.get_child(["0:Objects"])
            server_interface_node = objects_node.get_child(["2:ServerInterfaces"])
            server_interface_1 = server_interface_node.get_child(["2:Server interface_1"])

            if not server_interface_1:
                logger.error("No se encontró el nodo 'Server interface_1'.")
                return None

            e_listaRecetario = server_interface_1.get_child([f"2:RECETARIO"])
            e_datosSeleccionado = server_interface_1.get_child([f"2:datosComplementarios"])

            logger.info("LEEEEEEEEE")

            pantalla_receta = e_datosSeleccionado.get_child([f"2:pantalla_receta"])
            self.PANTALLA_ENCENDIDA = pantalla_receta.get_value()
            logger.error(f"PANTALLA OPC: {self.PANTALLA_ENCENDIDA}")

            if self.PANTALLA_ENCENDIDA != self.ULTIMO_ESTADO_PANTALLA:
                if self.PANTALLA_ENCENDIDA is False:
                    try:
                        for child in e_listaRecetario.get_children():
                            receta = {}
                            for elem in child.get_children():
                                receta[elem.get_browse_name().Name] = elem.get_value()
                            lista_recetas[child.get_browse_name().Name] = receta
                            logger.info(f"Receta {child.get_browse_name().Name} obtenida con {len(receta)} valores.")
                    except Exception as e:
                        logger.error("No se pudo acceder a la estructura de recetario")

                    self.guardarRecetaEnBD(lista_recetas)

            self.ULTIMO_ESTADO_PANTALLA = self.PANTALLA_ENCENDIDA

        except Exception as e:
            logger.error(f"Error al intertar ACTUALIZAR RECETAS {e}")

    def guardarRecetaEnBD(self, datosPLC):
        try:
            db: Session = next(get_db())

            for index, (clave, datosReceta) in enumerate(datosPLC.items(), start=1):
                receta_id = index  # Matcheamos el índice + 1 con el ID

                if receta_id > 20:
                    print(f"Receta {receta_id} excede el límite de 20 y no será guardada.")
                    continue

                receta_existente = db.query(Receta).filter(Receta.id == receta_id).first()

                if receta_existente:
                    receta_existente.nombre = datosReceta.get("nombre")
                    receta_existente.nroPaso = datosReceta.get("nroPaso")
                    receta_existente.tipoFin = datosReceta.get("tipoFin")
                    print(f"Receta {receta_id} actualizada correctamente.")
                else:
                    # Creamos una nueva receta si no existe
                    nueva_receta = Receta(
                        id=receta_id,
                        nombre=datosReceta.get("nombre"),
                        nroPaso=datosReceta.get("nroPaso"),
                        tipoFin=datosReceta.get("tipoFin"),
                    )
                    db.add(nueva_receta)
                    print(f"Receta {receta_id} creada correctamente.")

            # Confirmamos todos los cambios realizados
            db.commit()

        except Exception as e:
            # Si hay un error, revertimos los cambios
            db.rollback()
            print(f"Error al guardar o actualizar las recetas en la base de datos: {e}")

        finally:
            # Cerramos la sesión de la base de datos
            db.close()
