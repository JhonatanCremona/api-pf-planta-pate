from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
from models.ciclo import Ciclo
from models.receta import Receta
from models.sensoresAA import SensoresAA

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

def datetime_to_string(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def limpiar_archivo_json(archivo):
    try:
        if os.path.exists(archivo):
            with open(archivo, "w") as file:
                json.dump([], file)
            logger.info(f"Archivo {archivo} limpiado correctamente")
    except Exception as e:
        logger.error(f"Error al limpiar archivo {archivo}: {e}")

class ObtenerNodosOpc:
    PANTALLA_ENCENDIDA = True
    ULTIMO_ESTADO_PANTALLA = False

    SENSORES_ACTIVOS = {
        "temp_agua": 1,      # Temperatura agua
        "temp_ingreso": 2,   # Temperatura ingreso
        "temp_prod": 3,      # Temperatura producto
        "temp_chiller": 4,   # Temperatura chiller
        "niv_agua": 5,       # Nivel agua
    }

    def __init__(self, conexion_servidor):
        self.conexion_servidor = conexion_servidor
        self.estados_anteriores = {}
        self.session = next(get_db())

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()

    def datosGenerales(self):
        resultado = {
            "datos-cocinas": [],
            "datos-enfriadores": [],
        }

        archivos_json = {
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

        datos_json = {}
        for equipo, archivo in archivos_json.items():
            try:
                if os.path.exists(archivo) and os.path.getsize(archivo) > 0:
                    try:
                        with open(archivo, "r") as file:
                            datos_json[equipo] = json.load(file)
                    except json.JSONDecodeError:
                        logger.error(f"Error en formato JSON en archivo {archivo}")
                        limpiar_archivo_json(archivo)
                        datos_json[equipo] = []
                else:
                    datos_json[equipo] = []
            except Exception as e:
                logger.error(f"Error cargando archivo {archivo}: {e}")
                datos_json[equipo] = []

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

                    estados_validos = {
                        "COCINA": ["OPERATIVO", "PAUSA", "PRE CALENTAMIENTO"],
                        "ENFRIADOR": ["PRE ENFRIAMIENTO", "OPERATIVO", "PAUSA"]
                    }
                    
                    estados_anteriores = {}

                    for equipo in equipos:
                        try:
                            equipo_node = interface_node.get_child([equipo])
                            children = equipo_node.get_children()
                            valores = [child.get_value() for child in children]

                            historial_actual = datos_json.get(equipo, [])
                            nuevo_id = len(historial_actual) + 1

                            tipo = "COCINA" if "COCINA" in equipo else "ENFRIADOR"
                            estado_actual = valores[3].strip().upper()
                            estado_anterior = self.estados_anteriores.get(equipo, "")

                            self.estados_anteriores[equipo] = estado_actual

                            estados_continuos = {
                                "COCINA": ["OPERATIVO", "PRE CALENTAMIENTO", "PAUSA"],
                                "ENFRIADOR": ["OPERATIVO", "PRE ENFRIAMIENTO", "PAUSA"]
                            }

                            if estado_actual in estados_continuos[tipo]:
                                historial_actual = datos_json.get(equipo, [])
                                nuevo_id = len(historial_actual) + 1

                                id_ciclo = self.obtener_id_ciclo_existente(valores[22], valores[0])

                                if id_ciclo is not None:
                                    # Guardar el paso en el historial JSON como lo haces actualmente
                                    nuevo_paso = {
                                        "id_historial": nuevo_id,
                                        "tiempo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "temp_agua": valores[8],
                                        "temp_ingreso": valores[9],
                                        "estado": valores[3],
                                        "niv_agua": valores[11],
                                        "idCiclo": id_ciclo,
                                    }

                                    historial_actual.append(nuevo_paso)
                                    datos_json[equipo] = historial_actual

                                    try:
                                        # Guardar el historial JSON
                                        with open(archivos_json[equipo], "w") as file:
                                            json.dump(historial_actual, file, indent=2, default=datetime_to_string)
                                        
                                        # Guardar los sensores activos
                                        self.guardar_sensores_activos(valores, id_ciclo)
                                        
                                    except Exception as e:
                                        logger.error(f"No se pudo guardar paso en {equipo}: {e}")

                            if estado_actual in ["FINALIZADO", "CANCELADO"] and (estado_anterior!="FINALIZADO" or estado_anterior!="CANCELADO"):
                                historial_actual = datos_json.get(equipo, [])
                                if historial_actual:
                                    ultimo_paso = historial_actual[-1]
                                    id_ciclo = ultimo_paso.get("idCiclo")
                                    
                                    if id_ciclo is not None:
                                        if self.finalizar_ciclo(id_ciclo):
                                            datos_json[equipo] = []
                                            with open(archivos_json[equipo], "w") as file:
                                                json.dump([], file)
                                            logger.info(f"Ciclo finalizado y historial limpiado para {equipo}")

                            # Reemplaza la llamada actual a guardarEnBaseCiclo por:
                            if estado_anterior in ["FINALIZADO", "CANCELADO"] and estado_actual in ["PRE CALENTAMIENTO", "PRE ENFRIAMIENTO"]:
                                datos_json[equipo] = []
                                with open(archivos_json[equipo], "w") as file:
                                    json.dump([], file)

                                # Obtiene el ID de la receta
                                id_receta = self.obtener_o_crear_receta(valores)
                                
                                if id_receta is not None:
                                    self.guardarEnBaseCiclo({
                                        "estadoMaquina": estado_actual,
                                        "cantidadTorres": valores[4],
                                        "lote": valores[22],
                                        "fecha_inicio": datetime.now(),
                                        "peso": valores[5],
                                        "idEquipo": valores[0],
                                        "idReceta": id_receta,  # Usamos el ID obtenido
                                    })
                                else:
                                    logger.error(f"No se pudo obtener/crear la receta para {equipo}")

                            if "COCINA" in equipo:
                                equipo_general = {
                                    "tipo": "COCINA",
                                    "id": cocina_id,
                                    "estado": valores[3],
                                    "temp_agua": valores[7],
                                    "temp_prod": valores[8],
                                    "temp_ingreso": valores[9],
                                    "temp_chiller": valores[10],
                                    "niv_agua": valores[11],
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
                                    "temp_agua": valores[8],
                                    "temp_prod": valores[9],
                                    "temp_ingreso": valores[10],
                                    "temp_chiller": valores[11],
                                    "niv_agua": valores[12],
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
                            logger.error(f"Error al obtener datos de {equipo}: {e}")

                except Exception as e:
                    logger.error(f"Error al acceder a {interface}: {e}")

        except Exception as e:
            logger.error(f"Error al buscar nodos: {e}")

        return resultado

    def guardarEnBaseCiclo(self, datos):
        try:
            nuevo_ciclo = Ciclo(
                estadoMaquina=datos["estadoMaquina"],
                cantidadTorres=datos["cantidadTorres"],
                lote=datos["lote"],
                fecha_inicio=datos["fecha_inicio"],
                peso=datos["peso"],
                idEquipo=datos["idEquipo"],
                idReceta=datos["idReceta"]
            )
            self.session.add(nuevo_ciclo)
            self.session.commit()
            logger.info(f"Nuevo ciclo creado con ID: {nuevo_ciclo.id}")
            return nuevo_ciclo.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al guardar nuevo ciclo: {e}")
            return None

    def finalizar_ciclo(self, id_ciclo):
        """Actualiza los datos de finalización de un ciclo"""
        try:
            ciclo = self.session.query(Ciclo).filter_by(id=id_ciclo).first()
            if ciclo and ciclo.fecha_fin is None:  # Verifica que no se haya finalizado antes
                fecha_fin = datetime.now()
                tiempo_transcurrido = str(fecha_fin - ciclo.fecha_inicio)
                
                ciclo.fecha_fin = fecha_fin
                ciclo.cantidadPausas = 1
                ciclo.tiempoTranscurrido = tiempo_transcurrido
                
                self.session.commit()
                logger.info(f"Ciclo {id_ciclo} finalizado correctamente")
                return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al finalizar ciclo {id_ciclo}: {e}")
        return False

    def guardar_sensores_activos(self, valores, id_ciclo):
        try:
            fecha_actual = datetime.now()
            sensores_a_guardar = [
                {
                    "idSensor": self.SENSORES_ACTIVOS["temp_agua"],
                    "valor": valores[8],  # temp_agua
                },
                {
                    "idSensor": self.SENSORES_ACTIVOS["temp_ingreso"],
                    "valor": valores[9],  # temp_ingreso
                },
                {
                    "idSensor": self.SENSORES_ACTIVOS["temp_prod"],
                    "valor": valores[10],  # temp_producto
                },
                {
                    "idSensor": self.SENSORES_ACTIVOS["temp_chiller"],
                    "valor": valores[11],  # temp_chiller
                },
                {
                    "idSensor": self.SENSORES_ACTIVOS["niv_agua"],
                    "valor": valores[12],  # nivel_agua
                }
            ]

            for sensor in sensores_a_guardar:
                nuevo_registro = SensoresAA(
                    idSensor=sensor["idSensor"],
                    valor=sensor["valor"],
                    idCiclo=id_ciclo,
                    fechaRegistro=fecha_actual
                )
                self.session.add(nuevo_registro)
            
            self.session.commit()
            logger.info(f"Sensores activos guardados para ciclo {id_ciclo}")
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al guardar sensores activos: {e}")

    def obtener_o_crear_receta(self, valores):
        try:
            nombre_receta = valores[2]
            nro_paso = valores[12]
            tipo_fin = valores[5]

            # Buscamos la receta por nombre
            receta = self.session.query(Receta).filter(Receta.nombre == nombre_receta).first()

            if receta:
                # Si existe, actualizamos los datos por si cambiaron
                receta.nroPaso = nro_paso
                receta.tipoFin = tipo_fin
                self.session.commit()
                return receta.id
            else:
                # Si no existe, obtenemos el último ID
                ultimo_id = self.session.query(Receta).order_by(Receta.id.desc()).first()
                nuevo_id = 1 if not ultimo_id else ultimo_id.id + 1

                # Creamos la nueva receta
                nueva_receta = Receta(
                    id=nuevo_id,
                    nombre=nombre_receta,
                    nroPaso=nro_paso,
                    tipoFin=tipo_fin
                )
                self.session.add(nueva_receta)
                self.session.commit()
                logger.info(f"Nueva receta creada - ID: {nuevo_id}, Nombre: {nombre_receta}")
                return nuevo_id

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al obtener/crear receta: {e}")
            return None

    def obtener_id_ciclo_existente(self, lote, idEquipo):
        try:
            ciclo = self.session.query(Ciclo).filter_by(lote=lote, idEquipo=idEquipo).order_by(Ciclo.id.desc()).first()
            if ciclo:
                return ciclo.id
            else:
                return None
        except Exception as e:
            logger.error(f"Error al buscar ciclo existente: {e}")
            return None

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
