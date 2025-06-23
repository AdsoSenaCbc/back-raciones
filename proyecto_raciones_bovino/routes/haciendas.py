# routes/haciendas.py - 

import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.hacienda_service import HaciendaService

# Crear blueprint para haciendas
haciendas_bp = Blueprint('haciendas', __name__)

# ===============================
# 1. CONSULTAR HACIENDAS 
# ===============================

@haciendas_bp.route('/', methods=['GET'])
@jwt_required()
def listar_haciendas():
    """
    CONSULTAR: Lista haciendas con filtros avanzados y paginación mejorada
    """
    try:
        # Parámetros de paginación
        pagina = request.args.get('pagina', 1, type=int)
        por_pagina = min(request.args.get('limite', 50, type=int), 100)
        
        # Parámetros de filtros - MEJORADOS
        filtros = {}
        
        # Filtro por estado activo
        activo = request.args.get('activo')
        if activo is not None:
            filtros['activo'] = activo.lower() == 'true'
        
        # Filtros de ubicación
        if request.args.get('departamento'):
            filtros['departamento'] = request.args.get('departamento').strip()
        
        if request.args.get('municipio'):
            filtros['municipio'] = request.args.get('municipio').strip()
        
        if request.args.get('propietario'):
            filtros['propietario'] = request.args.get('propietario').strip()
        
        # Búsqueda general
        if request.args.get('buscar'):
            filtros['buscar'] = request.args.get('buscar').strip()
        
        # NUEVOS FILTROS AGREGADOS
        # Filtro por rango de hectáreas
        if request.args.get('hectareas_min'):
            filtros['hectareas_min'] = request.args.get('hectareas_min', type=float)
        
        if request.args.get('hectareas_max'):
            filtros['hectareas_max'] = request.args.get('hectareas_max', type=float)
        
        # Filtro por NIT
        if request.args.get('nit'):
            filtros['nit'] = request.args.get('nit').strip()
        
        # Filtro solo haciendas con animales
        if request.args.get('con_animales', 'false').lower() == 'true':
            filtros['con_animales'] = True
        
        # Ordenamiento
        filtros['ordenar'] = request.args.get('ordenar', 'nombre')
        filtros['direccion'] = request.args.get('direccion', 'asc')
        
        resultado, codigo = HaciendaService.listar_haciendas(filtros, pagina, por_pagina)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar haciendas: {str(e)}',
            'status': 'error'
        }), 500

@haciendas_bp.route('/<int:hacienda_id>', methods=['GET'])
@jwt_required()
def obtener_hacienda(hacienda_id):
    """
    CONSULTAR: Obtiene una hacienda específica por ID - MEJORADO
    """
    try:
        # Parámetros para incluir información adicional
        incluir_estadisticas = request.args.get('incluir_estadisticas', 'false').lower() == 'true'
        incluir_animales = request.args.get('incluir_animales', 'false').lower() == 'true'
        
        resultado, codigo = HaciendaService.obtener_hacienda(hacienda_id)
        
        if codigo == 200 and (incluir_estadisticas or incluir_animales):
            try:
                from models.hacienda import Hacienda
                hacienda = Hacienda.query.get(hacienda_id)
                if hacienda:
                    if incluir_estadisticas:
                        resultado['hacienda']['estadisticas_animales'] = hacienda.obtener_estadisticas_animales()
                        resultado['hacienda']['animales_por_estado'] = hacienda.contar_animales_por_estado()
                        resultado['hacienda']['total_animales'] = len(hacienda.animales) if hacienda.animales else 0
                    
                    if incluir_animales:
                        # Incluir resumen de animales
                        animales_activos = hacienda.obtener_animales_activos()
                        resultado['hacienda']['animales_activos'] = [
                            {
                                'idanimal': a.idanimal,
                                'hierro': a.hierro,
                                'sexo': a.sexo,
                                'raza': a.raza,
                                'edad': a.calcular_edad()
                            }
                            for a in animales_activos[:10]  # Solo los primeros 10
                        ]
                        resultado['hacienda']['total_animales_activos'] = len(animales_activos)
            except:
                pass  # No fallar si no se pueden obtener datos adicionales
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener hacienda: {str(e)}',
            'status': 'error'
        }), 500

