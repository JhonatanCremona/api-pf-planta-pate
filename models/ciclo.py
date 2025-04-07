from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Double
from sqlalchemy.orm import relationship
from config.db import Base

class Ciclo(Base):
    __tablename__ = "ciclo"
    
    id = Column(Integer, primary_key=True, index=True)
    estado = Column(Integer, index=True, nullable=False)
    nroTorre = Column(Integer, index=True, nullable=False)
    lote = Column(Integer, index=True, nullable=False)
    tipoFin = Column(Integer, index=True, nullable=False)
    cantidadPausas = Column(Integer, index=True, nullable=False)
    tiempoTranscurrido = Column(Integer, index=True, nullable=False)
    fechaInicio = Column(Integer, index=True, nullable=False)
    fechaFin = Column(Integer, index=True, nullable=False)
    cantidad = Column(Integer, index=True, nullable=False)
    idEquipo = Column(Integer, index=True, nullable=False)