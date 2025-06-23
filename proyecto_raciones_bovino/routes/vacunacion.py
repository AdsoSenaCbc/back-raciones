from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from services.vacunacion_service import VacunacionService

# Crear blueprint para vacunación
vacunacion_bp = Blueprint('vacunacion', __name__)

# ===============================
# ENDPOINTS DEL CATÁLOGO DE VACUNAS
# ===============================

@vacunacion_bp.route('/vacunas/', methods=['GET'])
@jwt_required()
def listar_vacunas():
    """
    Lista vacunas del catálogo con filtros y paginación
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        # Parámetros de filtro
        filtros = {}
        
        # Filtro por estado activo
        activo = request.args.get('activo')
        if activo is not None:
            filtros['activo'] = activo.lower() == 'true'
        
        # Búsqueda general
        if request.args.get('buscar'):
            filtros['buscar'] = request.args.get('buscar').strip()
        
        resultado, codigo = VacunacionService.listar_vacunas(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar vacunas: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/vacunas/', methods=['POST'])
@jwt_required()
def crear_vacuna():
    """
    Crea una nueva vacuna en el catálogo
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = VacunacionService.crear_vacuna(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear vacuna: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/vacunas/<int:vacuna_id>', methods=['PUT'])
@jwt_required()
def actualizar_vacuna(vacuna_id):
    """
    Actualiza una vacuna del catálogo
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        resultado, codigo = VacunacionService.actualizar_vacuna(vacuna_id, data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar vacuna: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/vacunas/activas', methods=['GET'])
@jwt_required()
def obtener_vacunas_activas():
    """
    Obtiene solo las vacunas activas
    """
    try:
        resultado, codigo = VacunacionService.obtener_vacunas_activas()
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener vacunas activas: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# ENDPOINTS DE VACUNACIONES
# ===============================

@vacunacion_bp.route('/aplicaciones/', methods=['GET'])
@jwt_required()
def listar_vacunaciones():
    """
    Lista vacunaciones con filtros y paginación
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        # Parámetros de filtro
        filtros = {}
        
        if request.args.get('hacienda_id'):
            filtros['hacienda_id'] = request.args.get('hacienda_id', type=int)
        
        if request.args.get('animal_id'):
            filtros['animal_id'] = request.args.get('animal_id', type=int)
        
        if request.args.get('vacuna_id'):
            filtros['vacuna_id'] = request.args.get('vacuna_id', type=int)
        
        if request.args.get('fecha_desde'):
            filtros['fecha_desde'] = request.args.get('fecha_desde')
        
        if request.args.get('fecha_hasta'):
            filtros['fecha_hasta'] = request.args.get('fecha_hasta')
        
        if request.args.get('veterinario'):
            filtros['veterinario'] = request.args.get('veterinario').strip()
        
        if request.args.get('buscar'):
            filtros['buscar'] = request.args.get('buscar').strip()
        
        resultado, codigo = VacunacionService.listar_vacunaciones(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar vacunaciones: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/aplicaciones/', methods=['POST'])
@jwt_required()
def registrar_vacunacion():
    """
    Registra una nueva vacunación
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = VacunacionService.registrar_vacunacion(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al registrar vacunación: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/aplicaciones/<int:vacunacion_id>', methods=['DELETE'])
@jwt_required()
def eliminar_vacunacion(vacunacion_id):
    """
    Elimina una vacunación (solo administradores)
    """
    try:
        current_user_id = get_jwt_identity()
        
        resultado, codigo = VacunacionService.eliminar_vacunacion(vacunacion_id, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar vacunación: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# ENDPOINTS DE CONSULTAS ESPECÍFICAS
# ===============================

@vacunacion_bp.route('/animal/<int:animal_id>', methods=['GET'])
@jwt_required()
def obtener_vacunaciones_animal(animal_id):
    """
    Obtiene el historial de vacunaciones de un animal específico
    """
    try:
        resultado, codigo = VacunacionService.obtener_vacunaciones_animal(animal_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener vacunaciones del animal: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/proximas-dosis', methods=['GET'])
@jwt_required()
def obtener_proximas_dosis():
    """
    Obtiene animales que necesitan próximas dosis
    """
    try:
        dias_adelante = request.args.get('dias', 30, type=int)
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        # Validar parámetros
        if dias_adelante < 1 or dias_adelante > 365:
            return jsonify({
                'error': 'Los días deben estar entre 1 y 365',
                'status': 'error'
            }), 400
        
        resultado, codigo = VacunacionService.obtener_proximas_dosis(dias_adelante, hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener próximas dosis: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/dosis-vencidas', methods=['GET'])
@jwt_required()
def obtener_dosis_vencidas():
    """
    Obtiene vacunaciones con dosis vencidas
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        resultado, codigo = VacunacionService.obtener_vencidas(hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener dosis vencidas: {str(e)}',
            'status': 'error'
        }), 500

@vacunacion_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas_vacunacion():
    """
    Obtiene estadísticas de vacunación
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        resultado, codigo = VacunacionService.obtener_estadisticas_vacunacion(hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# ENDPOINTS DE REPORTES
# ===============================

@vacunacion_bp.route('/reporte/calendario-vacunacion', methods=['GET'])
@jwt_required()
def obtener_calendario_vacunacion():
    """
    Obtiene calendario de vacunación (próximas y vencidas)
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        # Obtener próximas dosis (próximos 60 días)
        proximas, _ = VacunacionService.obtener_proximas_dosis(60, hacienda_id)
        
        # Obtener dosis vencidas
        vencidas, _ = VacunacionService.obtener_vencidas(hacienda_id)
        
        # Organizar por urgencia
        urgentes = []  # Vencidas o próximas 7 días
        cercanas = []  # Próximas 8-30 días
        programadas = []  # Próximas 31-60 días
        
        hoy = date.today()
        limite_urgente = hoy + timedelta(days=7)
        limite_cercano = hoy + timedelta(days=30)
        
        # Clasificar vencidas como urgentes
        if vencidas['status'] == 'success':
            urgentes.extend(vencidas['dosis_vencidas'])
        
        # Clasificar próximas por urgencia
        if proximas['status'] == 'success':
            for vacunacion in proximas['proximas_dosis']:
                if vacunacion.get('proxima_dosis'):
                    try:
                        fecha_proxima = datetime.strptime(vacunacion['proxima_dosis'], '%Y-%m-%d').date()
                        if fecha_proxima <= limite_urgente:
                            urgentes.append(vacunacion)
                        elif fecha_proxima <= limite_cercano:
                            cercanas.append(vacunacion)
                        else:
                            programadas.append(vacunacion)
                    except:
                        programadas.append(vacunacion)
        
        return jsonify({
            'calendario': {
                'urgentes': urgentes,
                'cercanas': cercanas,
                'programadas': programadas
            },
            'resumen': {
                'total_urgentes': len(urgentes),
                'total_cercanas': len(cercanas),
                'total_programadas': len(programadas)
            },
            'hacienda_id': hacienda_id,
            'fecha_consulta': hoy.isoformat(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener calendario de vacunación: {str(e)}',
            'status': 'error'
        }), 500