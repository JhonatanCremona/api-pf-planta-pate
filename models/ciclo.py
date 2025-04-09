from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Double
from sqlalchemy.orm import relationship
from config.db import Base

class Ciclo(Base):
    __tablename__ = "ciclo"
    
    id = Column(Integer, primary_key=True, index=True)
    estado = Column(Integer, index=True, nullable=False)
    cantidadTorres = Column(Integer, index=True, nullable=False)
    lote = Column(Integer, index=True, nullable=False)
    cantidadPausas = Column(Integer, index=True, nullable=False)
    tiempoTranscurrido = Column(Integer, index=True, nullable=False)
    fecha_inicio = Column(Integer, index=True, nullable=False)
    fecha_fin = Column(Integer, index=True, nullable=False)
    peso = Column(Integer, index=True, nullable=False)
    idEquipo = Column(Integer, index=True, nullable=False)
    idReceta = Column(Integer, index=True, nullable=False)