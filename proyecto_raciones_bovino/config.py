import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""
    
    # Configuración de la base de datos
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'racionesbovino')
    
    # URI de conexión con manejo de errores
    try:
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4'
    except Exception as e:
        print(f"Error en configuración de base de datos: {e}")
        SQLALCHEMY_DATABASE_URI = 'sqlite:///fallback.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # JWT Configuration con valores más seguros
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu-clave-secreta-muy-segura-cambiala-en-produccion')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_ACCESS_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', 30)))
    JWT_ALGORITHM = 'HS256'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
    
    # Configuración de seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-para-flask')
    WTF_CSRF_ENABLED = True
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    # Email Configuration (opcional)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Configuración de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', 50))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', 100))
    
    # Configuración de cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
    # Configuración más permisiva para desarrollo
    WTF_CSRF_ENABLED = False
    
    # Logging más detallado
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # Configuración de seguridad estricta
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # JWT más corto en producción
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # Validar que las variables críticas estén configuradas
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Validar configuración crítica
        required_vars = ['JWT_SECRET_KEY', 'SECRET_KEY', 'MYSQL_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var) == getattr(cls, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variables de entorno requeridas en producción: {', '.join(missing_vars)}")

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DEBUG = True
    
    # Base de datos en memoria para tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # JWT de prueba
    JWT_SECRET_KEY = 'test-secret-key-not-for-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    
    # Desabilitar CSRF para tests
    WTF_CSRF_ENABLED = False
    
    # Email de prueba
    MAIL_SUPPRESS_SEND = True
    
    # Cache simple para tests
    CACHE_TYPE = 'null'

class DockerConfig(Config):
    """Configuración para contenedores Docker"""
    
    # Configuración específica para Docker
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql_container')
    
    # Configuración de red para Docker
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))

# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """
    Obtiene la configuración basada en el entorno
    
    Args:
        config_name: Nombre de la configuración ('development', 'production', etc.)
        
    Returns:
        Clase de configuración correspondiente
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)

def validate_config():
    """
    Valida que la configuración sea correcta
    
    Returns:
        Tuple (is_valid, errors_list)
    """
    errors = []
    
    # Validar base de datos
    if not os.getenv('MYSQL_DB'):
        errors.append("MYSQL_DB no está configurado")
    
    # Validar JWT
    jwt_secret = os.getenv('JWT_SECRET_KEY', '')
    if len(jwt_secret) < 32:
        errors.append("JWT_SECRET_KEY debe tener al menos 32 caracteres")
    
    # Validar configuración de email si está habilitada
    if os.getenv('MAIL_USERNAME') and not os.getenv('MAIL_PASSWORD'):
        errors.append("MAIL_PASSWORD es requerido si MAIL_USERNAME está configurado")
    
    return len(errors) == 0, errors

# Configuración de logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d]: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': 'app.log',
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}