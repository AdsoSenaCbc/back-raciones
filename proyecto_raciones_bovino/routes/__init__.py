# Inicialización del módulo de rutas

# Importar todos los blueprints
from .auth import auth_bp
from .usuarios import usuarios_bp
from .haciendas import haciendas_bp
from .animales import animales_bp
from .vacunacion import vacunacion_bp
from .nacimientos import nacimientos_bp

# Hacer disponibles los blueprints cuando se importe el paquete
__all__ = [
    'auth_bp',
    'usuarios_bp',
    'haciendas_bp',
    'animales_bp',
    'vacunacion_bp',
    'nacimientos_bp'
]