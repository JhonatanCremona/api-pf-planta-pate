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

    def calcular_tiempo_transcurrido_json(self, historial_actual):
        """Calcula el tiempo transcurrido entre el primer y último registro en el historial JSON"""
        try:
            if not historial_actual or len(historial_actual) < 2:
                return "00:00:00"
                
            # Obtener el primer y último registro del historial
            primer_registro = historial_actual[0]
            ultimo_registro = historial_actual[-1]
            
            # Obtener timestamps de ambos registros
            tiempo_inicio = datetime.strptime(primer_registro["tiempo"], "%Y-%m-%d %H:%M:%S")
            tiempo_final = datetime.strptime(ultimo_registro["tiempo"], "%Y-%m-%d %H:%M:%S")
            
            # Calcular diferencia
            diferencia = tiempo_final - tiempo_inicio
            
            # Formatear resultado
            horas = diferencia.days * 24 + diferencia.seconds // 3600
            minutos = (diferencia.seconds % 3600) // 60
            segundos = diferencia.seconds % 60
            
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        except Exception as e:
            logger.error(f"Error calculando tiempo transcurrido desde JSON: {e}")
            return "00:00:00"

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
                        "COCINA": ["OPERATIVO", "PAUSA", "PRE OPERATIVO"],
                        "ENFRIADOR": ["PRE OPERATIVO", "OPERATIVO", "PAUSA"]
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
                                "COCINA": ["OPERATIVO", "PRE OPERATIVO", "PAUSA"],
                                "ENFRIADOR": ["OPERATIVO", "PRE OPERATIVO", "PAUSA"]
                            }

                            # Modificar esta sección en datosGenerales()
                            if estado_actual in estados_continuos[tipo]:
                                historial_actual = datos_json.get(equipo, [])
                                nuevo_id = len(historial_actual) + 1

                                # Generar id_ciclo sin dependencia de base de datos
                                id_ciclo = self.obtener_id_ciclo_existente(valores[22], valores[0])
                                
                                # Crear nuevo_paso según el tipo de equipo
                                if tipo == "COCINA":
                                    nuevo_paso = {
                                        "id_historial": nuevo_id,
                                        "tiempo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "temp_agua": valores[7],
                                        "temp_ingreso": valores[9],
                                        "temp_prod": valores[8],
                                        "estado": valores[3],
                                        "niv_agua": valores[11],
                                        "idCiclo": id_ciclo,
                                    }
                                else:  # ENFRIADOR
                                    nuevo_paso = {
                                        "id_historial": nuevo_id,
                                        "tiempo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "temp_agua": valores[8],
                                        "temp_ingreso": valores[10],
                                        "temp_prod": valores[9],
                                        "estado": valores[3],
                                        "niv_agua": valores[12],
                                        "idCiclo": id_ciclo,
                                    }

                                historial_actual.append(nuevo_paso)
                                datos_json[equipo] = historial_actual

                                try:
                                    # Guardar el historial JSON
                                    with open(archivos_json[equipo], "w") as file:
                                        json.dump(historial_actual, file, indent=2, default=datetime_to_string)
                                except Exception as e:
                                    logger.error(f"No se pudo guardar paso en {equipo}: {e}")

                            if estado_actual in ["FINALIZADO", "CANCELADO"] and estado_anterior not in ["FINALIZADO", "CANCELADO"]:
                                historial_actual = datos_json.get(equipo, [])
                                if historial_actual:
                                    ultimo_paso = historial_actual[-1]
                                    id_ciclo = ultimo_paso.get("idCiclo")
                                    
                                    if id_ciclo is not None:
                                        if self.finalizar_ciclo(id_ciclo, estado_actual):  # Pasamos el estado actual
                                            datos_json[equipo] = []
                                            with open(archivos_json[equipo], "w") as file:
                                                json.dump([], file)
                                            logger.info(f"Ciclo finalizado y historial limpiado para {equipo}")

                            # Reemplaza la llamada actual a guardarEnBaseCiclo por:
                            if estado_anterior in ["FINALIZADO", "CANCELADO"] and estado_actual in ["PRE OPERATIVO", "PRE OPERATIVO"]:
                                datos_json[equipo] = []
                                with open(archivos_json[equipo], "w") as file:
                                    json.dump([], file)
                            
                                # Obtiene el ID de la receta
                                id_receta = self.obtener_o_crear_receta(valores)
                                
                                #if id_receta is not None:
                                #    self.guardarEnBaseCiclo({
                                #        "estadoMaquina": estado_actual,
                                #        "cantidadTorres": valores[4],
                                #        "lote": valores[22],
                                #        "fecha_inicio": datetime.now(),
                                #        "peso": valores[5],
                                #        "idEquipo": valores[0],
                                #        "idReceta": id_receta,  # Usamos el ID obtenido
                                #    })
                                #else:
                                #    logger.error(f"No se pudo obtener/crear la receta para {equipo}")

                            if "COCINA" in equipo:
                                ciclo_activo = None
                                if historial_actual:
                                    id_ciclo = historial_actual[0].get("idCiclo")
                                    if id_ciclo:
                                        ciclo_activo = self.session.query(Ciclo).filter_by(id=id_ciclo).first()
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
                                    "tiempoTranscurrido": self.calcular_tiempo_transcurrido_json(historial_actual) if historial_actual else "00:00:00",
                                    "ultimo_ciclo": self.obtener_ultimo_ciclo_finalizado(valores[0]),
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
                                ciclo_activo = None
                                if historial_actual:
                                    id_ciclo = historial_actual[0].get("idCiclo")
                                    if id_ciclo:
                                        ciclo_activo = self.session.query(Ciclo).filter_by(id=id_ciclo).first()
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
                                    "tiempoTranscurrido": self.calcular_tiempo_transcurrido_json(historial_actual) if historial_actual else "00:00:00",
                                    "ultimo_ciclo": self.obtener_ultimo_ciclo_finalizado(valores[0]),
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

    def obtener_ultimo_ciclo_finalizado(self, id_equipo):
        """Obtiene el último ciclo finalizado para un equipo,
        con un fallback para cuando la base de datos está vacía"""
        try:
            # Intentar obtener de la base de datos
            ultimo_ciclo = (
                self.session.query(Ciclo)
                .filter(
                    Ciclo.idEquipo == id_equipo,
                    Ciclo.estadoMaquina.in_(["FINALIZADO", "CANCELADO"]),
                    Ciclo.fecha_fin.isnot(None)
                )
                .order_by(Ciclo.fecha_fin.desc())
                .first()
            )
            return ultimo_ciclo.id if ultimo_ciclo else None
        except Exception:
            # Si no funciona la BD, retornar None
            return None

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

    def finalizar_ciclo(self, id_ciclo, estado_maquina):
        try:
            ciclo = self.session.query(Ciclo).filter_by(id=id_ciclo).first()
            if ciclo and ciclo.fecha_fin is None:  # Verifica que no se haya finalizado antes
                fecha_fin = datetime.now()
                tiempo_transcurrido = str(fecha_fin - ciclo.fecha_inicio)
                
                ciclo.fecha_fin = fecha_fin
                ciclo.cantidadPausas = 1
                ciclo.tiempoTranscurrido = tiempo_transcurrido
                ciclo.estadoMaquina = estado_maquina
                
                self.session.commit()
                logger.info(f"Ciclo {id_ciclo} finalizado correctamente con estado {estado_maquina}")
                return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al finalizar ciclo {id_ciclo}: {e}")
        return False

    def guardar_sensores_activos(self, valores, id_ciclo, tipo):
        try:
            # Primero verificamos si el ciclo está finalizado
            ciclo = self.session.query(Ciclo).filter_by(id=id_ciclo).first()
            if not ciclo or ciclo.fecha_fin is not None:
                logger.warning(f"No se pueden guardar sensores: ciclo {id_ciclo} no existe o ya está finalizado")
                return
                
            fecha_actual = datetime.now()
            
            # Definir índices según el tipo
            if tipo == "COCINA":
                indices = {
                    "temp_agua": 7,
                    "temp_ingreso": 9,
                    "temp_prod": 8,
                    "temp_chiller": 10,
                    "niv_agua": 11
                }
            else:  # ENFRIADOR
                indices = {
                    "temp_agua": 8,
                    "temp_ingreso": 10,
                    "temp_prod": 9,
                    "temp_chiller": 11,
                    "niv_agua": 12
                }

            # Verificar que el ciclo sigue activo antes de guardar
            if ciclo.fecha_fin is None:
                sensores_a_guardar = [
                    {
                        "idSensor": self.SENSORES_ACTIVOS["temp_agua"],
                        "valor": valores[indices["temp_agua"]],
                    },
                    {
                        "idSensor": self.SENSORES_ACTIVOS["temp_ingreso"],
                        "valor": valores[indices["temp_ingreso"]],
                    },
                    {
                        "idSensor": self.SENSORES_ACTIVOS["temp_prod"],
                        "valor": valores[indices["temp_prod"]],
                    },
                    {
                        "idSensor": self.SENSORES_ACTIVOS["temp_chiller"],
                        "valor": valores[indices["temp_chiller"]],
                    },
                    {
                        "idSensor": self.SENSORES_ACTIVOS["niv_agua"],
                        "valor": valores[indices["niv_agua"]],
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
            else:
                logger.warning(f"No se guardaron sensores: el ciclo {id_ciclo} ya está finalizado")
        
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
        """
        Genera un ID único para el ciclo basado en el lote y equipo,
        sin necesidad de consultar la base de datos.
        """
        try:
            # Primero intentamos buscar en la base de datos por compatibilidad
            try:
                ciclo = (self.session.query(Ciclo)
                        .filter_by(lote=lote, idEquipo=idEquipo, fecha_fin=None)
                        .order_by(Ciclo.id.desc())
                        .first())
                
                if ciclo:
                    return ciclo.id
            except Exception:
                # Si hay error en la BD, continuamos con el método alternativo
                pass
            
            # Método alternativo: generar un ID único basado en lote y equipo
            # Esto permite mantener consistencia entre ejecuciones
            import hashlib
            
            # Combinamos lote y equipo para crear un identificador único
            unique_key = f"{lote}-{idEquipo}"
            
            # Generamos un hash para tener un valor numérico consistente
            hash_object = hashlib.md5(unique_key.encode())
            hash_hex = hash_object.hexdigest()
            
            # Convertimos los primeros 8 caracteres del hash a un entero
            # Esto nos da un ID entre 0 y 4,294,967,295
            ciclo_id = int(hash_hex[:8], 16) 
            
            logger.info(f"Generado ID virtual {ciclo_id} para equipo {idEquipo}, lote {lote}")
            return ciclo_id
                
        except Exception as e:
            logger.error(f"Error generando ID para ciclo: {e}")
            # Fallback: generar un ID aleatorio entre 1 y 1,000,000
            import random
            return random.randint(1, 1000000)

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
