# routes/ingredientes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ingredientes_service import IngredientesService

# Crear blueprint para ingredientes
ingredientes_bp = Blueprint('ingredientes', __name__)

# ===============================
# GESTIÓN DE DEPARTAMENTOS Y MUNICIPIOS
# ===============================

@ingredientes_bp.route('/departamentos/', methods=['GET'])
@jwt_required()
def listar_departamentos():
    """
    Lista todos los departamentos
    """
    try:
        resultado, codigo = IngredientesService.listar_departamentos()
        return jsonify(resultado), codigo
    except Exception as e:
        return jsonify({
            'error': f'Error al listar departamentos: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/departamentos/<int:departamento_id>/municipios', methods=['GET'])
@jwt_required()
def obtener_municipios_por_departamento(departamento_id):
    """
    Obtiene municipios de un departamento específico
    """
    try:
        resultado, codigo = IngredientesService.obtener_municipios_por_departamento(departamento_id)
        return jsonify(resultado), codigo
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener municipios: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/municipios/', methods=['POST'])
@jwt_required()
def crear_municipio():
    """
    Crea un nuevo municipio
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = IngredientesService.crear_municipio(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear municipio: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# GESTIÓN DE CONSULTAS BROMATOLÓGICAS
# ===============================

@ingredientes_bp.route('/consultas-bromatologicas/', methods=['GET'])
@jwt_required()
def listar_consultas_bromatologicas():
    """
    Lista consultas bromatológicas con filtros
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        # Parámetros de filtro
        filtros = {}
        
        if request.args.get('departamento_id'):
            filtros['departamento_id'] = request.args.get('departamento_id', type=int)
        
        if request.args.get('municipio_id'):
            filtros['municipio_id'] = request.args.get('municipio_id', type=int)
        
        activo = request.args.get('activo')
        if activo is not None:
            filtros['activo'] = activo.lower() == 'true'
        
        if request.args.get('laboratorio'):
            filtros['laboratorio'] = request.args.get('laboratorio').strip()
        
        resultado, codigo = IngredientesService.listar_consultas_bromatologicas(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar consultas: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/consultas-bromatologicas/', methods=['POST'])
@jwt_required()
def crear_consulta_bromatologica():
    """
    Crea una nueva consulta bromatológica
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = IngredientesService.crear_consulta_bromatologica(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear consulta: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# GESTIÓN DE INGREDIENTES
# ===============================

@ingredientes_bp.route('/ingredientes/', methods=['GET'])
@jwt_required()
def listar_ingredientes():
    """
    Lista ingredientes con filtros y paginación
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        # Parámetros de filtro
        filtros = {}
        
        if request.args.get('tipo_ingrediente'):
            filtros['tipo_ingrediente'] = request.args.get('tipo_ingrediente').strip()
        
        disponible = request.args.get('disponible')
        if disponible is not None:
            filtros['disponible'] = disponible.lower() == 'true'
        
        if request.args.get('buscar'):
            filtros['buscar'] = request.args.get('buscar').strip()
        
        resultado, codigo = IngredientesService.listar_ingredientes(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar ingredientes: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/ingredientes/', methods=['POST'])
@jwt_required()
def crear_ingrediente():
    """
    Crea un nuevo ingrediente
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = IngredientesService.crear_ingrediente(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear ingrediente: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/ingredientes/<int:ingrediente_id>', methods=['GET'])
@jwt_required()
def obtener_ingrediente(ingrediente_id):
    """
    Obtiene un ingrediente específico
    """
    try:
        include_caracteristicas = request.args.get('incluir_caracteristicas', 'false').lower() == 'true'
        resultado, codigo = IngredientesService.obtener_ingrediente(ingrediente_id, include_caracteristicas)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener ingrediente: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/ingredientes/<int:ingrediente_id>', methods=['PUT'])
@jwt_required()
def actualizar_ingrediente(ingrediente_id):
    """
    Actualiza un ingrediente existente
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        resultado, codigo = IngredientesService.actualizar_ingrediente(ingrediente_id, data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar ingrediente: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/ingredientes/disponibles', methods=['GET'])
@jwt_required()
def obtener_ingredientes_disponibles():
    """
    Obtiene ingredientes disponibles para formulación de raciones
    """
    try:
        resultado, codigo = IngredientesService.obtener_ingredientes_disponibles()
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener ingredientes disponibles: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/ingredientes/tipos', methods=['GET'])
@jwt_required()
def obtener_tipos_ingredientes():
    """
    Obtiene los tipos de ingredientes disponibles
    """
    try:
        tipos = [
            {'valor': 'Forraje', 'nombre': 'Forraje'},
            {'valor': 'Concentrado', 'nombre': 'Concentrado'},
            {'valor': 'Suplemento', 'nombre': 'Suplemento'},
            {'valor': 'Mineral', 'nombre': 'Mineral'}
        ]
        
        return jsonify({
            'tipos_ingredientes': tipos,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener tipos: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# GESTIÓN DE CARACTERÍSTICAS NUTRICIONALES
# ===============================

@ingredientes_bp.route('/caracteristicas-nutricionales/', methods=['POST'])
@jwt_required()
def crear_caracteristica_nutricional():
    """
    Crea una nueva característica nutricional
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = IngredientesService.crear_caracteristica_nutricional(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear análisis nutricional: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/ingredientes/<int:ingrediente_id>/caracteristicas', methods=['GET'])
@jwt_required()
def listar_caracteristicas_por_ingrediente(ingrediente_id):
    """
    Lista todas las características nutricionales de un ingrediente
    """
    try:
        resultado, codigo = IngredientesService.listar_caracteristicas_por_ingrediente(ingrediente_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener características: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# BÚSQUEDAS Y ESTADÍSTICAS
# ===============================

@ingredientes_bp.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_ingredientes():
    """
    Búsqueda general de ingredientes
    """
    try:
        termino = request.args.get('q', '').strip()
        
        if not termino:
            return jsonify({
                'error': 'Se requiere un término de búsqueda (parámetro q)',
                'status': 'error'
            }), 400
        
        if len(termino) < 2:
            return jsonify({
                'error': 'El término de búsqueda debe tener al menos 2 caracteres',
                'status': 'error'
            }), 400
        
        # Usar el listado con filtro de búsqueda
        filtros = {'buscar': termino}
        resultado, codigo = IngredientesService.listar_ingredientes(filtros, 1, 100)
        
        if codigo == 200:
            return jsonify({
                'ingredientes': resultado['ingredientes'],
                'total': resultado['total'],
                'termino_busqueda': termino,
                'status': 'success'
            }), 200
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error en búsqueda: {str(e)}',
            'status': 'error'
        }), 500

@ingredientes_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas_ingredientes():
    """
    Obtiene estadísticas de ingredientes
    """
    try:
        resultado, codigo = IngredientesService.obtener_estadisticas_ingredientes()
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# UTILIDADES Y VALIDACIONES
# ===============================

@ingredientes_bp.route('/validar-nombre', methods=['POST'])
@jwt_required()
def validar_nombre_ingrediente():
    """
    Valida un nombre de ingrediente y verifica disponibilidad
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('nombre_ingrediente'):
            return jsonify({
                'error': 'Nombre del ingrediente es requerido',
                'status': 'error'
            }), 400
        
        nombre = data['nombre_ingrediente'].strip()
        ingrediente_id_excluir = data.get('excluir_id')
        
        # Validaciones básicas
        if len(nombre) < 3:
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': 'El nombre debe tener al menos 3 caracteres',
                'status': 'error'
            }), 400
        
        if len(nombre) > 100:
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': 'El nombre no puede exceder 100 caracteres',
                'status': 'error'
            }), 400
        
        # Verificar disponibilidad
        from models import Ingrediente
        ingrediente_existente = Ingrediente.query.filter_by(nombre_ingrediente=nombre).first()
        disponible = True
        
        if ingrediente_existente:
            if not ingrediente_id_excluir or ingrediente_existente.idingrediente != ingrediente_id_excluir:
                disponible = False
        
        return jsonify({
            'valido': True,
            'disponible': disponible,
            'mensaje': 'Nombre disponible' if disponible else 'Nombre ya registrado',
            'nombre_validado': nombre,
            'ingrediente_existente': ingrediente_existente.to_dict() if ingrediente_existente and not disponible else None,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar nombre: {str(e)}',
            'status': 'error'
        }), 500