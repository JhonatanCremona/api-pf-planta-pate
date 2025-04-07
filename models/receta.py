from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Double
from sqlalchemy.orm import relationship
from config.db import Base

class Receta(Base):
    __tablename__ = "receta"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(Integer, index=True, nullable=False)
    nroPaso = Column(Integer, index=True, nullable=False)
    tipoDeCorte = Column(Integer, index=True, nullable=False)
    idCiclo = Column(Integer, index=True, nullable=False)