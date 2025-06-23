from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import datetime
from config import Config

# Importar modelos (TODOS LOS MODELOS INTEGRADOS + NACIMIENTOS)
from models import db, RolUsuario, Usuario, Hacienda, EstadoAnimal, Animal, CatalogoVacuna, VacunacionAnimal, Nacimiento

# Importar rutas (TODAS LAS RUTAS INTEGRADAS + NACIMIENTOS)
from routes import auth_bp, usuarios_bp, haciendas_bp, animales_bp, vacunacion_bp, nacimientos_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # Registrar blueprints (TODOS LOS BLUEPRINTS + NACIMIENTOS)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(haciendas_bp, url_prefix='/api/haciendas')
    app.register_blueprint(animales_bp, url_prefix='/api/animales')
    app.register_blueprint(vacunacion_bp, url_prefix='/api/vacunacion')
    app.register_blueprint(nacimientos_bp, url_prefix='/api/nacimientos')
    
    # Manejador de errores JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token expirado',
            'status': 'error',
            'code': 'TOKEN_EXPIRED'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Token inválido',
            'status': 'error',
            'code': 'TOKEN_INVALID'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Token requerido para acceder a este recurso',
            'status': 'error',
            'code': 'TOKEN_MISSING'
        }), 401
    
    # Manejador de errores globales
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint no encontrado',
            'status': 'error',
            'code': 'NOT_FOUND'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Método no permitido',
            'status': 'error',
            'code': 'METHOD_NOT_ALLOWED'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Error interno del servidor',
            'status': 'error',
            'code': 'INTERNAL_ERROR'
        }), 500
    
    # Ruta principal (CON TODOS LOS ENDPOINTS + NACIMIENTOS)
    @app.route('/', methods=['GET'])
    def home():
        return jsonify({
            'message': 'Bienvenido a Raciones Bovino API',
            'version': '1.2.0',
            'description': 'Sistema completo de gestión de usuarios, haciendas, animales, vacunación y nacimientos para raciones bovinas',
            'status': 'Servidor funcionando correctamente',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'auth': {
                    'login': 'POST /api/auth/login',
                    'registrar': 'POST /api/auth/registrar',
                    'registrar_admin': 'POST /api/auth/registrar-admin',
                    'cambiar_password': 'PUT /api/auth/cambiar-password',
                    'refresh': 'POST /api/auth/refresh',
                    'logout': 'POST /api/auth/logout',
                    'validar_email': 'POST /api/auth/validar-email',
                    'validar_documento': 'POST /api/auth/validar-documento'
                },
                'usuarios': {
                    'perfil': 'GET /api/usuarios/perfil',
                    'actualizar_perfil': 'PUT /api/usuarios/perfil',
                    'usuarios': 'GET /api/usuarios/usuarios',
                    'toggle_estado': 'PUT /api/usuarios/usuarios/{id}/toggle-estado',
                    'actualizar_usuario': 'PUT /api/usuarios/usuarios/{id}',
                    'eliminar_usuario': 'DELETE /api/usuarios/usuarios/{id}',
                    'roles': 'GET /api/usuarios/roles',
                    'estadisticas': 'GET /api/usuarios/estadisticas'
                },
                'haciendas': {
                    'listar': 'GET /api/haciendas/',
                    'crear': 'POST /api/haciendas/',
                    'obtener': 'GET /api/haciendas/{id}',
                    'actualizar': 'PUT /api/haciendas/{id}',
                    'cambiar_estado': 'PUT /api/haciendas/{id}/estado',
                    'eliminar': 'DELETE /api/haciendas/{id}',
                    'buscar': 'GET /api/haciendas/buscar',
                    'estadisticas': 'GET /api/haciendas/estadisticas',
                    'activas': 'GET /api/haciendas/activas',
                    'por_departamento': 'GET /api/haciendas/por-departamento',
                    'validar_nit': 'POST /api/haciendas/validar-nit'
                },
                'animales': {
                    'listar': 'GET /api/animales/',
                    'crear': 'POST /api/animales/',
                    'obtener': 'GET /api/animales/{id}',
                    'actualizar': 'PUT /api/animales/{id}',
                    'cambiar_estado': 'PUT /api/animales/{id}/estado',
                    'eliminar': 'DELETE /api/animales/{id}',
                    'buscar': 'GET /api/animales/buscar',
                    'estadisticas': 'GET /api/animales/estadisticas',
                    'por_hacienda': 'GET /api/animales/por-hacienda/{id}',
                    'estados': 'GET /api/animales/estados',
                    'hembras_reproductivas': 'GET /api/animales/hembras-reproductivas',
                    'preñadas': 'GET /api/animales/preñadas',
                    'validar_hierro': 'POST /api/animales/validar-hierro'
                },
                'vacunacion': {
                    'catalogo_vacunas': {
                        'listar': 'GET /api/vacunacion/vacunas/',
                        'crear': 'POST /api/vacunacion/vacunas/',
                        'actualizar': 'PUT /api/vacunacion/vacunas/{id}',
                        'activas': 'GET /api/vacunacion/vacunas/activas'
                    },
                    'aplicaciones': {
                        'listar': 'GET /api/vacunacion/aplicaciones/',
                        'registrar': 'POST /api/vacunacion/aplicaciones/',
                        'eliminar': 'DELETE /api/vacunacion/aplicaciones/{id}',
                        'por_animal': 'GET /api/vacunacion/animal/{id}'
                    },
                    'gestion': {
                        'proximas_dosis': 'GET /api/vacunacion/proximas-dosis',
                        'dosis_vencidas': 'GET /api/vacunacion/dosis-vencidas',
                        'estadisticas': 'GET /api/vacunacion/estadisticas',
                        'calendario': 'GET /api/vacunacion/reporte/calendario-vacunacion'
                    }
                },
                'nacimientos': {
                    'listar': 'GET /api/nacimientos/',
                    'crear': 'POST /api/nacimientos/',
                    'obtener': 'GET /api/nacimientos/{id}',
                    'actualizar': 'PUT /api/nacimientos/{id}',
                    'eliminar': 'DELETE /api/nacimientos/{id}',
                    'por_madre': 'GET /api/nacimientos/por-madre/{id}',
                    'por_padre': 'GET /api/nacimientos/por-padre/{id}',
                    'buscar': 'GET /api/nacimientos/buscar',
                    'estadisticas': 'GET /api/nacimientos/estadisticas',
                    'recientes': 'GET /api/nacimientos/recientes',
                    'crias_sin_vacunar': 'GET /api/nacimientos/crias-sin-vacunar',
                    'marcar_vacunas': 'PUT /api/nacimientos/{id}/marcar-vacunas',
                    'por_hacienda': 'GET /api/nacimientos/por-hacienda/{id}',
                    'tipos_parto': 'GET /api/nacimientos/tipos-parto',
                    'reporte_resumen': 'GET /api/nacimientos/reporte/resumen',
                    'validar_animales': 'POST /api/nacimientos/validar-animales'
                },
                'utilidades': {
                    'health': 'GET /api/health',
                    'stats': 'GET /api/stats'
                }
            }
        }), 200
    
    # Ruta de verificación de salud (CON TODAS LAS ESTADÍSTICAS + NACIMIENTOS)
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            # Verificar conexión a la base de datos
            total_usuarios = Usuario.query.count()
            total_roles = RolUsuario.query.count()
            total_haciendas = Hacienda.query.count()
            usuarios_activos = Usuario.query.filter_by(activo=True).count()
            haciendas_activas = Hacienda.query.filter_by(activo=True).count()
            
            # Estadísticas de animales
            total_animales = Animal.query.count()
            total_estados = EstadoAnimal.query.count()
            animales_activos = Animal.query.join(EstadoAnimal).filter(
                EstadoAnimal.nombre_estado == 'Activo'
            ).count()
            
            # Estadísticas de vacunación
            total_vacunas = CatalogoVacuna.query.count()
            vacunas_activas = CatalogoVacuna.query.filter_by(activo=True).count()
            total_vacunaciones = VacunacionAnimal.query.count()
            
            # Estadísticas de nacimientos (NUEVO)
            total_nacimientos = Nacimiento.query.count()
            nacimientos_ultimo_mes = Nacimiento.obtener_recientes(30)
            crias_sin_vacunar = Nacimiento.obtener_crias_sin_vacunar()
            
            return jsonify({
                'status': 'OK',
                'message': 'API funcionando correctamente',
                'timestamp': datetime.now().isoformat(),
                'database': {
                    'connected': True,
                    'usuarios_total': total_usuarios,
                    'usuarios_activos': usuarios_activos,
                    'roles': total_roles,
                    'haciendas_total': total_haciendas,
                    'haciendas_activas': haciendas_activas,
                    'animales_total': total_animales,
                    'animales_activos': animales_activos,
                    'estados_animal': total_estados,
                    'vacunas_total': total_vacunas,
                    'vacunas_activas': vacunas_activas,
                    'vacunaciones_total': total_vacunaciones,
                    'nacimientos_total': total_nacimientos,
                    'nacimientos_ultimo_mes': len(nacimientos_ultimo_mes),
                    'crias_pendientes_vacunacion': len(crias_sin_vacunar)
                },
                'services': {
                    'auth': 'active',
                    'usuarios': 'active',
                    'haciendas': 'active',
                    'animales': 'active',
                    'vacunacion': 'active',
                    'nacimientos': 'active',
                    'jwt': 'active'
                }
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'ERROR',
                'message': 'Error conectando a la base de datos',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'database': {
                    'connected': False
                }
            }), 500
    
    # Ruta para estadísticas básicas (pública) (CON NACIMIENTOS)
    @app.route('/api/stats', methods=['GET'])
    def stats():
        try:
            stats_data = {
                'usuarios': {
                    'total': Usuario.query.count(),
                    'activos': Usuario.query.filter_by(activo=True).count(),
                    'inactivos': Usuario.query.filter_by(activo=False).count()
                },
                'roles': {
                    'total': RolUsuario.query.count(),
                    'activos': RolUsuario.query.filter_by(activo=True).count()
                },
                'haciendas': {
                    'total': Hacienda.query.count(),
                    'activas': Hacienda.query.filter_by(activo=True).count(),
                    'inactivas': Hacienda.query.filter_by(activo=False).count()
                },
                'animales': {
                    'total': Animal.query.count(),
                    'machos': Animal.query.filter_by(sexo='Macho').count(),
                    'hembras': Animal.query.filter_by(sexo='Hembra').count(),
                    'preñadas': Animal.query.filter_by(sexo='Hembra', preñada=True).count()
                },
                'vacunacion': {
                    'total_vacunas': CatalogoVacuna.query.count(),
                    'vacunas_activas': CatalogoVacuna.query.filter_by(activo=True).count(),
                    'total_vacunaciones': VacunacionAnimal.query.count()
                },
                'nacimientos': {
                    'total_nacimientos': Nacimiento.query.count(),
                    'nacimientos_ultimo_mes': len(Nacimiento.obtener_recientes(30)),
                    'crias_sin_vacunar': len(Nacimiento.obtener_crias_sin_vacunar()),
                    'nacimientos_este_año': Nacimiento.query.filter(
                        Nacimiento.fecha_nacimiento >= datetime(datetime.now().year, 1, 1).date()
                    ).count()
                },
                'timestamp': datetime.now().isoformat()
            }
            return jsonify(stats_data), 200
        except Exception as e:
            return jsonify({
                'error': f'Error obteniendo estadísticas: {str(e)}',
                'status': 'error'
            }), 500
    
    return app

