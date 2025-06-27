from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(db.Model):
    """
    Modelo para la tabla usuarios
    Representa los usuarios registrados en el sistema
    """
    __tablename__ = 'usuarios'
    
    # Campos de la tabla
    idusuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idrol = db.Column(db.Integer, db.ForeignKey('rol_usuario.idrol'), nullable=False)
    nombres = db.Column(db.String(50), nullable=False)
    apellidos = db.Column(db.String(50), nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(150))
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Usuario {self.nombres} {self.apellidos}>'
    
    def set_password(self, password):
        """Genera y establece el hash de la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña contra el hash almacenado"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Convierte el objeto a diccionario para JSON"""
        data = {
            'idusuario': self.idusuario,
            'idrol': self.idrol,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'documento': self.documento,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'activo': self.activo,
            'rol': self.rol.nombre_rol if self.rol else None,
            'nombre_completo': f"{self.nombres} {self.apellidos}"
        }
        
        # Solo incluir información sensible si se solicita específicamente
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    def es_administrador(self):
        """Verifica si el usuario tiene rol de administrador"""
        return self.rol and self.rol.nombre_rol == 'Administrador'
    
    def es_instructor(self):
        """Verifica si el usuario tiene rol de instructor"""
        return self.rol and self.rol.nombre_rol == 'Instructor'
    
    def es_aprendiz(self):
        """Verifica si el usuario tiene rol de aprendiz"""
        return self.rol and self.rol.nombre_rol == 'Aprendiz'
    
    def puede_gestionar_usuarios(self):
        """Verifica si el usuario puede gestionar otros usuarios"""
        return self.es_administrador()
    
    def puede_ver_estadisticas(self):
        """Verifica si el usuario puede ver estadísticas del sistema"""
        return self.es_administrador()
    
    def puede_gestionar_haciendas(self):
        """Verifica si el usuario puede gestionar haciendas"""
        return self.es_administrador() or self.es_instructor()
    
    def activar(self):
        """Activa el usuario"""
        self.activo = True
        db.session.commit()
    
    def desactivar(self):
        """Desactiva el usuario"""
        self.activo = False
        db.session.commit()
    
    @staticmethod
    def buscar_por_email(email):
        """Busca un usuario por su email"""
        return Usuario.query.filter_by(email=email).first()
    
    @staticmethod
    def buscar_por_documento(documento):
        """Busca un usuario por su documento"""
        return Usuario.query.filter_by(documento=documento).first()
    
    @staticmethod
    def crear_usuario_admin_defecto():
        """Crea un usuario administrador por defecto si no existe"""
        try:
            # Buscar si ya existe un admin
            admin_existente = Usuario.query.join(Usuario.rol).filter(
                db.and_(Usuario.email == 'admin@racionesbovino.com',
                    db.text("rol_usuario.nombre_rol = 'Administrador'"))
            ).first()
            
            if not admin_existente:
                # Importar RolUsuario aquí para evitar importación circular
                from .rol import RolUsuario
                
                rol_admin = RolUsuario.query.filter_by(nombre_rol='Administrador').first()
                if rol_admin:
                    admin = Usuario(
                        idrol=rol_admin.idrol,
                        nombres='Administrador',
                        apellidos='Sistema',
                        documento='00000000',
                        email='admin@racionesbovino.com',
                        telefono='0000000000',
                        direccion='Sistema',
                        activo=True
                    )
                    admin.set_password('admin123')  # Cambiar en producción
                    
                    db.session.add(admin)
                    db.session.commit()
                    return True
                else:
                    print("❌ No se encontró el rol Administrador")
                    return False
            else:
                print("✅ Usuario administrador ya existe")
                return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando usuario admin: {e}")
            return False
    
    @staticmethod
    def obtener_estadisticas():
        """Obtiene estadísticas de usuarios"""
        try:
            total = Usuario.query.count()
            activos = Usuario.query.filter_by(activo=True).count()
            inactivos = total - activos
            
            # Usuarios por rol
            por_rol = db.session.query(
                db.text("rol_usuario.nombre_rol"),
                db.func.count(Usuario.idusuario)
            ).join(Usuario.rol).group_by(db.text("rol_usuario.nombre_rol")).all()
            
            return {
                'total_usuarios': total,
                'usuarios_activos': activos,
                'usuarios_inactivos': inactivos,
                'por_rol': [
                    {'rol': rol, 'cantidad': cant} 
                    for rol, cant in por_rol
                ]
            }
        except Exception as e:
            print(f"Error obteniendo estadísticas de usuarios: {e}")
            return {
                'total_usuarios': 0,
                'usuarios_activos': 0,
                'usuarios_inactivos': 0,
                'por_rol': []
            }