@haciendas_bp.route('/activas', methods=['GET'])
@jwt_required()
def listar_haciendas_activas():
    """
    CONSULTAR: Lista solo las haciendas activas - MEJORADO
    """
    try:
        filtros = {'activo': True}
        
        # Filtros adicionales opcionales
        if request.args.get('departamento'):
            filtros['departamento'] = request.args.get('departamento').strip()
        
        if request.args.get('municipio'):
            filtros['municipio'] = request.args.get('municipio').strip()
        
        # Incluir información básica de animales
        incluir_conteo_animales = request.args.get('incluir_animales', 'false').lower() == 'true'
        
        resultado, codigo = HaciendaService.listar_haciendas(filtros, 1, 1000)
        
        if codigo == 200:
            # Simplificar respuesta para uso en selects/dropdowns
            haciendas_simples = []
            
            for h in resultado['haciendas']:
                hacienda_simple = {
                    'idhacienda': h['idhacienda'],
                    'nombre': h['nombre'],
                    'propietario': h['propietario'],
                    'municipio': h['municipio'],
                    'departamento': h['departamento'],
                    'nit': h['nit']
                }
                
                if incluir_conteo_animales:
                    try:
                        from models.hacienda import Hacienda
                        hacienda_obj = Hacienda.query.get(h['idhacienda'])
                        if hacienda_obj:
                            hacienda_simple['total_animales'] = len(hacienda_obj.animales) if hacienda_obj.animales else 0
                    except:
                        hacienda_simple['total_animales'] = 0
                
                haciendas_simples.append(hacienda_simple)
            
            return jsonify({
                'haciendas': haciendas_simples,
                'total': len(haciendas_simples),
                'filtros_aplicados': filtros,
                'status': 'success'
            }), 200
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar haciendas activas: {str(e)}',
            'status': 'error'
        }), 500

