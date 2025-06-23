# Inicialización del módulo de servicios

# Importar todos los servicios
from .auth_service import AuthService
from .animal_service import AnimalService
from .hacienda_service import HaciendaService
from .vacunacion_service import VacunacionService
from .nacimiento_service import NacimientoService

# Hacer disponibles los servicios cuando se importe el paquete
__all__ = [
    'AuthService',
    'AnimalService',
    'HaciendaService',
    'VacunacionService',
    'NacimientoService'
]