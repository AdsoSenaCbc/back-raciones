from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.animal_service import AnimalService

# Crear blueprint para animales
animales_bp = Blueprint('animales', __name__)

@animales_bp.route('/', methods=['GET'])
@jwt_required()
def listar_animales():
    """
    Lista animales con filtros y paginación
    ---
    Obtiene la lista de animales con opciones de filtrado
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)  # Máximo 100
        
        # Parámetros de filtro
        filtros = {}
        
        # Filtro por hacienda
        if request.args.get('hacienda_id'):
            filtros['hacienda_id'] = request.args.get('hacienda_id', type=int)
        
        # Filtro por estado
        if request.args.get('estado_id'):
            filtros['estado_id'] = request.args.get('estado_id', type=int)
        
        # Filtro por sexo
        if request.args.get('sexo'):
            filtros['sexo'] = request.args.get('sexo').strip()
        
        # Filtro por raza
        if request.args.get('raza'):
            filtros['raza'] = request.args.get('raza').strip()
        
        # Filtro por preñada
        preñada = request.args.get('preñada')
        if preñada is not None:
            filtros['preñada'] = preñada.lower() == 'true'
        
        # Búsqueda general
        if request.args.get('buscar'):
            filtros['buscar'] = request.args.get('buscar').strip()
        
        resultado, codigo = AnimalService.listar_animales(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar animales: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/', methods=['POST'])
@jwt_required()
def crear_animal():
    """
    Crea un nuevo animal
    ---
    Permite a administradores e instructores crear animales
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = AnimalService.crear_animal(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear animal: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/<int:animal_id>', methods=['GET'])
@jwt_required()
def obtener_animal(animal_id):
    """
    Obtiene un animal específico por ID
    ---
    Retorna los datos completos de un animal
    """
    try:
        resultado, codigo = AnimalService.obtener_animal(animal_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener animal: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/<int:animal_id>', methods=['PUT'])
@jwt_required()
def actualizar_animal(animal_id):
    """
    Actualiza un animal existente
    ---
    Permite a administradores e instructores actualizar animales
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        resultado, codigo = AnimalService.actualizar_animal(animal_id, data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar animal: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/<int:animal_id>/estado', methods=['PUT'])
@jwt_required()
def cambiar_estado_animal(animal_id):
    """
    Cambia el estado de un animal
    ---
    Permite cambiar el estado del animal (Activo, Vendido, etc.)
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'estado_id' not in data:
            return jsonify({
                'error': 'Se requiere especificar el estado_id',
                'status': 'error'
            }), 400
        
        estado_id = data['estado_id']
        if not isinstance(estado_id, int):
            return jsonify({
                'error': 'El estado_id debe ser un entero',
                'status': 'error'
            }), 400
        
        resultado, codigo = AnimalService.cambiar_estado_animal(animal_id, estado_id, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al cambiar estado: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/<int:animal_id>', methods=['DELETE'])
@jwt_required()
def eliminar_animal(animal_id):
    """
    Elimina un animal (solo administradores)
    ---
    Elimina permanentemente un animal del sistema
    """
    try:
        current_user_id = get_jwt_identity()
        
        resultado, codigo = AnimalService.eliminar_animal(animal_id, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar animal: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_animales():
    """
    Búsqueda general de animales
    ---
    Busca en múltiples campos: hierro, raza, observaciones
    """
    try:
        termino = request.args.get('q', '').strip()
        hacienda_id = request.args.get('hacienda_id', type=int)
        
        if not termino:
            return jsonify({
                'error': 'Se requiere un término de búsqueda (parámetro q)',
                'status': 'error'
            }), 400
        
        resultado, codigo = AnimalService.buscar_animales(termino, hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error en búsqueda: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas():
    """
    Obtiene estadísticas de animales
    ---
    Retorna estadísticas generales o por hacienda
    """
    try:
        hacienda_id = request.args.get('hacienda_id', type=int)
        resultado, codigo = AnimalService.obtener_estadisticas_animales(hacienda_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/por-hacienda/<int:hacienda_id>', methods=['GET'])
@jwt_required()
def listar_animales_por_hacienda(hacienda_id):
    """
    Lista animales de una hacienda específica
    ---
    Obtiene todos los animales de una hacienda con filtros opcionales
    """
    try:
        filtros = {'hacienda_id': hacienda_id}
        
        # Filtros adicionales
        if request.args.get('sexo'):
            filtros['sexo'] = request.args.get('sexo').strip()
        
        if request.args.get('estado_id'):
            filtros['estado_id'] = request.args.get('estado_id', type=int)
        
        if request.args.get('raza'):
            filtros['raza'] = request.args.get('raza').strip()
        
        preñada = request.args.get('preñada')
        if preñada is not None:
            filtros['preñada'] = preñada.lower() == 'true'
        
        # Paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 100, type=int), 200)
        
        resultado, codigo = AnimalService.listar_animales(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar animales por hacienda: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/estados', methods=['GET'])
@jwt_required()
def obtener_estados():
    """
    Obtiene todos los estados de animal disponibles
    ---
    Lista todos los estados posibles para los animales
    """
    try:
        resultado, codigo = AnimalService.obtener_estados_animal()
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estados: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/hembras-reproductivas', methods=['GET'])
@jwt_required()
def listar_hembras_reproductivas():
    """
    Lista hembras en edad reproductiva
    ---
    Obtiene hembras activas en edad reproductiva (2-15 años aprox)
    """
    try:
        filtros = {
            'sexo': 'Hembra',
            'estado_id': 1  # Solo activas
        }
        
        # Filtrar por hacienda si se especifica
        if request.args.get('hacienda_id'):
            filtros['hacienda_id'] = request.args.get('hacienda_id', type=int)
        
        resultado, codigo = AnimalService.listar_animales(filtros, 1, 1000)
        
        if codigo == 200:
            # Importación correcta
            from models import Animal
            
            hembras_reproductivas = []
            for animal_data in resultado['animales']:
                # Buscar el animal en la base de datos para usar el método
                animal = Animal.query.get(animal_data['idanimal'])
                if animal:
                    edad = animal.calcular_edad()
                    if edad and 2 <= edad <= 15:
                        hembras_reproductivas.append(animal_data)
                else:
                    # Si no tiene fecha de nacimiento, incluir por defecto
                    hembras_reproductivas.append(animal_data)
            
            return jsonify({
                'hembras_reproductivas': hembras_reproductivas,
                'total': len(hembras_reproductivas),
                'status': 'success'
            }), 200
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener hembras reproductivas: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/preñadas', methods=['GET'])
@jwt_required()
def listar_preñadas():
    """
    Lista hembras preñadas
    ---
    Obtiene todas las hembras que están actualmente preñadas
    """
    try:
        filtros = {
            'sexo': 'Hembra',
            'preñada': True
        }
        
        # Filtrar por hacienda si se especifica
        if request.args.get('hacienda_id'):
            filtros['hacienda_id'] = request.args.get('hacienda_id', type=int)
        
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        resultado, codigo = AnimalService.listar_animales(filtros, pagina, por_pagina)
        
        if codigo == 200:
            # Agregar información adicional de gestación
            from models import Animal
            for animal_data in resultado['animales']:
                animal = Animal.query.get(animal_data['idanimal'])
                if animal:
                    dias_gestacion = animal.dias_gestacion()
                    animal_data['dias_gestacion'] = dias_gestacion
                    if dias_gestacion:
                        # Gestación promedio bovina: 283 días
                        animal_data['dias_faltantes'] = max(0, 283 - dias_gestacion)
                        animal_data['fecha_probable_parto'] = None  # Se puede calcular si se necesita
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener animales preñados: {str(e)}',
            'status': 'error'
        }), 500

@animales_bp.route('/validar-hierro', methods=['POST'])
@jwt_required()
def validar_hierro():
    """
    Valida un hierro y verifica si está disponible en la hacienda
    ---
    Útil para validación en tiempo real en formularios
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('hierro') or not data.get('hacienda_id'):
            return jsonify({
                'error': 'Hierro y hacienda_id son requeridos',
                'status': 'error'
            }), 400
        
        hierro = str(data['hierro']).strip()
        hacienda_id = data['hacienda_id']
        animal_id_excluir = data.get('excluir_id')  # Para edición
        
        # Validar hierro
        from models.animal import Animal
        es_valido, mensaje = Animal.validar_hierro(hierro, hacienda_id, animal_id_excluir)
        
        return jsonify({
            'valido': es_valido,
            'disponible': es_valido,
            'mensaje': mensaje,
            'status': 'success' if es_valido else 'error'
        }), 200 if es_valido else 400
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar hierro: {str(e)}',
            'status': 'error'
        }), 500