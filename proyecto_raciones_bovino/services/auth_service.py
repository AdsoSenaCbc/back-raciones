from models import db, Usuario, RolUsuario
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime
import re

class AuthService:
    """
    Servicio de autenticación simplificado
    Maneja login y registro directo de usuarios
    """
    
    @staticmethod
    def validar_email(email):
        """Valida formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    @staticmethod
    def validar_documento(documento):
        """Valida formato de documento"""
        # Solo números y letras, entre 6 y 20 caracteres
        return documento.isalnum() and 6 <= len(documento) <= 20
    
    @staticmethod
    def validar_password(password):
        """Valida contraseña - mínimo 6 caracteres"""
        if not password or len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        
        # Opcional: agregar más validaciones
        if len(password) > 128:
            return False, "La contraseña no puede exceder 128 caracteres"
        
        return True, "Contraseña válida"
    
    @staticmethod
    def validar_nombres(nombres, apellidos):
        """Valida nombres y apellidos"""
        if not nombres or not apellidos:
            return False, "Nombres y apellidos son requeridos"
        
        if len(nombres.strip()) < 2 or len(apellidos.strip()) < 2:
            return False, "Nombres y apellidos deben tener al menos 2 caracteres"
        
        if len(nombres.strip()) > 50 or len(apellidos.strip()) > 50:
            return False, "Nombres y apellidos no pueden exceder 50 caracteres"
        
        # Solo letras, espacios y algunos caracteres especiales
        patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$'
        if not re.match(patron, nombres) or not re.match(patron, apellidos):
            return False, "Nombres y apellidos solo pueden contener letras"
        
        return True, "Nombres válidos"
    
    @staticmethod
    def login(email, password):
        """
        Autentica un usuario en el sistema
        
        Args:
            email (str): Email del usuario
            password (str): Contraseña del usuario
            
        Returns:
            tuple: (resultado_dict, codigo_http)
        """
        try:
            # Validar datos de entrada
            if not email or not password:
                return {
                    'error': 'Email y contraseña son requeridos',
                    'status': 'error',
                    'code': 'MISSING_CREDENTIALS'
                }, 400
            
            email = email.lower().strip()
            
            if not AuthService.validar_email(email):
                return {
                    'error': 'Formato de email inválido',
                    'status': 'error',
                    'code': 'INVALID_EMAIL'
                }, 400
            
            # Buscar usuario
            usuario = Usuario.query.filter_by(email=email).first()
            
            if not usuario:
                return {
                    'error': 'Credenciales incorrectas',
                    'status': 'error',
                    'code': 'INVALID_CREDENTIALS'
                }, 401
            
            if not usuario.activo:
                return {
                    'error': 'Cuenta desactivada. Contacte al administrador',
                    'status': 'error',
                    'code': 'ACCOUNT_DISABLED'
                }, 403
            
            if not usuario.check_password(password):
                return {
                    'error': 'Credenciales incorrectas',
                    'status': 'error',
                    'code': 'INVALID_CREDENTIALS'
                }, 401
            
            # Crear tokens JWT
            access_token = create_access_token(
                identity=usuario.idusuario,
                additional_claims={
                    'rol': usuario.rol.nombre_rol,
                    'email': usuario.email,
                    'nombre_completo': f"{usuario.nombres} {usuario.apellidos}"
                }
            )
            refresh_token = create_refresh_token(identity=usuario.idusuario)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'usuario': usuario.to_dict(),
                'message': 'Autenticación exitosa',
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error interno durante la autenticación: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def registrar_usuario(datos, creado_por_id=None):
        """
        Registra un nuevo usuario directamente (sin aprobación)
        
        Args:
            datos (dict): Datos del usuario a registrar
            creado_por_id (int): ID del usuario que crea (opcional, para admins)
            
        Returns:
            tuple: (resultado_dict, codigo_http)
        """
        try:
            # Validar campos requeridos
            campos_requeridos = ['nombres', 'apellidos', 'documento', 'email', 'password']
            campos_faltantes = [campo for campo in campos_requeridos if not datos.get(campo)]
            
            if campos_faltantes:
                return {
                    'error': f'Campos requeridos faltantes: {", ".join(campos_faltantes)}',
                    'status': 'error',
                    'code': 'MISSING_FIELDS'
                }, 400
            
            # Limpiar y validar datos
            email = datos['email'].lower().strip()
            documento = datos['documento'].strip()
            nombres = datos['nombres'].strip()
            apellidos = datos['apellidos'].strip()
            password = datos['password']
            telefono = datos.get('telefono', '').strip() or None
            direccion = datos.get('direccion', '').strip() or None
            rol_solicitado = datos.get('rol', 'Aprendiz')  # Por defecto Aprendiz
            
            # Validaciones
            if not AuthService.validar_email(email):
                return {
                    'error': 'Formato de email inválido',
                    'status': 'error',
                    'code': 'INVALID_EMAIL'
                }, 400
            
            if not AuthService.validar_documento(documento):
                return {
                    'error': 'Documento debe contener solo números y letras (6-20 caracteres)',
                    'status': 'error',
                    'code': 'INVALID_DOCUMENT'
                }, 400
            
            es_valido, mensaje = AuthService.validar_nombres(nombres, apellidos)
            if not es_valido:
                return {
                    'error': mensaje,
                    'status': 'error',
                    'code': 'INVALID_NAMES'
                }, 400
            
            es_valido, mensaje = AuthService.validar_password(password)
            if not es_valido:
                return {
                    'error': mensaje,
                    'status': 'error',
                    'code': 'INVALID_PASSWORD'
                }, 400
            
            # Validar teléfono si se proporciona
            if telefono:
                patron_telefono = r'^[0-9\+\-\(\)\s]{7,15}$'
                if not re.match(patron_telefono, telefono):
                    return {
                        'error': 'Formato de teléfono inválido',
                        'status': 'error',
                        'code': 'INVALID_PHONE'
                    }, 400
            
            # Verificar que el rol existe
            rol = RolUsuario.query.filter_by(nombre_rol=rol_solicitado, activo=True).first()
            if not rol:
                return {
                    'error': f'Rol "{rol_solicitado}" no válido. Los roles disponibles son: Administrador, Instructor, Aprendiz',
                    'status': 'error',
                    'code': 'INVALID_ROLE'
                }, 400
            
            # Verificar si ya existe el documento o email
            usuario_existente = Usuario.query.filter(
                db.or_(Usuario.documento == documento, Usuario.email == email)
            ).first()
            
            if usuario_existente:
                campo = 'documento' if usuario_existente.documento == documento else 'email'
                return {
                    'error': f'El {campo} ya está registrado en el sistema',
                    'status': 'error',
                    'code': 'ALREADY_EXISTS'
                }, 409
            
            # Crear el usuario
            usuario = Usuario(
                idrol=rol.idrol,
                nombres=nombres,
                apellidos=apellidos,
                documento=documento,
                email=email,
                telefono=telefono,
                direccion=direccion,
                activo=True  # Activado por defecto
            )
            usuario.set_password(password)
            
            db.session.add(usuario)
            db.session.commit()
            
            # Preparar respuesta
            mensaje = f'Usuario "{nombres} {apellidos}" registrado exitosamente'
            respuesta = {
                'message': mensaje,
                'status': 'success',
                'usuario': usuario.to_dict()
            }
            
            # Si fue creado por un admin, incluir esa información
            if creado_por_id:
                creador = Usuario.query.get(creado_por_id)
                if creador:
                    respuesta['creado_por'] = f'{creador.nombres} {creador.apellidos}'
            
            return respuesta, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al registrar usuario: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def refresh_token(usuario_id):
        """
        Renueva el token de acceso
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            tuple: (resultado_dict, codigo_http)
        """
        try:
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario or not usuario.activo:
                return {
                    'error': 'Usuario no válido o inactivo',
                    'status': 'error',
                    'code': 'INVALID_USER'
                }, 401
            
            # Crear nuevo token de acceso
            new_token = create_access_token(
                identity=usuario.idusuario,
                additional_claims={
                    'rol': usuario.rol.nombre_rol,
                    'email': usuario.email,
                    'nombre_completo': f"{usuario.nombres} {usuario.apellidos}"
                }
            )
            
            return {
                'access_token': new_token,
                'status': 'success',
                'message': 'Token renovado exitosamente'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al renovar token: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def cambiar_password(usuario_id, password_actual, password_nueva):
        """
        Cambia la contraseña de un usuario
        
        Args:
            usuario_id (int): ID del usuario
            password_actual (str): Contraseña actual
            password_nueva (str): Nueva contraseña
            
        Returns:
            tuple: (resultado_dict, codigo_http)
        """
        try:
            usuario = Usuario.query.get(usuario_id)
            
            if not usuario:
                return {
                    'error': 'Usuario no encontrado',
                    'status': 'error',
                    'code': 'USER_NOT_FOUND'
                }, 404
            
            # Verificar contraseña actual
            if not usuario.check_password(password_actual):
                return {
                    'error': 'Contraseña actual incorrecta',
                    'status': 'error',
                    'code': 'INVALID_CURRENT_PASSWORD'
                }, 401
            
            # Validar nueva contraseña
            es_valido, mensaje = AuthService.validar_password(password_nueva)
            if not es_valido:
                return {
                    'error': mensaje,
                    'status': 'error',
                    'code': 'INVALID_NEW_PASSWORD'
                }, 400
            
            # Cambiar contraseña
            usuario.set_password(password_nueva)
            db.session.commit()
            
            return {
                'message': 'Contraseña cambiada exitosamente',
                'status': 'success'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al cambiar contraseña: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500