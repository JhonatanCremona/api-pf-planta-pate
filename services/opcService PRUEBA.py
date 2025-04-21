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

                            elif estado in ["COCINANDO", "ENFRIANDO"]:
                                ultimo_id = max([paso["id"] for paso in cocinas_data[cocina]], default=0)
                                cocina_id = ultimo_id + 1

                                paso_data = {
                                    "id": cocina_id,
                                    "tiempo": valores[7],
                                    "temp_Agua": valores[8],
                                    "temp_Ingreso": valores[10],
                                    "temp_Prod": valores[9],
                                    "estado": estado,
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