@haciendas_bp.route('/por-departamento', methods=['GET'])
@jwt_required()
def listar_por_departamento():
    """
    CONSULTAR: Lista haciendas agrupadas por departamento - MEJORADO
    """
    try:
        from models import db, Hacienda
        
        # Parámetros opcionales
        solo_activas = request.args.get('solo_activas', 'true').lower() == 'true'
        incluir_detalles = request.args.get('incluir_detalles', 'false').lower() == 'true'
        
        # Consulta base
        query = db.session.query(
            Hacienda.departamento,
            db.func.count(Hacienda.idhacienda).label('cantidad'),
            db.func.sum(Hacienda.hectareas).label('hectareas_totales'),
            db.func.avg(Hacienda.hectareas).label('hectareas_promedio')
        )
        
        if solo_activas:
            query = query.filter_by(activo=True)
        
        resultado_query = query.group_by(
            Hacienda.departamento
        ).order_by(Hacienda.departamento).all()
        
        departamentos = []
        for dept, cantidad, hectareas_total, hectareas_prom in resultado_query:
            if dept:  # Solo departamentos no nulos
                dept_data = {
                    'departamento': dept,
                    'cantidad_haciendas': cantidad,
                    'hectareas_totales': float(hectareas_total) if hectareas_total else 0,
                    'hectareas_promedio': round(float(hectareas_prom), 2) if hectareas_prom else 0
                }
                
                # Incluir detalles si se solicita
                if incluir_detalles:
                    # Obtener municipios en este departamento
                    municipios_query = db.session.query(
                        Hacienda.municipio,
                        db.func.count(Hacienda.idhacienda).label('cantidad')
                    ).filter(Hacienda.departamento == dept)
                    
                    if solo_activas:
                        municipios_query = municipios_query.filter_by(activo=True)
                    
                    municipios = municipios_query.group_by(
                        Hacienda.municipio
                    ).order_by(Hacienda.municipio).all()
                    
                    dept_data['municipios'] = [
                        {'municipio': mun or 'Sin especificar', 'cantidad': cant}
                        for mun, cant in municipios if mun
                    ]
                
                departamentos.append(dept_data)
        
        return jsonify({
            'departamentos': departamentos,
            'total_departamentos': len(departamentos),
            'filtros_aplicados': {
                'solo_activas': solo_activas,
                'incluir_detalles': incluir_detalles
            },
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al agrupar por departamento: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# 2. AGREGAR HACIENDAS - MEJORADO
# ===============================

@haciendas_bp.route('/', methods=['POST'])
@jwt_required()
def crear_hacienda():
    """
    AGREGAR: Crea una nueva hacienda - MEJORADO con validaciones
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        # Validaciones adicionales
        campos_requeridos = ['nit', 'nombre', 'propietario']
        campos_faltantes = [campo for campo in campos_requeridos if not data.get(campo)]
        
        if campos_faltantes:
            return jsonify({
                'error': f'Campos requeridos faltantes: {", ".join(campos_faltantes)}',
                'status': 'error',
                'campos_faltantes': campos_faltantes
            }), 400
        
        # Validaciones de formato
        nit = str(data['nit']).strip()
        if len(nit) < 6:
            return jsonify({
                'error': 'El NIT debe tener al menos 6 caracteres',
                'status': 'error'
            }), 400
        
        nombre = str(data['nombre']).strip()
        if len(nombre) < 3:
            return jsonify({
                'error': 'El nombre debe tener al menos 3 caracteres',
                'status': 'error'
            }), 400
        
        resultado, codigo = HaciendaService.crear_hacienda(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al crear hacienda: {str(e)}',
            'status': 'error'
        }), 500

# NUEVO: Crear múltiples haciendas
@haciendas_bp.route('/lote', methods=['POST'])
@jwt_required()
def crear_haciendas_lote():
    """
    AGREGAR: Crea múltiples haciendas en lote
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('haciendas'):
            return jsonify({
                'error': 'Se requiere una lista de haciendas',
                'status': 'error'
            }), 400
        
        haciendas_data = data['haciendas']
        if not isinstance(haciendas_data, list):
            return jsonify({
                'error': 'El campo "haciendas" debe ser una lista',
                'status': 'error'
            }), 400
        
        if len(haciendas_data) > 20:
            return jsonify({
                'error': 'No se pueden crear más de 20 haciendas a la vez',
                'status': 'error'
            }), 400
        
        resultados_exitosos = []
        errores = []
        
        for i, hacienda_data in enumerate(haciendas_data):
            try:
                resultado, codigo = HaciendaService.crear_hacienda(hacienda_data, current_user_id)
                if codigo == 201:
                    resultados_exitosos.append(resultado)
                else:
                    errores.append({
                        'indice': i,
                        'nit': hacienda_data.get('nit', 'N/A'),
                        'nombre': hacienda_data.get('nombre', 'N/A'),
                        'error': resultado.get('error', 'Error desconocido')
                    })
            except Exception as e:
                errores.append({
                    'indice': i,
                    'nit': hacienda_data.get('nit', 'N/A'),
                    'nombre': hacienda_data.get('nombre', 'N/A'),
                    'error': str(e)
                })
        
        return jsonify({
            'message': f'Procesadas {len(haciendas_data)} haciendas',
            'exitosas': len(resultados_exitosos),
            'errores': len(errores),
            'haciendas_creadas': resultados_exitosos,
            'errores_detalle': errores,
            'status': 'success' if len(resultados_exitosos) > 0 else 'error'
        }), 200 if len(resultados_exitosos) > 0 else 400
        
    except Exception as e:
        return jsonify({
            'error': f'Error al procesar lote de haciendas: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# 3. EDITAR HACIENDAS - MEJORADO
# ===============================

@haciendas_bp.route('/<int:hacienda_id>', methods=['PUT'])
@jwt_required()
def actualizar_hacienda(hacienda_id):
    """
    EDITAR: Actualiza una hacienda existente - MEJORADO
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        # Validaciones opcionales para campos que se están actualizando
        if 'nit' in data and data['nit']:
            nit = str(data['nit']).strip()
            if len(nit) < 6:
                return jsonify({
                    'error': 'El NIT debe tener al menos 6 caracteres',
                    'status': 'error'
                }), 400
        
        if 'nombre' in data and data['nombre']:
            nombre = str(data['nombre']).strip()
            if len(nombre) < 3:
                return jsonify({
                    'error': 'El nombre debe tener al menos 3 caracteres',
                    'status': 'error'
                }), 400
        
        resultado, codigo = HaciendaService.actualizar_hacienda(hacienda_id, data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar hacienda: {str(e)}',
            'status': 'error'
        }), 500

@haciendas_bp.route('/<int:hacienda_id>/estado', methods=['PUT'])
@jwt_required()
def cambiar_estado_hacienda(hacienda_id):
    """
    EDITAR: Cambia el estado (activo/inactivo) de una hacienda - MEJORADO
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'activo' not in data:
            return jsonify({
                'error': 'Se requiere especificar el estado (activo: true/false)',
                'status': 'error'
            }), 400
        
        activo = data['activo']
        if not isinstance(activo, bool):
            return jsonify({
                'error': 'El campo activo debe ser verdadero o falso',
                'status': 'error'
            }), 400
        
        # Validación adicional: verificar animales si se va a desactivar
        if not activo:
            verificar_animales = data.get('verificar_animales', True)
            if verificar_animales:
                from models.hacienda import Hacienda
                hacienda = Hacienda.query.get(hacienda_id)
                if hacienda and hacienda.tiene_animales():
                    animales_activos = len(hacienda.obtener_animales_activos())
                    if animales_activos > 0:
                        return jsonify({
                            'error': f'No se puede desactivar la hacienda porque tiene {animales_activos} animales activos',
                            'status': 'error',
                            'animales_activos': animales_activos,
                            'sugerencia': 'Transfiera los animales o use verificar_animales=false'
                        }), 409
        
        motivo = data.get('motivo', '')  # Opcional: motivo del cambio
        
        resultado, codigo = HaciendaService.cambiar_estado_hacienda(hacienda_id, activo, current_user_id)
        
        # Agregar motivo si se proporcionó
        if codigo == 200 and motivo:
            resultado['motivo_cambio'] = motivo
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al cambiar estado: {str(e)}',
            'status': 'error'
        }), 500

# NUEVO: Actualizar solo ubicación
@haciendas_bp.route('/<int:hacienda_id>/ubicacion', methods=['PUT'])
@jwt_required()
def actualizar_ubicacion(hacienda_id):
    """
    EDITAR: Actualiza específicamente la ubicación de una hacienda
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos de ubicación',
                'status': 'error'
            }), 400
        
        # Filtrar solo campos de ubicación
        campos_ubicacion = {
            'poblacion': data.get('poblacion'),
            'municipio': data.get('municipio'),
            'departamento': data.get('departamento'),
            'direccion': data.get('direccion'),
            'localizacion': data.get('localizacion')
        }
        
        # Limpiar campos None y validar
        campos_ubicacion = {k: v for k, v in campos_ubicacion.items() if v is not None}
        
        if not campos_ubicacion:
            return jsonify({
                'error': 'Debe proporcionar al menos un campo de ubicación para actualizar',
                'status': 'error'
            }), 400
        
        resultado, codigo = HaciendaService.actualizar_hacienda(hacienda_id, campos_ubicacion, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar ubicación: {str(e)}',
            'status': 'error'
        }), 500

# NUEVO: Actualizar solo datos de contacto
@haciendas_bp.route('/<int:hacienda_id>/contacto', methods=['PUT'])
@jwt_required()
def actualizar_contacto(hacienda_id):
    """
    EDITAR: Actualiza específicamente los datos de contacto
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos de contacto',
                'status': 'error'
            }), 400
        
        # Filtrar solo campos de contacto
        campos_contacto = {
            'propietario': data.get('propietario'),
            'telefono': data.get('telefono')
        }
        
        # Limpiar campos None
        campos_contacto = {k: v for k, v in campos_contacto.items() if v is not None}
        
        if not campos_contacto:
            return jsonify({
                'error': 'Debe proporcionar al menos un campo de contacto para actualizar',
                'status': 'error'
            }), 400
        
        # Validaciones específicas
        if 'telefono' in campos_contacto and campos_contacto['telefono']:
            import re
            telefono = str(campos_contacto['telefono']).strip()
            patron_telefono = r'^[0-9\+\-\(\)\s]{7,15}$'
            if not re.match(patron_telefono, telefono):
                return jsonify({
                    'error': 'Formato de teléfono inválido',
                    'status': 'error'
                }), 400
        
        resultado, codigo = HaciendaService.actualizar_hacienda(hacienda_id, campos_contacto, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al actualizar contacto: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# 4. ELIMINAR HACIENDAS - MEJORADO
# ===============================

@haciendas_bp.route('/<int:hacienda_id>', methods=['DELETE'])
@jwt_required()
def eliminar_hacienda(hacienda_id):
    """
    ELIMINAR: Elimina una hacienda (solo administradores) - MEJORADO
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Verificaciones antes de eliminar
        verificar_animales = request.args.get('verificar_animales', 'true').lower() == 'true'
        forzar = request.args.get('forzar', 'false').lower() == 'true'
        
        if verificar_animales and not forzar:
            from models.hacienda import Hacienda
            hacienda = Hacienda.query.get(hacienda_id)
            if hacienda and hacienda.tiene_animales():
                total_animales = len(hacienda.animales) if hacienda.animales else 0
                animales_activos = len(hacienda.obtener_animales_activos())
                
                return jsonify({
                    'error': 'No se puede eliminar la hacienda porque tiene animales registrados',
                    'status': 'error',
                    'detalles': {
                        'total_animales': total_animales,
                        'animales_activos': animales_activos,
                        'hacienda': hacienda.nombre
                    },
                    'sugerencias': [
                        'Transfiera los animales a otra hacienda',
                        'Elimine los animales primero',
                        'Use forzar=true para eliminar todo'
                    ]
                }), 409
        
        if forzar:
            # Eliminar primero todos los animales relacionados
            try:
                from models.hacienda import Hacienda
                hacienda = Hacienda.query.get(hacienda_id)
                if hacienda and hacienda.animales:
                    animales_eliminados = len(hacienda.animales)
                    for animal in hacienda.animales:
                        from models import db
                        db.session.delete(animal)
                    db.session.commit()
                    
                    return jsonify({
                        'message': f'Hacienda y {animales_eliminados} animales eliminados forzosamente',
                        'status': 'warning',
                        'animales_eliminados': animales_eliminados
                    }), 200
            except Exception as e:
                from models import db
                db.session.rollback()
                return jsonify({
                    'error': f'Error al eliminar forzosamente: {str(e)}',
                    'status': 'error'
                }), 500
        
        resultado, codigo = HaciendaService.eliminar_hacienda(hacienda_id, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar hacienda: {str(e)}',
            'status': 'error'
        }), 500

# NUEVO: Eliminar múltiples haciendas
@haciendas_bp.route('/lote', methods=['DELETE'])
@jwt_required()
def eliminar_haciendas_lote():
    """
    ELIMINAR: Elimina múltiples haciendas en lote (solo administradores)
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('hacienda_ids'):
            return jsonify({
                'error': 'Se requiere una lista de IDs de haciendas',
                'status': 'error'
            }), 400
        
        hacienda_ids = data['hacienda_ids']
        if not isinstance(hacienda_ids, list):
            return jsonify({
                'error': 'El campo "hacienda_ids" debe ser una lista',
                'status': 'error'
            }), 400
        
        if len(hacienda_ids) > 10:
            return jsonify({
                'error': 'No se pueden eliminar más de 10 haciendas a la vez',
                'status': 'error'
            }), 400
        
        eliminadas_exitosas = []
        errores = []
        advertencias = []
        
        for hacienda_id in hacienda_ids:
            try:
                # Verificar animales antes de eliminar
                from models.hacienda import Hacienda
                hacienda = Hacienda.query.get(hacienda_id)
                if hacienda and hacienda.tiene_animales():
                    advertencias.append({
                        'hacienda_id': hacienda_id,
                        'nombre': hacienda.nombre,
                        'mensaje': 'Tiene animales registrados, no eliminada'
                    })
                    continue
                
                resultado, codigo = HaciendaService.eliminar_hacienda(hacienda_id, current_user_id)
                if codigo == 200:
                    eliminadas_exitosas.append(hacienda_id)
                else:
                    errores.append({
                        'hacienda_id': hacienda_id,
                        'error': resultado.get('error', 'Error desconocido')
                    })
            except Exception as e:
                errores.append({
                    'hacienda_id': hacienda_id,
                    'error': str(e)
                })
        
        return jsonify({
            'message': f'Procesadas {len(hacienda_ids)} haciendas para eliminación',
            'eliminadas': len(eliminadas_exitosas),
            'errores': len(errores),
            'advertencias': len(advertencias),
            'haciendas_eliminadas': eliminadas_exitosas,
            'errores_detalle': errores,
            'advertencias_detalle': advertencias,
            'status': 'success' if len(eliminadas_exitosas) > 0 else 'error'
        }), 200 if len(eliminadas_exitosas) > 0 else 400
        
    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar lote de haciendas: {str(e)}',
            'status': 'error'
        }), 500

