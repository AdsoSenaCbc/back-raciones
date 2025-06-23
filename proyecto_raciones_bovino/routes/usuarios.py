from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Usuario, RolUsuario

# Crear blueprint para usuarios
usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/perfil', methods=['GET'])
@jwt_required()
def get_perfil():
    """
    Obtiene el perfil del usuario actual
    ---
    Retorna la información del usuario autenticado
    """
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        
        if not usuario:
            return jsonify({
                'error': 'Usuario no encontrado',
                'status': 'error'
            }), 404
        
        return jsonify({
            'usuario': usuario.to_dict(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener perfil: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/perfil', methods=['PUT'])
@jwt_required()
def actualizar_perfil():
    """
    Actualiza el perfil del usuario actual
    ---
    Permite al usuario actualizar su información personal
    """
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        
        if not usuario:
            return jsonify({
                'error': 'Usuario no encontrado',
                'status': 'error'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        # Campos que el usuario puede actualizar
        campos_permitidos = ['nombres', 'apellidos', 'telefono', 'direccion']
        actualizado = False
        
        for campo in campos_permitidos:
            if campo in data and data[campo] is not None:
                valor = str(data[campo]).strip() if data[campo] else None
                setattr(usuario, campo, valor)
                actualizado = True
        
        if not actualizado:
            return jsonify({
                'message': 'No se realizaron cambios',
                'status': 'info'
            }), 200
        
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'usuario': usuario.to_dict(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Error al actualizar perfil: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/usuarios', methods=['GET'])
@jwt_required()
def get_usuarios():
    """
    Obtiene lista de usuarios (solo administradores)
    ---
    Lista todos los usuarios del sistema
    """
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        if not current_user or not current_user.es_administrador():
            return jsonify({
                'error': 'Solo administradores pueden ver la lista de usuarios',
                'status': 'error',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # Obtener parámetros de filtro
        activo = request.args.get('activo')  # true/false
        rol = request.args.get('rol')  # nombre del rol
        limite = request.args.get('limite', 50, type=int)
        pagina = request.args.get('pagina', 1, type=int)
        buscar = request.args.get('buscar', '').strip()
        
        # Construir query
        query = Usuario.query.join(RolUsuario)
        
        if activo is not None:
            query = query.filter(Usuario.activo == (activo.lower() == 'true'))
        
        if rol:
            query = query.filter(RolUsuario.nombre_rol == rol)
        
        if buscar:
            query = query.filter(
                db.or_(
                    Usuario.nombres.ilike(f'%{buscar}%'),
                    Usuario.apellidos.ilike(f'%{buscar}%'),
                    Usuario.email.ilike(f'%{buscar}%'),
                    Usuario.documento.ilike(f'%{buscar}%')
                )
            )
        
        # Paginación
        usuarios = query.order_by(Usuario.nombres, Usuario.apellidos).paginate(
            page=pagina, 
            per_page=limite, 
            error_out=False
        )
        
        return jsonify({
            'usuarios': [u.to_dict() for u in usuarios.items],
            'total': usuarios.total,
            'pagina_actual': pagina,
            'total_paginas': usuarios.pages,
            'por_pagina': limite,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener usuarios: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/usuarios/<int:usuario_id>/toggle-estado', methods=['PUT'])
@jwt_required()
def toggle_estado_usuario(usuario_id):
    """
    Activa/desactiva un usuario (solo administradores)
    ---
    Cambia el estado activo/inactivo de un usuario
    """
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        if not current_user or not current_user.es_administrador():
            return jsonify({
                'error': 'Solo administradores pueden cambiar estado de usuarios',
                'status': 'error',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # No puede desactivarse a sí mismo
        if current_user_id == usuario_id:
            return jsonify({
                'error': 'No puedes cambiar tu propio estado',
                'status': 'error'
            }), 400
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                'error': 'Usuario no encontrado',
                'status': 'error'
            }), 404
        
        # Cambiar estado
        usuario.activo = not usuario.activo
        db.session.commit()
        
        estado_texto = 'activado' if usuario.activo else 'desactivado'
        
        return jsonify({
            'message': f'Usuario {usuario.nombres} {usuario.apellidos} {estado_texto} exitosamente',
            'usuario': usuario.to_dict(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Error al cambiar estado del usuario: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(usuario_id):
    """
    Actualiza un usuario específico (solo administradores)
    ---
    Permite a administradores actualizar cualquier usuario
    """
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        if not current_user or not current_user.es_administrador():
            return jsonify({
                'error': 'Solo administradores pueden actualizar otros usuarios',
                'status': 'error',
                'code': 'ACCESS_DENIED'
            }), 403
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                'error': 'Usuario no encontrado',
                'status': 'error'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos para actualizar',
                'status': 'error'
            }), 400
        
        # Campos que se pueden actualizar
        campos_permitidos = ['nombres', 'apellidos', 'telefono', 'direccion', 'idrol']
        actualizado = False
        
        for campo in campos_permitidos:
            if campo in data and data[campo] is not None:
                if campo == 'idrol':
                    # Verificar que el rol existe
                    rol = RolUsuario.query.get(data[campo])
                    if not rol:
                        return jsonify({
                            'error': 'Rol no encontrado',
                            'status': 'error'
                        }), 404
                    setattr(usuario, campo, data[campo])
                else:
                    valor = str(data[campo]).strip() if data[campo] else None
                    setattr(usuario, campo, valor)
                actualizado = True
        
        if actualizado:
            db.session.commit()
        
        return jsonify({
            'message': f'Usuario {usuario.nombres} {usuario.apellidos} actualizado exitosamente',
            'usuario': usuario.to_dict(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Error al actualizar usuario: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@jwt_required()
def eliminar_usuario(usuario_id):
    """
    Elimina un usuario (solo administradores)
    ---
    Elimina permanentemente un usuario del sistema
    """
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        if not current_user or not current_user.es_administrador():
            return jsonify({
                'error': 'Solo administradores pueden eliminar usuarios',
                'status': 'error',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # No puede eliminarse a sí mismo
        if current_user_id == usuario_id:
            return jsonify({
                'error': 'No puedes eliminar tu propia cuenta',
                'status': 'error'
            }), 400
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({
                'error': 'Usuario no encontrado',
                'status': 'error'
            }), 404
        
        nombre_usuario = f"{usuario.nombres} {usuario.apellidos}"
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({
            'message': f'Usuario {nombre_usuario} eliminado exitosamente',
            'status': 'success'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Error al eliminar usuario: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """
    Obtiene lista de roles disponibles
    ---
    Lista todos los roles del sistema
    """
    try:
        roles = RolUsuario.query.filter_by(activo=True).all()
        return jsonify({
            'roles': [rol.to_dict() for rol in roles],
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener roles: {str(e)}',
            'status': 'error'
        }), 500

@usuarios_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def get_estadisticas():
    """
    Obtiene estadísticas del sistema (solo administradores)
    ---
    Retorna estadísticas generales del sistema
    """
    try:
        current_user_id = get_jwt_identity()
        current_user = Usuario.query.get(current_user_id)
        
        if not current_user or not current_user.es_administrador():
            return jsonify({
                'error': 'Solo administradores pueden ver estadísticas',
                'status': 'error',
                'code': 'ACCESS_DENIED'
            }), 403
        
        estadisticas = Usuario.obtener_estadisticas()
        
        return jsonify({
            'estadisticas': estadisticas,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'status': 'error'
        }), 500