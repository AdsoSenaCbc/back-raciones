# routes/nrc.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from services.nrc_service import NrcService

# Crear blueprint para NRC
nrc_bp = Blueprint('nrc', __name__)

# ===============================
# LACTANCIA BASE
# ===============================

@nrc_bp.route('/lactancia-base/', methods=['GET'])
@jwt_required()
def listar_nrc_lactancia_base():
    """
    Lista registros de NRC lactancia base
    """
    try:
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        resultado, codigo = NrcService.listar_nrc_lactancia_base(pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar NRC lactancia base: {str(e)}',
            'status': 'error'
        }), 500

@nrc_bp.route('/lactancia-base/', methods=['POST'])
@jwt_required()
def crear_nrc_lactancia_base():
    """
    Crea un nuevo registro de NRC lactancia base
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = NrcService.crear_nrc_lactancia_base(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear NRC lactancia base: {str(e)}',
            'status': 'error'
        }), 500

@nrc_bp.route('/lactancia-base/requerimientos/<float:peso_kg>', methods=['GET'])
@jwt_required()
def obtener_requerimientos_lactancia(peso_kg):
    """
    Obtiene requerimientos de lactancia para un peso específico
    """
    try:
        resultado, codigo = NrcService.obtener_requerimientos_lactancia(peso_kg)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener requerimientos: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# PRODUCCIÓN LECHE
# ===============================

@nrc_bp.route('/produccion-leche/', methods=['POST'])
@jwt_required()
def crear_nrc_produccion_leche():
    """
    Crea un nuevo registro de NRC producción leche
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = NrcService.crear_nrc_produccion_leche(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear NRC producción leche: {str(e)}',
            'status': 'error'
        }), 500

@nrc_bp.route('/produccion-leche/requerimientos/<float:porcentaje_grasa>', methods=['GET'])
@jwt_required()
def obtener_requerimientos_produccion(porcentaje_grasa):
    """
    Obtiene requerimientos por kg de leche según % grasa
    """
    try:
        resultado, codigo = NrcService.obtener_requerimientos_produccion(porcentaje_grasa)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener requerimientos: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# GESTACIÓN
# ===============================

@nrc_bp.route('/gestacion/requerimientos/<float:peso_kg>', methods=['GET'])
@jwt_required()
def obtener_requerimientos_gestacion(peso_kg):
    """
    Obtiene requerimientos adicionales por gestación
    """
    try:
        resultado, codigo = NrcService.obtener_requerimientos_gestacion(peso_kg)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener requerimientos de gestación: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# CEBA
# ===============================

@nrc_bp.route('/ceba/', methods=['GET'])
@jwt_required()
def listar_nrc_ceba():
    """
    Lista todos los registros de NRC para ceba
    """
    try:
        resultado, codigo = NrcService.listar_nrc_ceba()
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar NRC ceba: {str(e)}',
            'status': 'error'
        }), 500

@nrc_bp.route('/ceba/requerimientos/<float:peso_kg>', methods=['GET'])
@jwt_required()
def obtener_requerimientos_ceba(peso_kg):
    """
    Obtiene requerimientos para ceba
    """
    try:
        gdp_objetivo = request.args.get('gdp_objetivo', type=float)
        resultado, codigo = NrcService.obtener_requerimientos_ceba(peso_kg, gdp_objetivo)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener requerimientos de ceba: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# CALCULADORA INTEGRADA
# ===============================

