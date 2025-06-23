from . import db

class CatalogoVacuna(db.Model):
    """
    Modelo para la tabla catalogo_vacunas
    Representa el catálogo de vacunas disponibles en el sistema
    """
    __tablename__ = 'catalogo_vacunas'
    
    # Campos de la tabla
    idvacuna = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_vacuna = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    frecuencia_dias = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=False)
    
    # Relación con vacunaciones
    vacunaciones = db.relationship('VacunacionAnimal', backref='vacuna', lazy=True)
    
    def __repr__(self):
        return f'<CatalogoVacuna {self.nombre_vacuna}>'
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'idvacuna': self.idvacuna,
            'nombre_vacuna': self.nombre_vacuna,
            'descripcion': self.descripcion,
            'frecuencia_dias': self.frecuencia_dias,
            'activo': self.activo
        }
    
    def activar(self):
        """Activa la vacuna"""
        self.activo = True
        db.session.commit()
    
    def desactivar(self):
        """Desactiva la vacuna"""
        self.activo = False
        db.session.commit()
    
    def actualizar_datos(self, datos):
        """Actualiza los datos de la vacuna"""
        campos_actualizables = ['nombre_vacuna', 'descripcion', 'frecuencia_dias']
        
        actualizado = False
        for campo in campos_actualizables:
            if campo in datos and datos[campo] is not None:
                if campo == 'frecuencia_dias':
                    try:
                        setattr(self, campo, int(datos[campo]))
                        actualizado = True
                    except (ValueError, TypeError):
                        continue
                else:
                    setattr(self, campo, str(datos[campo]).strip())
                    actualizado = True
        
        if actualizado:
            db.session.commit()
        
        return actualizado
    
    @staticmethod
    def obtener_activas():
        """Obtiene todas las vacunas activas"""
        return CatalogoVacuna.query.filter_by(activo=True).all()
    
    @staticmethod
    def buscar_por_nombre(nombre):
        """Busca vacunas por nombre (búsqueda parcial)"""
        return CatalogoVacuna.query.filter(
            CatalogoVacuna.nombre_vacuna.ilike(f'%{nombre}%')
        ).all()
    
    @staticmethod
    def obtener_estadisticas():
        """Obtiene estadísticas del catálogo de vacunas"""
        total = CatalogoVacuna.query.count()
        activas = CatalogoVacuna.query.filter_by(activo=True).count()
        inactivas = total - activas
        
        # Vacunas más utilizadas
        try:
            from .vacunacion_animal import VacunacionAnimal
            vacunas_mas_usadas = db.session.query(
                CatalogoVacuna.nombre_vacuna,
                db.func.count(VacunacionAnimal.idvacunacion).label('total_aplicaciones')
            ).join(VacunacionAnimal).group_by(
                CatalogoVacuna.idvacuna, CatalogoVacuna.nombre_vacuna
            ).order_by(db.desc('total_aplicaciones')).limit(10).all()
            
            vacunas_populares = [
                {'vacuna': nombre, 'aplicaciones': total}
                for nombre, total in vacunas_mas_usadas
            ]
        except ImportError:
            vacunas_populares = []
        
        return {
            'total_vacunas': total,
            'vacunas_activas': activas,
            'vacunas_inactivas': inactivas,
            'vacunas_mas_usadas': vacunas_populares
        }
    
    @staticmethod
    def validar_nombre_vacuna(nombre):
        """Valida el nombre de la vacuna"""
        if not nombre or not nombre.strip():
            return False, "Nombre de vacuna es requerido"
        
        nombre = nombre.strip()
        if len(nombre) < 3:
            return False, "El nombre debe tener al menos 3 caracteres"
        
        if len(nombre) > 100:
            return False, "El nombre no puede exceder 100 caracteres"
        
        return True, "Nombre válido"
    
    @staticmethod
    def validar_frecuencia(frecuencia_dias):
        """Valida la frecuencia en días"""
        if frecuencia_dias is None:
            return True, "Campo opcional"
        
        try:
            frecuencia = int(frecuencia_dias)
            if frecuencia < 1:
                return False, "La frecuencia debe ser mayor a 0 días"
            if frecuencia > 3650:  # 10 años máximo
                return False, "La frecuencia no puede exceder 3650 días (10 años)"
            return True, "Frecuencia válida"
        except (ValueError, TypeError):
            return False, "La frecuencia debe ser un número entero de días"
    
    @staticmethod
    def crear_vacunas_por_defecto():
        """Crea vacunas comunes por defecto si no existen"""
        vacunas_defecto = [
            {
                'nombre_vacuna': 'Aftosa',
                'descripcion': 'Vacuna contra fiebre aftosa',
                'frecuencia_dias': 180,
                'activo': True
            },
            {
                'nombre_vacuna': 'Brucelosis',
                'descripcion': 'Vacuna contra brucelosis bovina',
                'frecuencia_dias': 365,
                'activo': True
            },
            {
                'nombre_vacuna': 'Carbón Sintomático',
                'descripcion': 'Vacuna contra carbón sintomático',
                'frecuencia_dias': 365,
                'activo': True
            },
            {
                'nombre_vacuna': 'Rabia',
                'descripcion': 'Vacuna antirrábica',
                'frecuencia_dias': 365,
                'activo': True
            },
            {
                'nombre_vacuna': 'IBR/DVB',
                'descripcion': 'Vacuna contra rinotraqueítis infecciosa bovina y diarrea viral bovina',
                'frecuencia_dias': 365,
                'activo': True
            },
            {
                'nombre_vacuna': 'Clostridiosis',
                'descripcion': 'Vacuna contra enfermedades clostridiales',
                'frecuencia_dias': 365,
                'activo': True
            }
        ]
        
        for vacuna_data in vacunas_defecto:
            vacuna_existente = CatalogoVacuna.query.filter_by(
                nombre_vacuna=vacuna_data['nombre_vacuna']
            ).first()
            if not vacuna_existente:
                nueva_vacuna = CatalogoVacuna(
                    nombre_vacuna=vacuna_data['nombre_vacuna'],
                    descripcion=vacuna_data['descripcion'],
                    frecuencia_dias=vacuna_data['frecuencia_dias'],
                    activo=vacuna_data['activo']
                )
                db.session.add(nueva_vacuna)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando vacunas por defecto: {e}")
            return False