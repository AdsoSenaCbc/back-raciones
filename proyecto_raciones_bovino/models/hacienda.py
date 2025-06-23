from . import db
from datetime import datetime
from sqlalchemy import or_, and_
import re

class Hacienda(db.Model):
    """
    Modelo para la tabla haciendas
    Representa las haciendas registradas en el sistema
    """
    __tablename__ = 'haciendas'
    
    # Campos de la tabla
    idhacienda = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nit = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    propietario = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15))
    poblacion = db.Column(db.String(80))
    municipio = db.Column(db.String(80))
    departamento = db.Column(db.String(80))
    direccion = db.Column(db.String(150))
    localizacion = db.Column(db.String(50))
    hierro = db.Column(db.String(20))
    hectareas = db.Column(db.Numeric(10, 2))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=False)
    
    #  Relación con animales
    animales = db.relationship('Animal', backref='hacienda', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Hacienda {self.nombre} - {self.nit}>'
    
    def to_dict(self, include_sensitive=False):
        """Convierte el objeto a diccionario para JSON"""
        data = {
            'idhacienda': self.idhacienda,
            'nit': self.nit,
            'nombre': self.nombre,
            'propietario': self.propietario,
            'telefono': self.telefono,
            'poblacion': self.poblacion,
            'municipio': self.municipio,
            'departamento': self.departamento,
            'direccion': self.direccion,
            'localizacion': self.localizacion,
            'hierro': self.hierro,
            'hectareas': float(self.hectareas) if self.hectareas else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'activo': self.activo
        }
        return data
    
    def activar(self):
        """Activa la hacienda"""
        self.activo = True
        db.session.commit()
    
    def desactivar(self):
        """Desactiva la hacienda"""
        self.activo = False
        db.session.commit()
    
    def actualizar_datos(self, datos):
        """Actualiza los datos de la hacienda"""
        campos_actualizables = [
            'nombre', 'propietario', 'telefono', 'poblacion',
            'municipio', 'departamento', 'direccion', 'localizacion',
            'hierro', 'hectareas'
        ]
        
        actualizado = False
        for campo in campos_actualizables:
            if campo in datos and datos[campo] is not None:
                if campo == 'hectareas':
                    # Convertir a Decimal para campo numérico
                    try:
                        setattr(self, campo, float(datos[campo]))
                        actualizado = True
                    except (ValueError, TypeError):
                        continue
                else:
                    setattr(self, campo, str(datos[campo]).strip())
                    actualizado = True
        
        if actualizado:
            db.session.commit()
        
        return actualizado
    
    # NUEVO MÉTODO: Obtener estadísticas de animales de esta hacienda
    def obtener_estadisticas_animales(self):
        """Obtiene estadísticas de animales de esta hacienda"""
        from .animal import Animal
        return Animal.obtener_estadisticas_hacienda(self.idhacienda)
    
    # NUEVO MÉTODO: Contar animales por estado
    def contar_animales_por_estado(self):
        """Cuenta animales agrupados por estado"""
        from .animal import Animal
        from .estado_animal import EstadoAnimal
        
        query = db.session.query(
            EstadoAnimal.nombre_estado,
            db.func.count(Animal.idanimal).label('cantidad')
        ).join(Animal).filter(
            Animal.idhacienda == self.idhacienda
        ).group_by(EstadoAnimal.nombre_estado).all()
        
        return {estado: cantidad for estado, cantidad in query}
    
    # NUEVO MÉTODO: Obtener animales activos
    def obtener_animales_activos(self):
        """Obtiene todos los animales activos de la hacienda"""
        from .animal import Animal
        from .estado_animal import EstadoAnimal
        
        return Animal.query.join(EstadoAnimal).filter(
            and_(
                Animal.idhacienda == self.idhacienda,
                EstadoAnimal.nombre_estado == 'Activo'
            )
        ).all()
    
    # NUEVO MÉTODO: Verificar si tiene animales
    def tiene_animales(self):
        """Verifica si la hacienda tiene animales registrados"""
        from .animal import Animal
        return Animal.query.filter_by(idhacienda=self.idhacienda).count() > 0
    
    @staticmethod
    def buscar_por_nit(nit):
        """Busca una hacienda por su NIT"""
        return Hacienda.query.filter_by(nit=nit).first()
    
    @staticmethod
    def buscar_por_nombre(nombre):
        """Busca haciendas por nombre (búsqueda parcial)"""
        return Hacienda.query.filter(
            Hacienda.nombre.ilike(f'%{nombre}%')
        ).all()
    
    @staticmethod
    def buscar_por_propietario(propietario):
        """Busca haciendas por propietario (búsqueda parcial)"""
        return Hacienda.query.filter(
            Hacienda.propietario.ilike(f'%{propietario}%')
        ).all()
    
    @staticmethod
    def buscar_por_ubicacion(departamento=None, municipio=None, poblacion=None):
        """Busca haciendas por ubicación"""
        query = Hacienda.query
        
        if departamento:
            query = query.filter(Hacienda.departamento.ilike(f'%{departamento}%'))
        if municipio:
            query = query.filter(Hacienda.municipio.ilike(f'%{municipio}%'))
        if poblacion:
            query = query.filter(Hacienda.poblacion.ilike(f'%{poblacion}%'))
        
        return query.all()
    
    @staticmethod
    def obtener_activas():
        """Obtiene todas las haciendas activas"""
        return Hacienda.query.filter_by(activo=True).all()
    
    @staticmethod
    def obtener_por_estado(activo=True):
        """Obtiene haciendas por estado (activas/inactivas)"""
        return Hacienda.query.filter_by(activo=activo).all()
    
    @staticmethod
    def buscar_general(termino):
        """Búsqueda general en múltiples campos"""
        return Hacienda.query.filter(
            or_(
                Hacienda.nombre.ilike(f'%{termino}%'),
                Hacienda.propietario.ilike(f'%{termino}%'),
                Hacienda.nit.ilike(f'%{termino}%'),
                Hacienda.municipio.ilike(f'%{termino}%'),
                Hacienda.departamento.ilike(f'%{termino}%')
            )
        ).all()
    
    @staticmethod
    def obtener_estadisticas():
        """Obtiene estadísticas generales de haciendas (ACTUALIZADO con animales)"""
        total = Hacienda.query.count()
        activas = Hacienda.query.filter_by(activo=True).count()
        inactivas = total - activas
        
        # Estadísticas de hectáreas
        hectareas_totales = db.session.query(
            db.func.sum(Hacienda.hectareas)
        ).filter_by(activo=True).scalar() or 0
        
        # Haciendas por departamento
        por_departamento = db.session.query(
            Hacienda.departamento,
            db.func.count(Hacienda.idhacienda)
        ).filter_by(activo=True).group_by(
            Hacienda.departamento
        ).all()
        
        # NUEVAS ESTADÍSTICAS: Estadísticas de animales por hacienda
        try:
            from .animal import Animal
            
            # Haciendas con animales
            haciendas_con_animales = db.session.query(
                db.func.count(db.distinct(Animal.idhacienda))
            ).scalar() or 0
            
            # Animales por hacienda usando outerjoin
            animales_por_hacienda = db.session.query(
                Hacienda.nombre,
                db.func.count(Animal.idanimal).label('total_animales')
            ).outerjoin(Animal, Hacienda.idhacienda == Animal.idhacienda
            ).filter(Hacienda.activo == True
            ).group_by(Hacienda.idhacienda, Hacienda.nombre).all()
            
        except ImportError:
            # Si aún no se han creado las tablas de animales
            haciendas_con_animales = 0
            animales_por_hacienda = []
        except Exception as e:
            # Manejo de errores más específico
            print(f"Error obteniendo estadísticas de animales: {e}")
            haciendas_con_animales = 0
            animales_por_hacienda = []
        
        estadisticas = {
            'total_haciendas': total,
            'haciendas_activas': activas,
            'haciendas_inactivas': inactivas,
            'hectareas_totales': float(hectareas_totales),
            'haciendas_con_animales': haciendas_con_animales,
            'por_departamento': [
                {'departamento': dept, 'cantidad': cant}
                for dept, cant in por_departamento if dept
            ],
            'animales_por_hacienda': [
                {'hacienda': nombre, 'total_animales': total_animales}
                for nombre, total_animales in animales_por_hacienda
            ]
        }
        
        return estadisticas
    
    # ================================
    # MÉTODOS FALTANTES AGREGADOS
    # ================================
    
    @staticmethod
    def validar_nit(nit):
        """Valida el formato del NIT"""
        if not nit or not nit.strip():
            return False, "NIT es requerido"
        
        nit = nit.strip()
        if len(nit) < 6 or len(nit) > 20:
            return False, "El NIT debe tener entre 6 y 20 caracteres"
        
        # Permitir números, letras y algunos caracteres especiales (-, .)
        patron = r'^[a-zA-Z0-9\-\.]+$'
        if not re.match(patron, nit):
            return False, "El NIT solo puede contener números, letras, guiones y puntos"
        
        return True, "NIT válido"
    
    @staticmethod
    def validar_hectareas(hectareas):
        """Valida las hectáreas de la hacienda"""
        if hectareas is None:
            return True, "Campo opcional"
        
        try:
            hectareas_float = float(hectareas)
            if hectareas_float < 0:
                return False, "Las hectáreas no pueden ser negativas"
            if hectareas_float > 999999.99:
                return False, "Cantidad de hectáreas demasiado grande"
            return True, "Hectáreas válidas"
        except (ValueError, TypeError):
            return False, "Las hectáreas deben ser un número válido"
    
    @staticmethod
    def crear_hacienda_ejemplo():
        """Crea una hacienda de ejemplo si no existe"""
        try:
            # Verificar si ya existe
            hacienda_ejemplo = Hacienda.query.filter_by(nit='900123456-1').first()
            
            if not hacienda_ejemplo:
                hacienda_ejemplo = Hacienda(
                    nit='900123456-1',
                    nombre='Hacienda La Esperanza',
                    propietario='Juan Carlos Ejemplo',
                    telefono='3001234567',
                    poblacion='Valledupar',
                    municipio='Valledupar',
                    departamento='Cesar',
                    direccion='Vereda La Esperanza, Km 15 vía a Manaure',
                    localizacion='Norte de Valledupar',
                    hierro='LE-2024',
                    hectareas=150.5,
                    activo=True
                )
                
                db.session.add(hacienda_ejemplo)
                db.session.commit()
                print("✅ Hacienda de ejemplo creada: La Esperanza")
                return True
            else:
                print("✅ Hacienda de ejemplo ya existe: La Esperanza")
                return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando hacienda de ejemplo: {e}")
            return False