# ===============================
# ENDPOINTS ADICIONALES - CONSERVADOS Y MEJORADOS
# ===============================

@haciendas_bp.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_haciendas():
    """
    CONSULTAR: Búsqueda general de haciendas - MEJORADO
    """
    try:
        current_user_id = get_jwt_identity()
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
        
        # Filtros adicionales en la búsqueda
        solo_activas = request.args.get('solo_activas', 'false').lower() == 'true'
        incluir_animales = request.args.get('incluir_animales', 'false').lower() == 'true'
        
        resultado, codigo = HaciendaService.buscar_haciendas(termino, current_user_id)
        
        if codigo == 200 and solo_activas:
            # Filtrar solo activas
            resultado['haciendas'] = [h for h in resultado['haciendas'] if h.get('activo', False)]
            resultado['total'] = len(resultado['haciendas'])
        
        if codigo == 200 and incluir_animales:
            # Agregar conteo de animales
            for hacienda in resultado['haciendas']:
                try:
                    from models.hacienda import Hacienda
                    hacienda_obj = Hacienda.query.get(hacienda['idhacienda'])
                    if hacienda_obj:
                        hacienda['total_animales'] = len(hacienda_obj.animales) if hacienda_obj.animales else 0
                        hacienda['animales_activos'] = len(hacienda_obj.obtener_animales_activos())
                except:
                    hacienda['total_animales'] = 0
                    hacienda['animales_activos'] = 0
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error en búsqueda: {str(e)}',
            'status': 'error'
        }), 500