@nrc_bp.route('/calcular-lactancia', methods=['POST'])
@jwt_required()
def calcular_requerimientos_lactancia():
    """
    Calcula requerimientos completos para una vaca en lactancia
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        # Validar campos requeridos
        campos_requeridos = ['peso_kg', 'produccion_leche_kg', 'porcentaje_grasa']
        campos_faltantes = [campo for campo in campos_requeridos if not data.get(campo)]
        
        if campos_faltantes:
            return jsonify({
                'error': f'Campos requeridos faltantes: {", ".join(campos_faltantes)}',
                'status': 'error'
            }), 400
        
        resultado, codigo = NrcService.calcular_requerimientos_lactancia_completos(
            peso_kg=data['peso_kg'],
            produccion_leche_kg=data['produccion_leche_kg'],
            porcentaje_grasa=data['porcentaje_grasa'],
            dias_gestacion=data.get('dias_gestacion', 0)
        )
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al calcular requerimientos: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# UTILIDADES
# ===============================

@nrc_bp.route('/rangos-peso', methods=['GET'])
@jwt_required()
def obtener_rangos_peso():
    """
    Obtiene los rangos de peso disponibles en las tablas NRC
    """
    try:
        from models import NrcLactanciaBase, NrcGestacion, NrcCeba
        
        # Rangos de lactancia
        lactancia_min = NrcLactanciaBase.query.with_entities(
            db.func.min(NrcLactanciaBase.peso_kg)
        ).scalar() or 0
        
        lactancia_max = NrcLactanciaBase.query.with_entities(
            db.func.max(NrcLactanciaBase.peso_kg)
        ).scalar() or 0
        
        # Rangos de gestación
        gestacion_min = NrcGestacion.query.with_entities(
            db.func.min(NrcGestacion.peso_kg)
        ).scalar() or 0
        
        gestacion_max = NrcGestacion.query.with_entities(
            db.func.max(NrcGestacion.peso_kg)
        ).scalar() or 0
        
        # Rangos de ceba
        ceba_min = NrcCeba.query.with_entities(
            db.func.min(NrcCeba.peso_minimo)
        ).scalar() or 0
        
        ceba_max = NrcCeba.query.with_entities(
            db.func.max(NrcCeba.peso_maximo)
        ).scalar() or 0
        
        return jsonify({
            'rangos': {
                'lactancia': {
                    'peso_min': float(lactancia_min),
                    'peso_max': float(lactancia_max)
                },
                'gestacion': {
                    'peso_min': float(gestacion_min),
                    'peso_max': float(gestacion_max)
                },
                'ceba': {
                    'peso_min': float(ceba_min),
                    'peso_max': float(ceba_max)
                }
            },
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener rangos: {str(e)}',
            'status': 'error'
        }), 500

@nrc_bp.route('/validar-parametros', methods=['POST'])
@jwt_required()
def validar_parametros():
    """
    Valida si los parámetros están dentro de los rangos NRC disponibles
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        validaciones = {
            'peso_valido': False,
            'produccion_valida': False,
            'grasa_valida': False,
            'gdp_valida': False,
            'mensajes': []
        }
        
        # Validar peso para lactancia
        if data.get('peso_kg') and data.get('tipo') == 'lactancia':
            from models import NrcLactanciaBase
            nrc = NrcLactanciaBase.obtener_por_peso(data['peso_kg'])
            validaciones['peso_valido'] = nrc is not None
            if not validaciones['peso_valido']:
                validaciones['mensajes'].append('Peso fuera del rango de tablas NRC para lactancia')
        
        # Validar peso para ceba
        if data.get('peso_kg') and data.get('tipo') == 'ceba':
            from models import NrcCeba
            nrc = NrcCeba.obtener_por_peso(data['peso_kg'])
            validaciones['peso_valido'] = nrc is not None
            if not validaciones['peso_valido']:
                validaciones['mensajes'].append('Peso fuera del rango de tablas NRC para ceba')
        
        # Validar porcentaje de grasa
        if data.get('porcentaje_grasa'):
            grasa = data['porcentaje_grasa']
            validaciones['grasa_valida'] = 2.0 <= grasa <= 6.0
            if not validaciones['grasa_valida']:
                validaciones['mensajes'].append('Porcentaje de grasa debe estar entre 2.0% y 6.0%')
        
        # Validar producción de leche
        if data.get('produccion_leche_kg'):
            produccion = data['produccion_leche_kg']
            validaciones['produccion_valida'] = 5.0 <= produccion <= 60.0
            if not validaciones['produccion_valida']:
                validaciones['mensajes'].append('Producción de leche debe estar entre 5 y 60 litros/día')
        
        # Validar GDP
        if data.get('gdp_objetivo'):
            gdp = data['gdp_objetivo']
            validaciones['gdp_valida'] = 0.3 <= gdp <= 2.5
            if not validaciones['gdp_valida']:
                validaciones['mensajes'].append('GDP objetivo debe estar entre 0.3 y 2.5 kg/día')
        
        return jsonify({
            'validaciones': validaciones,
            'parametros_validos': all([
                validaciones.get('peso_valido', True),
                validaciones.get('produccion_valida', True),
                validaciones.get('grasa_valida', True),
                validaciones.get('gdp_valida', True)
            ]),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar parámetros: {str(e)}',
            'status': 'error'
        }), 500