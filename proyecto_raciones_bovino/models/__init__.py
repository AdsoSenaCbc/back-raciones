from flask_sqlalchemy import SQLAlchemy
# Instancia de SQLAlchemy que se usará en todos los modelos
db = SQLAlchemy()
# Importar todos los modelos para que estén disponibles
from .rol import RolUsuario
from .usuario import Usuario
from .hacienda import Hacienda
from .estado_animal import EstadoAnimal
from .animal import Animal
from .catalogo_vacuna import CatalogoVacuna
from .vacunacion_animal import VacunacionAnimal
from .nacimiento import Nacimiento
from .nrc import NrcLactanciaBase, NrcProduccionLeche, NrcGestacion, NrcCeba
from .ingredientes import Departamento, Municipio, ConsultaBromatologica, Ingrediente, CaracteristicaNutricional
from .raciones import RacionLactancia, RacionCeba, DetalleRacionLactancia, DetalleRacionCeba
# Hacer disponibles los modelos cuando se importe el paquete
__all__ = [
    'db',
    'RolUsuario',
    'Usuario',
    'Hacienda',
    'EstadoAnimal',
    'Animal',
    'CatalogoVacuna',
    'VacunacionAnimal',
    'Nacimiento',
    
    # Modelos NRC (National Research Council)
    'NrcLactanciaBase',
    'NrcProduccionLeche',
    'NrcGestacion',
    'NrcCeba',
    
    # Modelos de ubicación e ingredientes
    'Departamento',
    'Municipio',
    'ConsultaBromatologica',
    'Ingrediente',
    'CaracteristicaNutricional',
    
    # Modelos de raciones
    'RacionLactancia',
    'RacionCeba',
    'DetalleRacionLactancia',
    'DetalleRacionCeba'
]