from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Double
from sqlalchemy.orm import relationship
from config.db import Base

class SensoresAA(Base):
    __tablename__ = "sensoresaa"
    
    id = Column(Integer, primary_key=True, index=True)
    idSensor = Column(Integer, index=True, nullable=False)
    valor = Column(Integer, index=True, nullable=False)
    idCiclo = Column(Integer, index=True, nullable=False)
    fechaRegistro = Column(Integer, index=True, nullable=False)