@haciendas_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas():
    """
    CONSULTAR: Obtiene estadísticas de haciendas - MEJORADO
    """
    try:
        incluir_detalladas = request.args.get('detalladas', 'false').lower() == 'true'
        
        resultado, codigo = HaciendaService.obtener_estadisticas()
        
        if codigo == 200 and incluir_detalladas:
            # Agregar estadísticas adicionales
            try:
                from models import db, Hacienda
                
                # Distribución por tamaño (hectáreas)
                rangos_hectareas = [
                    (0, 50, 'Pequeña'),
                    (50, 200, 'Mediana'),
                    (200, 500, 'Grande'),
                    (500, float('inf'), 'Muy Grande')
                ]
                
                distribucion_tamaño = []
                for min_ha, max_ha, categoria in rangos_hectareas:
                    if max_ha == float('inf'):
                        count = Hacienda.query.filter(
                            Hacienda.activo == True,
                            Hacienda.hectareas >= min_ha
                        ).count()
                    else:
                        count = Hacienda.query.filter(
                            Hacienda.activo == True,
                            Hacienda.hectareas >= min_ha,
                            Hacienda.hectareas < max_ha
                        ).count()
                    
                    distribucion_tamaño.append({
                        'categoria': categoria,
                        'rango': f'{min_ha}-{max_ha if max_ha != float("inf") else "+"} ha',
                        'cantidad': count
                    })
                
                resultado['estadisticas']['distribucion_por_tamaño'] = distribucion_tamaño
                
                # Promedio de hectáreas
                promedio_hectareas = db.session.query(
                    db.func.avg(Hacienda.hectareas)
                ).filter(
                    Hacienda.activo == True,
                    Hacienda.hectareas.isnot(None)
                ).scalar()
                
                resultado['estadisticas']['promedio_hectareas'] = round(float(promedio_hectareas), 2) if promedio_hectareas else 0
                
            except:
                pass  # No fallar si no se pueden calcular estadísticas adicionales
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'status': 'error'
        }), 500

