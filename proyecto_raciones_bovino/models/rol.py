from . import db

class RolUsuario(db.Model):
    """
    Modelo para la tabla rol_usuario
    Representa los diferentes roles que pueden tener los usuarios
    """
    __tablename__ = 'rol_usuario'
    
    # Campos de la tabla
    idrol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_rol = db.Column(db.String(50), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=False)
    
    # Relación con usuarios (un rol puede tener muchos usuarios)
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)
    
    def __repr__(self):
        return f'<RolUsuario {self.nombre_rol}>'
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'idrol': self.idrol,
            'nombre_rol': self.nombre_rol,
            'activo': self.activo
        }
    
    @staticmethod
    def crear_roles_por_defecto():
        """Crea los roles por defecto si no existen"""
        roles_defecto = [
            {'nombre_rol': 'Administrador', 'activo': True},
            {'nombre_rol': 'Instructor', 'activo': True},
            {'nombre_rol': 'Aprendiz', 'activo': True}
        ]
        
        for rol_data in roles_defecto:
            rol_existente = RolUsuario.query.filter_by(nombre_rol=rol_data['nombre_rol']).first()
            if not rol_existente:
                nuevo_rol = RolUsuario(
                    nombre_rol=rol_data['nombre_rol'],
                    activo=rol_data['activo']
                )
                db.session.add(nuevo_rol)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando roles por defecto: {e}")
            return False