def inicializar_datos_por_defecto():
    """Inicializa roles, usuario administrador y datos de ejemplo (COMPLETO + NACIMIENTOS)"""
    try:
        print("🔧 Inicializando datos por defecto...")
        
        # Crear roles por defecto
        if RolUsuario.crear_roles_por_defecto():
            print("✅ Roles por defecto creados/verificados")
        
        # Crear usuario administrador por defecto
        if Usuario.crear_usuario_admin_defecto():
            print("✅ Usuario administrador por defecto creado/verificado")
        
        # Crear estados de animal por defecto
        if EstadoAnimal.crear_estados_por_defecto():
            print("✅ Estados de animal por defecto creados/verificados")
        
        # Crear vacunas por defecto
        if CatalogoVacuna.crear_vacunas_por_defecto():
            print("✅ Catálogo de vacunas por defecto creado/verificado")
        
        # Crear hacienda de ejemplo
        if Hacienda.crear_hacienda_ejemplo():
            print("✅ Hacienda de ejemplo creada/verificada")
        
        print("🎉 Inicialización completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")

if __name__ == '__main__':
    app = create_app()
    
    # Crear tablas y datos por defecto
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            print("✅ Base de datos conectada exitosamente")
            print("✅ Tablas creadas/verificadas (incluyendo nacimientos)")
            
            # Inicializar datos por defecto
            inicializar_datos_por_defecto()
            
        except Exception as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            print("💡 Verifica tu archivo .env y que MySQL esté corriendo")
            print("💡 Asegúrate de que la base de datos 'racionesbovino' exista")
            print(f"💡 Error específico: {str(e)}")
    
    print("\n" + "="*80)
    print("🚀 RACIONES BOVINO API - SISTEMA COMPLETO CON VACUNACIÓN Y NACIMIENTOS")
    print("="*80)
    print("📍 API disponible en: http://localhost:5000")
    print("🏥 Health check: http://localhost:5000/api/health")
    print("📊 Estadísticas: http://localhost:5000/api/stats")
    print("📚 Documentación: http://localhost:5000")
    print("")
    print("🔐 AUTENTICACIÓN:")
    print("   📧 Login: POST /api/auth/login")
    print("   📝 Registro: POST /api/auth/registrar")
    print("   🔑 Cambiar Password: PUT /api/auth/cambiar-password")
    print("")
    print("👤 GESTIÓN DE USUARIOS:")
    print("   👥 Lista: GET /api/usuarios/usuarios")
    print("   📊 Estadísticas: GET /api/usuarios/estadisticas")
    print("")
    print("🏡 GESTIÓN DE HACIENDAS:")
    print("   📋 Listar: GET /api/haciendas/")
    print("   ➕ Crear: POST /api/haciendas/")
    print("   📊 Estadísticas: GET /api/haciendas/estadisticas")
    print("")
    print("🐄 GESTIÓN DE ANIMALES:")
    print("   📋 Listar: GET /api/animales/")
    print("   ➕ Crear: POST /api/animales/")
    print("   📊 Estadísticas: GET /api/animales/estadisticas")
    print("   🤱 Preñadas: GET /api/animales/preñadas")
    print("")
    print("💉 SISTEMA DE VACUNACIÓN:")
    print("   📋 Catálogo: GET /api/vacunacion/vacunas/")
    print("   ➕ Crear Vacuna: POST /api/vacunacion/vacunas/")
    print("   💉 Aplicaciones: GET /api/vacunacion/aplicaciones/")
    print("   📝 Registrar: POST /api/vacunacion/aplicaciones/")
    print("   🐄 Por Animal: GET /api/vacunacion/animal/{id}")
    print("   📅 Próximas: GET /api/vacunacion/proximas-dosis")
    print("   ⚠️ Vencidas: GET /api/vacunacion/dosis-vencidas")
    print("   📊 Estadísticas: GET /api/vacunacion/estadisticas")
    print("   📅 Calendario: GET /api/vacunacion/reporte/calendario-vacunacion")
    print("")
    print("🍼 SISTEMA DE NACIMIENTOS (NUEVO):")
    print("   📋 Listar: GET /api/nacimientos/")
    print("   ➕ Registrar: POST /api/nacimientos/")
    print("   📝 Actualizar: PUT /api/nacimientos/{id}")
    print("   🐄 Por Madre: GET /api/nacimientos/por-madre/{id}")
    print("   🐂 Por Padre: GET /api/nacimientos/por-padre/{id}")
    print("   🆕 Recientes: GET /api/nacimientos/recientes")
    print("   💉 Sin Vacunar: GET /api/nacimientos/crias-sin-vacunar")
    print("   ✅ Marcar Vacunas: PUT /api/nacimientos/{id}/marcar-vacunas")
    print("   🏡 Por Hacienda: GET /api/nacimientos/por-hacienda/{id}")
    print("   📊 Estadísticas: GET /api/nacimientos/estadisticas")
    print("   📈 Reporte: GET /api/nacimientos/reporte/resumen")
    print("   🔍 Buscar: GET /api/nacimientos/buscar")
    print("   ✔️ Validar: POST /api/nacimientos/validar-animales")
    print("")
    print("👤 USUARIO ADMIN POR DEFECTO:")
    print("   📧 Email: admin@racionesbovino.com")
    print("   🔑 Password: admin123")
    print("   🎯 Rol: Administrador")
    print("")
    print("🏡 HACIENDA DE EJEMPLO:")
    print("   🏷️ NIT: 900123456-1")
    print("   📛 Nombre: Hacienda La Esperanza")
    print("   👤 Propietario: Juan Carlos Ejemplo")
    print("")
    print("📋 ESTADOS DE ANIMAL:")
    print("   ✅ Activo - Animal en condiciones normales")
    print("   💰 Vendido - Animal vendido o transferido")
    print("   ☠️ Muerto - Animal fallecido")
    print("   🏥 Enfermo - Animal con problemas de salud")
    print("   🔒 Cuarentena - Animal aislado por precaución")
    print("")
    print("💉 VACUNAS POR DEFECTO:")
    print("   🦠 Aftosa - Cada 6 meses")
    print("   🦠 Brucelosis - Anual")
    print("   🦠 Carbón Sintomático - Anual")
    print("   🦠 Rabia - Anual")
    print("   🦠 IBR/DVB - Anual")
    print("   🦠 Clostridiosis - Anual")
    print("")
    print("🍼 TIPOS DE PARTO:")
    print("   🌱 Natural - Parto sin asistencia")
    print("   🤝 Asistido - Con asistencia veterinaria")
    print("   ⚕️ Cesárea - Parto quirúrgico")
    print("")
    print("✨ FUNCIONALIDADES COMPLETAMENTE INTEGRADAS:")
    print("   ✅ Autenticación JWT robusta")
    print("   ✅ Gestión completa de usuarios con roles")
    print("   ✅ CRUD completo de haciendas")
    print("   ✅ CRUD completo de animales")
    print("   ✅ Seguimiento reproductivo bovino")
    print("   ✅ Sistema completo de vacunación")
    print("   ✅ Catálogo de vacunas personalizable")
    print("   ✅ Calendario de vacunación inteligente")
    print("   ✅ Alertas automáticas de dosis vencidas")
    print("   ✅ SISTEMA COMPLETO DE NACIMIENTOS (NUEVO)")
    print("   ✅ Registro y seguimiento de partos")
    print("   ✅ Control genealógico (madre/padre)")
    print("   ✅ Alertas de vacunación para crías")
    print("   ✅ Estadísticas reproductivas avanzadas")
    print("   ✅ Reportes de productividad")
    print("   ✅ Validaciones de compatibilidad")
    print("   ✅ Sistema de permisos granular")
    print("   ✅ Validaciones de negocio robustas")
    print("   ✅ API REST estándar y escalable")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)