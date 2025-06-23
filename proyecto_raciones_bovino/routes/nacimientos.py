from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.nacimiento_service import NacimientoService

# Crear blueprint para nacimientos
nacimientos_bp = Blueprint('nacimientos', __name__)

# ===============================
#  CONSULTAR NACIMIENTOS
# ===============================

@nacimientos_bp.route('/', methods=['GET'])
@jwt_required()
def listar_nacimientos():
    """
    Lista nacimientos con filtros y paginación
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        # Parámetros de filtro
        filtros = {}
        
        if request.args.get('hacienda_id'):
            filtros['hacienda_id'] = request.args.get('hacienda_id', type=int)
        
        if request.args.get('madre_id'):
            filtros['madre_id'] = request.args.get('madre_id', type=int)
        
        if request.args.get('padre_id'):
            filtros['padre_id'] = request.args.get('padre_id', type=int)
        
        if request.args.get('tipo_parto'):
            filtros['tipo_parto'] = request.args.get('tipo_parto').strip()
        
        if request.args.get('fecha_desde'):
            filtros['fecha_desde'] = request.args.get('fecha_desde')
        
        if request.args.get('fecha_hasta'):
            filtros['fecha_hasta'] = request.args.get('fecha_hasta')
        
        vacunas_aplicadas = request.args.get('vacunas_aplicadas')
        if vacunas_aplicadas is not None:
            filtros['vacunas_aplicadas'] = vacunas_aplicadas.lower() == 'true'
        
        if request.args.get('buscar'):
            filtros['buscar'] = request.args.get('buscar').strip()
        
        resultado, codigo = NacimientoService.listar_nacimientos(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar nacimientos: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/<int:nacimiento_id>', methods=['GET'])
@jwt_required()
def obtener_nacimiento(nacimiento_id):
    """
    Obtiene un nacimiento específico por ID
    """
    try:
        resultado, codigo = NacimientoService.obtener_nacimiento(nacimiento_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener nacimiento: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/por-madre/<int:madre_id>', methods=['GET'])
@jwt_required()
def obtener_nacimientos_por_madre(madre_id):
    """
    Obtiene todos los nacimientos de una madre específica
    """
    try:
        resultado, codigo = NacimientoService.obtener_nacimientos_por_madre(madre_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener nacimientos de la madre: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/por-padre/<int:padre_id>', methods=['GET'])
@jwt_required()
def obtener_nacimientos_por_padre(padre_id):
    """
    Obtiene todos los nacimientos de un padre específico
    """
    try:
        resultado, codigo = NacimientoService.obtener_nacimientos_por_padre(padre_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener nacimientos del padre: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/por-hacienda/<int:hacienda_id>', methods=['GET'])
@jwt_required()
def listar_nacimientos_por_hacienda(hacienda_id):
    """
    Lista nacimientos de una hacienda específica
    """
    try:
        filtros = {'hacienda_id': hacienda_id}
        
        # Filtros adicionales
        if request.args.get('tipo_parto'):
            filtros['tipo_parto'] = request.args.get('tipo_parto').strip()
        
        if request.args.get('fecha_desde'):
            filtros['fecha_desde'] = request.args.get('fecha_desde')
        
        if request.args.get('fecha_hasta'):
            filtros['fecha_hasta'] = request.args.get('fecha_hasta')
        
        # Paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 100, type=int), 200)
        
        resultado, codigo = NacimientoService.listar_nacimientos(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar nacimientos por hacienda: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/recientes', methods=['GET'])
@jwt_required()
def obtener_nacimientos_recientes():
    """
    Obtiene nacimientos recientes
    """
    try:
        dias = request.args.get('dias', 30, type=int)
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        resultado, codigo = NacimientoService.obtener_nacimientos_recientes(dias, hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener nacimientos recientes: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/crias-sin-vacunar', methods=['GET'])
@jwt_required()
def obtener_crias_sin_vacunar():
    """
    Obtiene crías que necesitan vacunación inicial
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        resultado, codigo = NacimientoService.obtener_crias_sin_vacunar(hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener crías sin vacunar: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# 2. AGREGAR NACIMIENTOS
# ===============================

@nacimientos_bp.route('/', methods=['POST'])
@jwt_required()
def crear_nacimiento():
    """
    Registra un nuevo nacimiento
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = NacimientoService.crear_nacimiento(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear nacimiento: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# 3. EDITAR NACIMIENTOS
# ===============================

@nacimientos_bp.route('/<int:nacimiento_id>', methods=['PUT'])
@jwt_required()
def actualizar_nacimiento(nacimiento_id):
    """
    Actualiza un nacimiento existente
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        resultado, codigo = NacimientoService.actualizar_nacimiento(nacimiento_id, data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar nacimiento: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/<int:nacimiento_id>/marcar-vacunas', methods=['PUT'])
@jwt_required()
def marcar_vacunas_aplicadas(nacimiento_id):
    """
    Marca las vacunas como aplicadas en un nacimiento
    """
    try:
        current_user_id = get_jwt_identity()
        
        resultado, codigo = NacimientoService.marcar_vacunas_aplicadas(nacimiento_id, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al marcar vacunas: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# 4. ELIMINAR NACIMIENTOS
# ===============================

@nacimientos_bp.route('/<int:nacimiento_id>', methods=['DELETE'])
@jwt_required()
def eliminar_nacimiento(nacimiento_id):
    """
    Elimina un nacimiento (solo administradores)
    """
    try:
        current_user_id = get_jwt_identity()
        
        resultado, codigo = NacimientoService.eliminar_nacimiento(nacimiento_id, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar nacimiento: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# ENDPOINTS ADICIONALES
# ===============================

@nacimientos_bp.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_nacimientos():
    """
    Búsqueda general de nacimientos
    """
    try:
        termino = request.args.get('q', '').strip()
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        if not termino:
            return jsonify({
                'error': 'Se requiere un término de búsqueda (parámetro q)',
                'status': 'error'
            }), 400
        
        resultado, codigo = NacimientoService.buscar_nacimientos(termino, hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error en búsqueda: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas_nacimientos():
    """
    Obtiene estadísticas de nacimientos
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        resultado, codigo = NacimientoService.obtener_estadisticas_nacimientos(hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/tipos-parto', methods=['GET'])
@jwt_required()
def obtener_tipos_parto():
    """
    Obtiene los tipos de parto disponibles
    """
    try:
        tipos = [
            {'valor': 'Natural', 'nombre': 'Natural'},
            {'valor': 'Asistido', 'nombre': 'Asistido'},
            {'valor': 'Cesarea', 'nombre': 'Cesárea'}
        ]
        
        return jsonify({
            'tipos_parto': tipos,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener tipos de parto: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/validar-animales', methods=['POST'])
@jwt_required()
def validar_animales_nacimiento():
    """
    Valida la compatibilidad de animales para un nacimiento
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('idanimal_cria') or not data.get('idanimal_madre'):
            return jsonify({
                'error': 'ID de cría y madre son requeridos',
                'status': 'error'
            }), 400
        
        from models.nacimiento import Nacimiento
        errores = Nacimiento.verificar_animales_compatibles(
            data['idanimal_cria'],
            data['idanimal_madre'],
            data.get('idanimal_padre')
        )
        
        if errores:
            return jsonify({
                'valido': False,
                'errores': errores,
                'status': 'error'
            }), 400
        
        return jsonify({
            'valido': True,
            'mensaje': 'Animales compatibles',
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar animales: {str(e)}',
            'status': 'error'
        }), 500

@nacimientos_bp.route('/reporte/resumen', methods=['GET'])
@jwt_required()
def obtener_reporte_resumen():
    """
    Obtiene un reporte resumen de nacimientos
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        # Obtener estadísticas
        estadisticas, codigo = NacimientoService.obtener_estadisticas_nacimientos(hacienda_id)
        if codigo != 200:
            return jsonify(estadisticas), codigo
        
        # Obtener nacimientos recientes
        recientes, _ = NacimientoService.obtener_nacimientos_recientes(30, hacienda_id)
        
        # Obtener crías sin vacunar
        sin_vacunar, _ = NacimientoService.obtener_crias_sin_vacunar(hacienda_id)
        
        reporte = {
            'resumen': {
                'hacienda_id': hacienda_id,
                'fecha_reporte': request.args.get('fecha', ''),
                'estadisticas': estadisticas.get('estadisticas', {}),
                'nacimientos_recientes': len(recientes.get('nacimientos_recientes', [])),
                'crias_sin_vacunar': len(sin_vacunar.get('crias_sin_vacunar', [])),
                'alerta_vacunacion': len(sin_vacunar.get('crias_sin_vacunar', [])) > 0
            },
            'detalles': {
                'recientes': recientes.get('nacimientos_recientes', [])[:5],  # Solo los 5 más recientes
                'sin_vacunar': sin_vacunar.get('crias_sin_vacunar', [])[:5]   # Solo los 5 más urgentes
            },
            'status': 'success'
        }
        
        return jsonify(reporte), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al generar reporte: {str(e)}',
            'status': 'error'
        }), 500