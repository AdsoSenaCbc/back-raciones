# models/ingredientes.py
from . import db
from datetime import datetime
from sqlalchemy import func, or_, and_

class Departamento(db.Model):
    """
    Modelo para departamentos de Colombia
    """
    __tablename__ = 'departamentos'
    
    iddepartamento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_departamento = db.Column(db.String(50), nullable=False, unique=True)
    
    # Relación con municipios
    municipios = db.relationship('Municipio', backref='departamento', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Departamento {self.nombre_departamento}>'
    
    def to_dict(self):
        return {
            'iddepartamento': self.iddepartamento,
            'nombre_departamento': self.nombre_departamento,
            'total_municipios': len(self.municipios) if self.municipios else 0
        }
    
    @staticmethod
    def crear_departamentos_colombia():
        """Crea los departamentos de Colombia por defecto"""
        departamentos_colombia = [
            'Amazonas', 'Antioquia', 'Arauca', 'Atlántico', 'Bolívar', 
            'Boyacá', 'Caldas', 'Caquetá', 'Casanare', 'Cauca', 
            'Cesar', 'Chocó', 'Córdoba', 'Cundinamarca', 'Guainía', 
            'Guaviare', 'Huila', 'La Guajira', 'Magdalena', 'Meta', 
            'Nariño', 'Norte de Santander', 'Putumayo', 'Quindío', 
            'Risaralda', 'San Andrés y Providencia', 'Santander', 
            'Sucre', 'Tolima', 'Valle del Cauca', 'Vaupés', 'Vichada',
            'Bogotá D.C.'
        ]
        
        for nombre_depto in departamentos_colombia:
            departamento_existente = Departamento.query.filter_by(nombre_departamento=nombre_depto).first()
            if not departamento_existente:
                nuevo_departamento = Departamento(nombre_departamento=nombre_depto)
                db.session.add(nuevo_departamento)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando departamentos: {e}")
            return False


class Municipio(db.Model):
    """
    Modelo para municipios por departamento
    """
    __tablename__ = 'municipios'
    
    idmunicipio = db.Column(db.Integer, primary_key=True, autoincrement=True)
    iddepartamento = db.Column(db.Integer, db.ForeignKey('departamentos.iddepartamento'), nullable=False)
    nombre_municipio = db.Column(db.String(80), nullable=False)
    
    # Constraint único por departamento
    __table_args__ = (
        db.UniqueConstraint('iddepartamento', 'nombre_municipio', name='unique_municipio_depto'),
    )
    
    # Relación con consultas bromatológicas
    consultas = db.relationship('ConsultaBromatologica', backref='municipio', lazy=True)
    
    def __repr__(self):
        return f'<Municipio {self.nombre_municipio} - {self.departamento.nombre_departamento if self.departamento else "N/A"}>'
    
    def to_dict(self):
        return {
            'idmunicipio': self.idmunicipio,
            'iddepartamento': self.iddepartamento,
            'nombre_municipio': self.nombre_municipio,
            'departamento': self.departamento.nombre_departamento if self.departamento else None
        }


class ConsultaBromatologica(db.Model):
    """
    Modelo para consultas/análisis bromatológicos
    """
    __tablename__ = 'consultas_bromatologicas'
    
    idconsulta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    iddepartamento = db.Column(db.Integer, db.ForeignKey('departamentos.iddepartamento'), nullable=False)
    idmunicipio = db.Column(db.Integer, db.ForeignKey('municipios.idmunicipio'), nullable=False)
    fecha_consulta = db.Column(db.Date, default=datetime.utcnow)
    laboratorio = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación con características nutricionales
    caracteristicas = db.relationship('CaracteristicaNutricional', backref='consulta', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ConsultaBromatologica {self.idconsulta} - {self.municipio.nombre_municipio if self.municipio else "N/A"}>'
    
    def to_dict(self):
        return {
            'idconsulta': self.idconsulta,
            'iddepartamento': self.iddepartamento,
            'idmunicipio': self.idmunicipio,
            'fecha_consulta': self.fecha_consulta.isoformat() if self.fecha_consulta else None,
            'laboratorio': self.laboratorio,
            'observaciones': self.observaciones,
            'activo': self.activo,
            'departamento': self.departamento.nombre_departamento if self.departamento else None,
            'municipio': self.municipio.nombre_municipio if self.municipio else None,
            'total_caracteristicas': len(self.caracteristicas) if self.caracteristicas else 0
        }


class Ingrediente(db.Model):
    """
    Modelo para catálogo de ingredientes
    """
    __tablename__ = 'ingredientes'
    
    idingrediente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_ingrediente = db.Column(db.String(100), nullable=False, unique=True)
    tipo_ingrediente = db.Column(db.Enum('Forraje', 'Concentrado', 'Suplemento', 'Mineral', name='tipo_ingrediente_enum'), nullable=False)
    descripcion = db.Column(db.Text)
    disponible = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    caracteristicas = db.relationship('CaracteristicaNutricional', backref='ingrediente', lazy=True, cascade='all, delete-orphan')
    detalles_lactancia = db.relationship('DetalleRacionLactancia', backref='ingrediente', lazy=True)
    detalles_ceba = db.relationship('DetalleRacionCeba', backref='ingrediente', lazy=True)
    
    def __repr__(self):
        return f'<Ingrediente {self.nombre_ingrediente}>'
    
    def to_dict(self, include_caracteristicas=False):
        data = {
            'idingrediente': self.idingrediente,
            'nombre_ingrediente': self.nombre_ingrediente,
            'tipo_ingrediente': self.tipo_ingrediente,
            'descripcion': self.descripcion,
            'disponible': self.disponible,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'total_analisis': len(self.caracteristicas) if self.caracteristicas else 0
        }
        
        if include_caracteristicas and self.caracteristicas:
            data['caracteristicas_nutricionales'] = [c.to_dict() for c in self.caracteristicas]
        
        return data
    
    def obtener_caracteristica_promedio(self):
        """Calcula valores nutricionales promedio de todas las características"""
        if not self.caracteristicas:
            return None
        
        caracteristicas_activas = [c for c in self.caracteristicas if c.consulta.activo]
        if not caracteristicas_activas:
            return None
        
        n = len(caracteristicas_activas)
        
        promedio = {
            'materia_seca': sum(c.materia_seca for c in caracteristicas_activas) / n,
            'proteina_cruda': sum(c.proteina_cruda for c in caracteristicas_activas) / n,
            'ceniza': sum(c.ceniza or 0 for c in caracteristicas_activas) / n,
            'extracto_etereo': sum(c.extracto_etereo or 0 for c in caracteristicas_activas) / n,
            'fdn': sum(c.fdn or 0 for c in caracteristicas_activas) / n,
            'fda': sum(c.fda or 0 for c in caracteristicas_activas) / n,
            'ndt': sum(c.ndt or 0 for c in caracteristicas_activas) / n,
            'calcio': sum(c.calcio or 0 for c in caracteristicas_activas) / n,
            'fosforo': sum(c.fosforo or 0 for c in caracteristicas_activas) / n,
            'ed_mcal_kg': sum(c.ed_mcal_kg or 0 for c in caracteristicas_activas) / n,
            'em_mcal_kg': sum(c.em_mcal_kg or 0 for c in caracteristicas_activas) / n,
            'total_analisis': n
        }
        
        return promedio
    
    @staticmethod
    def crear_ingredientes_basicos():
        """Crea ingredientes básicos comunes en alimentación bovina"""
        ingredientes_basicos = [
            # Forrajes
            {'nombre': 'Pasto Guinea', 'tipo': 'Forraje', 'descripcion': 'Panicum maximum'},
            {'nombre': 'Pasto Estrella', 'tipo': 'Forraje', 'descripcion': 'Cynodon nlemfuensis'},
            {'nombre': 'Pasto Brachiaria', 'tipo': 'Forraje', 'descripcion': 'Brachiaria spp.'},
            {'nombre': 'Ensilaje de Maíz', 'tipo': 'Forraje', 'descripcion': 'Zea mays ensilado'},
            {'nombre': 'Heno de Gramíneas', 'tipo': 'Forraje', 'descripcion': 'Heno de gramíneas tropicales'},
            
            # Concentrados
            {'nombre': 'Maíz Amarillo', 'tipo': 'Concentrado', 'descripcion': 'Grano de maíz molido'},
            {'nombre': 'Torta de Soya', 'tipo': 'Concentrado', 'descripcion': 'Subproducto de extracción de aceite'},
            {'nombre': 'Afrecho de Trigo', 'tipo': 'Concentrado', 'descripcion': 'Subproducto de molinería'},
            {'nombre': 'Palmiste', 'tipo': 'Concentrado', 'descripcion': 'Torta de palmiste'},
            {'nombre': 'Melaza', 'tipo': 'Concentrado', 'descripcion': 'Melaza de caña de azúcar'},
            
            # Suplementos
            {'nombre': 'Urea', 'tipo': 'Suplemento', 'descripcion': 'Fuente de nitrógeno no proteico'},
            {'nombre': 'Sal Común', 'tipo': 'Mineral', 'descripcion': 'Cloruro de sodio'},
            {'nombre': 'Sal Mineralizada', 'tipo': 'Mineral', 'descripcion': 'Mezcla de minerales'},
            {'nombre': 'Carbonato de Calcio', 'tipo': 'Mineral', 'descripcion': 'Fuente de calcio'},
            {'nombre': 'Fosfato Dicálcico', 'tipo': 'Mineral', 'descripcion': 'Fuente de fósforo y calcio'}
        ]
        
        for ingrediente_data in ingredientes_basicos:
            ingrediente_existente = Ingrediente.query.filter_by(nombre_ingrediente=ingrediente_data['nombre']).first()
            if not ingrediente_existente:
                nuevo_ingrediente = Ingrediente(
                    nombre_ingrediente=ingrediente_data['nombre'],
                    tipo_ingrediente=ingrediente_data['tipo'],
                    descripcion=ingrediente_data['descripcion'],
                    disponible=True
                )
                db.session.add(nuevo_ingrediente)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creando ingredientes básicos: {e}")
            return False


class CaracteristicaNutricional(db.Model):
    """
    Modelo para características nutricionales de ingredientes
    """
    __tablename__ = 'caracteristicas_nutricionales'
    
    idcaracteristica = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idingrediente = db.Column(db.Integer, db.ForeignKey('ingredientes.idingrediente'), nullable=False)
    idconsulta = db.Column(db.Integer, db.ForeignKey('consultas_bromatologicas.idconsulta'), nullable=False)
    
    # Composición química básica
    materia_seca = db.Column(db.Numeric(5,2), nullable=False)
    proteina_cruda = db.Column(db.Numeric(5,2), nullable=False)
    ceniza = db.Column(db.Numeric(5,2), default=0)
    extracto_etereo = db.Column(db.Numeric(5,2), default=0)
    
    # Fibra
    fdn = db.Column(db.Numeric(5,2), default=0)  # Fibra Detergente Neutro
    fda = db.Column(db.Numeric(5,2), default=0)  # Fibra Detergente Ácido
    lignina = db.Column(db.Numeric(5,2), default=0)
    hemicelulosa = db.Column(db.Numeric(5,2), default=0)
    
    # Carbohidratos
    almidon = db.Column(db.Numeric(5,2), default=0)
    carbohidratos_no_estructurales = db.Column(db.Numeric(5,2), default=0)
    carbohidratos_solubles = db.Column(db.Numeric(5,2), default=0)
    
    # Minerales
    calcio = db.Column(db.Numeric(5,3), default=0)
    fosforo = db.Column(db.Numeric(5,3), default=0)
    magnesio = db.Column(db.Numeric(5,3), default=0)
    potasio = db.Column(db.Numeric(5,3), default=0)
    azufre = db.Column(db.Numeric(5,3), default=0)
    
    # Energía y digestibilidad
    ndt = db.Column(db.Numeric(5,2), default=0)  # Nutrientes Digestibles Totales
    digestibilidad_ms = db.Column(db.Numeric(5,2), default=0)
    energia_bruta_mcal_kg = db.Column(db.Numeric(6,3), default=0)
    ed_mcal_kg = db.Column(db.Numeric(6,3), default=0)  # Energía Digestible
    em_mcal_kg = db.Column(db.Numeric(6,3), default=0)  # Energía Metabolizable
    enm_mcal_kg = db.Column(db.Numeric(6,3), default=0)  # Energía Neta Mantenimiento
    eng_mcal_kg = db.Column(db.Numeric(6,3), default=0)  # Energía Neta Ganancia
    enl_mcal_kg = db.Column(db.Numeric(6,3), default=0)  # Energía Neta Lactancia
    
    fecha_analisis = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CaracteristicaNutricional {self.ingrediente.nombre_ingrediente if self.ingrediente else "N/A"}>'
    
    def to_dict(self):
        return {
            'idcaracteristica': self.idcaracteristica,
            'idingrediente': self.idingrediente,
            'idconsulta': self.idconsulta,
            'ingrediente': self.ingrediente.nombre_ingrediente if self.ingrediente else None,
            'materia_seca': float(self.materia_seca),
            'proteina_cruda': float(self.proteina_cruda),
            'ceniza': float(self.ceniza) if self.ceniza else 0,
            'extracto_etereo': float(self.extracto_etereo) if self.extracto_etereo else 0,
            'fdn': float(self.fdn) if self.fdn else 0,
            'fda': float(self.fda) if self.fda else 0,
            'lignina': float(self.lignina) if self.lignina else 0,
            'hemicelulosa': float(self.hemicelulosa) if self.hemicelulosa else 0,
            'almidon': float(self.almidon) if self.almidon else 0,
            'carbohidratos_no_estructurales': float(self.carbohidratos_no_estructurales) if self.carbohidratos_no_estructurales else 0,
            'carbohidratos_solubles': float(self.carbohidratos_solubles) if self.carbohidratos_solubles else 0,
            'calcio': float(self.calcio) if self.calcio else 0,
            'fosforo': float(self.fosforo) if self.fosforo else 0,
            'magnesio': float(self.magnesio) if self.magnesio else 0,
            'potasio': float(self.potasio) if self.potasio else 0,
            'azufre': float(self.azufre) if self.azufre else 0,
            'ndt': float(self.ndt) if self.ndt else 0,
            'digestibilidad_ms': float(self.digestibilidad_ms) if self.digestibilidad_ms else 0,
            'energia_bruta_mcal_kg': float(self.energia_bruta_mcal_kg) if self.energia_bruta_mcal_kg else 0,
            'ed_mcal_kg': float(self.ed_mcal_kg) if self.ed_mcal_kg else 0,
            'em_mcal_kg': float(self.em_mcal_kg) if self.em_mcal_kg else 0,
            'enm_mcal_kg': float(self.enm_mcal_kg) if self.enm_mcal_kg else 0,
            'eng_mcal_kg': float(self.eng_mcal_kg) if self.eng_mcal_kg else 0,
            'enl_mcal_kg': float(self.enl_mcal_kg) if self.enl_mcal_kg else 0,
            'fecha_analisis': self.fecha_analisis.isoformat() if self.fecha_analisis else None,
            'consulta': self.consulta.to_dict() if self.consulta else None
        }
    
    @staticmethod
    def validar_datos_nutricionales(datos):
        """Valida los datos nutricionales de un ingrediente"""
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = ['materia_seca', 'proteina_cruda']
        for campo in campos_requeridos:
            if not datos.get(campo):
                errores.append(f'{campo.replace("_", " ").title()} es requerido')
        
        # Validar rangos
        validaciones = [
            ('materia_seca', 0, 100),
            ('proteina_cruda', 0, 50),
            ('ceniza', 0, 30),
            ('extracto_etereo', 0, 30),
            ('fdn', 0, 90),
            ('fda', 0, 80),
            ('ndt', 0, 100),
            ('digestibilidad_ms', 0, 100)
        ]
        
        for campo, min_val, max_val in validaciones:
            if datos.get(campo) is not None:
                try:
                    valor = float(datos[campo])
                    if valor < min_val or valor > max_val:
                        errores.append(f'{campo.replace("_", " ").title()} debe estar entre {min_val} y {max_val}%')
                except (ValueError, TypeError):
                    errores.append(f'{campo.replace("_", " ").title()} debe ser un número válido')
        
        return errores