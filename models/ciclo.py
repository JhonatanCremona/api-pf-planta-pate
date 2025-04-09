from sqlalchemy import Column, Integer, String, DateTime, Float,ForeignKey
from sqlalchemy.orm import relationship
from config.db import Base

class Ciclo(Base):
    __tablename__ = "ciclo"
    
    id = Column(Integer, primary_key=True, index=True)
    estadoMaquina = Column(String(50), index=True, nullable=False)
    cantidadTorres = Column(Integer, index=True, nullable=False)
    lote = Column(String(50), index=True, nullable=False)
    cantidadPausas = Column(Integer, index=True, nullable=False)
    tiempoTranscurrido = Column(String(50), index=True, nullable=False)
    fecha_inicio = Column(DateTime, index=True, nullable=False)
    fecha_fin = Column(DateTime, index=True, nullable=False)
    peso = Column(Float, index=True, nullable=False)

    idEquipo = Column(Integer, ForeignKey("equipo.id"), nullable=False)
    equipo = relationship("Equipo", back_populates="ciclo")

    idReceta = Column(Integer, ForeignKey("receta.id"),nullable=False)
    receta = relationship("Receta", back_populates="ciclo")

    estadociclo = relationship("EstadoCiclo", back_populates="ciclo")


