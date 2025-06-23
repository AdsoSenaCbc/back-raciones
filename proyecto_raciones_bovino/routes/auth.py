from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth_service import AuthService

# Crear blueprint para autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint para login de usuarios
    ---
    Permite a un usuario autenticarse en el sistema
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = AuthService.login(
            data.get('email', ''),
            data.get('password', '')
        )
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/registrar', methods=['POST'])
def registrar():
    """
    Endpoint para registrar un nuevo usuario directamente
    ---
    Permite registrar usuarios sin proceso de aprobación
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = AuthService.registrar_usuario(data)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/registrar-admin', methods=['POST'])
@jwt_required()
def registrar_admin():
    """
    Endpoint para que administradores registren usuarios
    ---
    Permite a administradores registrar usuarios con cualquier rol
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar que el usuario actual es administrador
        from models import Usuario
        current_user = Usuario.query.get(current_user_id)
        if not current_user or not current_user.es_administrador():
            return jsonify({
                'error': 'Solo administradores pueden usar este endpoint',
                'status': 'error',
                'code': 'ACCESS_DENIED'
            }), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        resultado, codigo = AuthService.registrar_usuario(data, current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/cambiar-password', methods=['PUT'])
@jwt_required()
def cambiar_password():
    """
    Endpoint para cambiar contraseña del usuario actual
    ---
    Permite al usuario cambiar su propia contraseña
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'status': 'error'
            }), 400
        
        if not data.get('password_actual') or not data.get('password_nueva'):
            return jsonify({
                'error': 'Contraseña actual y nueva contraseña son requeridas',
                'status': 'error'
            }), 400
        
        resultado, codigo = AuthService.cambiar_password(
            current_user_id,
            data['password_actual'],
            data['password_nueva']
        )
        
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Endpoint para renovar token de acceso
    ---
    Permite renovar el token de acceso usando el refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        resultado, codigo = AuthService.refresh_token(current_user_id)
        return jsonify(resultado), codigo
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Endpoint para logout
    ---
    En JWT, el logout es principalmente del lado del cliente
    """
    try:
        return jsonify({
            'message': 'Logout exitoso. Elimina el token del cliente',
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/validar-email', methods=['POST'])
def validar_email():
    """
    Endpoint para validar formato de email
    ---
    Utilidad para validación en tiempo real
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({
                'error': 'Email es requerido',
                'status': 'error'
            }), 400
        
        email = data['email'].lower().strip()
        
        # Validar formato
        if not AuthService.validar_email(email):
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': 'Formato de email inválido',
                'status': 'error'
            }), 400
        
        # Verificar disponibilidad
        from models import Usuario
        usuario_existente = Usuario.query.filter_by(email=email).first()
        disponible = usuario_existente is None
        
        return jsonify({
            'valido': True,
            'disponible': disponible,
            'mensaje': 'Email disponible' if disponible else 'Email ya registrado',
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar email: {str(e)}',
            'status': 'error'
        }), 500

@auth_bp.route('/validar-documento', methods=['POST'])
def validar_documento():
    """
    Endpoint para validar documento
    ---
    Utilidad para validación en tiempo real
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('documento'):
            return jsonify({
                'error': 'Documento es requerido',
                'status': 'error'
            }), 400
        
        documento = data['documento'].strip()
        
        # Validar formato
        if not AuthService.validar_documento(documento):
            return jsonify({
                'valido': False,
                'disponible': False,
                'mensaje': 'Documento debe contener solo números y letras (6-20 caracteres)',
                'status': 'error'
            }), 400
        
        # Verificar disponibilidad
        from models import Usuario
        usuario_existente = Usuario.query.filter_by(documento=documento).first()
        disponible = usuario_existente is None
        
        return jsonify({
            'valido': True,
            'disponible': disponible,
            'mensaje': 'Documento disponible' if disponible else 'Documento ya registrado',
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al validar documento: {str(e)}',
            'status': 'error'
        }), 500