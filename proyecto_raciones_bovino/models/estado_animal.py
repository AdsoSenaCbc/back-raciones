from . import db

class EstadoAnimal(db.Model):
    """
    Modelo para la tabla estados_animal
    Representa los diferentes estados que pueden tener los animales
    """
    __tablename__ = 'estados_animal'
    
    # Campos de la tabla
    idestado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_estado = db.Column(
        db.Enum('Activo', 'Vendido', 'Muerto', 'Enfermo', 'Cuarentena', name='estado_enum'), 
        nullable=False
    )
    descripcion = db.Column(db.String(100))
    
    # Relación con animales
    animales = db.relationship('Animal', backref='estado', lazy=True)
    
    def __repr__(self):
        return f'<EstadoAnimal {self.nombre_estado}>'
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'idestado': self.idestado,
            'nombre_estado': self.nombre_estado,
            'descripcion': self.descripcion
        }
    
    @staticmethod
    def crear_estados_por_defecto():
        """Crea los estados por defecto si no existen"""
        estados_defecto = [
            {'nombre_estado': 'Activo', 'descripcion': 'Animal en condiciones normales'},
            {'nombre_estado': 'Vendido', 'descripcion': 'Animal vendido o transferido'},
            {'nombre_estado': 'Muerto', 'descripcion': 'Animal fallecido'},
            {'nombre_estado': 'Enfermo', 'descripcion': 'Animal con problemas de salud'},
            {'nombre_estado': 'Cuarentena', 'descripcion': 'Animal aislado por precaución'}
        ]
        
        for estado_data in estados_defecto:
            estado_existente = EstadoAnimal.query.filter_by(
                nombre_estado=estado_data['nombre_estado']
            ).first()
            if not estado_existente:
                nuevo_estado = EstadoAnimal(
                    nombre_estado=estado_data['nombre_estado'],
                    descripcion=estado_data['descripcion']
                )
                db.session.add(nuevo_estado)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando estados por defecto: {e}")
            return False
    
    @staticmethod
    def obtener_activos():
        """Obtiene estados que permiten operaciones (no Vendido/Muerto)"""
        return EstadoAnimal.query.filter(
            ~EstadoAnimal.nombre_estado.in_(['Vendido', 'Muerto'])
        ).all()
    
    @staticmethod
    def obtener_por_nombre(nombre):
        """Busca un estado por nombre"""
        return EstadoAnimal.query.filter_by(nombre_estado=nombre).first()