@haciendas_bp.route('/validar-nit', methods=['POST'])
@jwt_required()
def validar_nit():
    """
    Valida un NIT y verifica si está disponible - MEJORADO
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('nit'):
            return jsonify({
                'error': 'NIT es requerido',
                'status': 'error'
            }), 400
        
        nit = str(data['nit']).strip()
        hacienda_id_excluir = data.get('excluir_id')
        
        # Validaciones básicas
        if len(nit) < 6:
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': 'El NIT debe tener al menos 6 caracteres',
                'status': 'error'
            }), 400
        
        if len(nit) > 20:
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': 'El NIT no puede exceder 20 caracteres',
                'status': 'error'
            }), 400
        
        # Validar formato
        from models.hacienda import Hacienda
        es_valido, mensaje = Hacienda.validar_nit(nit)
        
        if not es_valido:
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': mensaje,
                'status': 'error'
            }), 400
        
        # Verificar disponibilidad
        hacienda_existente = Hacienda.query.filter_by(nit=nit).first()
        disponible = True
        
        if hacienda_existente:
            if not hacienda_id_excluir or hacienda_existente.idhacienda != hacienda_id_excluir:
                disponible = False
        
        return jsonify({
            'valido': True,
            'disponible': disponible,
            'mensaje': 'NIT disponible' if disponible else 'NIT ya registrado',
            'nit_validado': nit,
            'hacienda_existente': hacienda_existente.to_dict() if hacienda_existente and not disponible else None,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar NIT: {str(e)}',
            'status': 'error'
        }), 500

# NUEVO ENDPOINT: Resumen completo de hacienda
@haciendas_bp.route('/<int:hacienda_id>/resumen', methods=['GET'])
@jwt_required()
def obtener_resumen_hacienda(hacienda_id):
    """
    CONSULTAR: Obtiene un resumen completo de la hacienda con todas las estadísticas
    """
    try:
        from models.hacienda import Hacienda
        
        hacienda = Hacienda.query.get(hacienda_id)
        if not hacienda:
            return jsonify({
                'error': 'Hacienda no encontrada',
                'status': 'error'
            }), 404
        
        # Datos básicos de la hacienda
        resumen = hacienda.to_dict()
        
        # Estadísticas de animales
        try:
            resumen['estadisticas_animales'] = hacienda.obtener_estadisticas_animales()
            resumen['animales_por_estado'] = hacienda.contar_animales_por_estado()
            
            # Información detallada de animales
            animales_activos = hacienda.obtener_animales_activos()
            resumen['total_animales_activos'] = len(animales_activos)
            
            # Conteos por categorías
            machos = sum(1 for a in animales_activos if a.sexo == 'Macho')
            hembras = sum(1 for a in animales_activos if a.sexo == 'Hembra')
            preñadas = sum(1 for a in animales_activos if a.sexo == 'Hembra' and a.preñada)
            
            resumen['resumen_reproductivo'] = {
                'machos': machos,
                'hembras': hembras,
                'hembras_preñadas': preñadas,
                'hembras_vacias': hembras - preñadas,
                'porcentaje_preñez': round((preñadas / hembras * 100), 1) if hembras > 0 else 0
            }
            
            # Distribución por razas
            razas = {}
            for animal in animales_activos:
                raza = animal.raza or 'Sin especificar'
                razas[raza] = razas.get(raza, 0) + 1
            
            resumen['distribucion_razas'] = [
                {'raza': raza, 'cantidad': cantidad}
                for raza, cantidad in razas.items()
            ]
            
        except Exception as e:
            resumen['estadisticas_animales'] = {}
            resumen['animales_por_estado'] = {}
            resumen['total_animales_activos'] = 0
            resumen['error_estadisticas'] = str(e)
        
        # Información calculada
        if resumen.get('hectareas'):
            if resumen['total_animales_activos'] > 0:
                resumen['animales_por_hectarea'] = round(
                    resumen['total_animales_activos'] / float(resumen['hectareas']), 2
                )
            else:
                resumen['animales_por_hectarea'] = 0
        
        return jsonify({
            'resumen': resumen,
            'fecha_consulta': datetime.now().isoformat(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener resumen: {str(e)}',
            'status': 'error'
        }), 500