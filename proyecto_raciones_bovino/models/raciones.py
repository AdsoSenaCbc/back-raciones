# models/raciones.py
from . import db
from datetime import datetime, date
from sqlalchemy import func, or_, and_

class RacionLactancia(db.Model):
    """
    Modelo para raciones calculadas de vacas en lactancia
    """
    __tablename__ = 'raciones_lactancia'
    
    idracion_lactancia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idanimal = db.Column(db.Integer, db.ForeignKey('animales.idanimal'), nullable=False)
    fecha_calculo = db.Column(db.Date, nullable=False)
    peso_animal = db.Column(db.Numeric(8,2), nullable=False)
    produccion_leche_dia = db.Column(db.Numeric(6,2), nullable=False)
    porcentaje_grasa = db.Column(db.Numeric(4,2), nullable=False)
    dias_gestacion = db.Column(db.Integer, default=0)
    
    # Requerimientos calculados base (mantenimiento)
    req_materia_seca_base = db.Column(db.Numeric(8,4))
    req_proteina_total_base = db.Column(db.Numeric(8,4))
    req_proteina_digestible_base = db.Column(db.Numeric(8,4))
    req_en_base = db.Column(db.Numeric(8,3))
    req_ed_base = db.Column(db.Numeric(8,3))
    req_em_base = db.Column(db.Numeric(8,3))
    req_tnd_base = db.Column(db.Numeric(8,4))
    req_calcio_base = db.Column(db.Numeric(8,5))
    req_fosforo_base = db.Column(db.Numeric(8,5))
    
    # Requerimientos por producción de leche
    req_proteina_total_produccion = db.Column(db.Numeric(8,4))
    req_proteina_digestible_produccion = db.Column(db.Numeric(8,4))
    req_en_produccion = db.Column(db.Numeric(8,3))
    req_ed_produccion = db.Column(db.Numeric(8,3))
    req_em_produccion = db.Column(db.Numeric(8,3))
    req_tnd_produccion = db.Column(db.Numeric(8,4))
    req_calcio_produccion = db.Column(db.Numeric(8,5))
    req_fosforo_produccion = db.Column(db.Numeric(8,5))
    
    # Requerimientos adicionales por gestación
    req_proteina_total_gestacion = db.Column(db.Numeric(8,4), default=0)
    req_proteina_digestible_gestacion = db.Column(db.Numeric(8,4), default=0)
    req_en_gestacion = db.Column(db.Numeric(8,3), default=0)
    req_ed_gestacion = db.Column(db.Numeric(8,3), default=0)
    req_em_gestacion = db.Column(db.Numeric(8,3), default=0)
    req_tnd_gestacion = db.Column(db.Numeric(8,4), default=0)
    req_calcio_gestacion = db.Column(db.Numeric(8,5), default=0)
    req_fosforo_gestacion = db.Column(db.Numeric(8,5), default=0)
    
    # Totales calculados
    req_total_materia_seca = db.Column(db.Numeric(8,4))
    req_total_proteina_total = db.Column(db.Numeric(8,4))
    req_total_proteina_digestible = db.Column(db.Numeric(8,4))
    req_total_en = db.Column(db.Numeric(8,3))
    req_total_ed = db.Column(db.Numeric(8,3))
    req_total_em = db.Column(db.Numeric(8,3))
    req_total_tnd = db.Column(db.Numeric(8,4))
    req_total_calcio = db.Column(db.Numeric(8,5))
    req_total_fosforo = db.Column(db.Numeric(8,5))
    
    observaciones = db.Column(db.Text)
    calculado_por = db.Column(db.Integer, db.ForeignKey('usuarios.idusuario'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    detalles = db.relationship('DetalleRacionLactancia', backref='racion_lactancia', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RacionLactancia {self.animal.hierro if self.animal else "N/A"} - {self.fecha_calculo}>'
    
    def to_dict(self, include_detalles=False):
        data = {
            'idracion_lactancia': self.idracion_lactancia,
            'idanimal': self.idanimal,
            'fecha_calculo': self.fecha_calculo.isoformat() if self.fecha_calculo else None,
            'peso_animal': float(self.peso_animal),
            'produccion_leche_dia': float(self.produccion_leche_dia),
            'porcentaje_grasa': float(self.porcentaje_grasa),
            'dias_gestacion': self.dias_gestacion,
            
            # Información del animal
            'animal': {
                'hierro': self.animal.hierro if self.animal else None,
                'sexo': self.animal.sexo if self.animal else None,
                'raza': self.animal.raza if self.animal else None,
                'hacienda': self.animal.hacienda.nombre if self.animal and self.animal.hacienda else None
            } if self.animal else None,
            
            # Requerimientos base
            'requerimientos_base': {
                'materia_seca': float(self.req_materia_seca_base) if self.req_materia_seca_base else 0,
                'proteina_total': float(self.req_proteina_total_base) if self.req_proteina_total_base else 0,
                'proteina_digestible': float(self.req_proteina_digestible_base) if self.req_proteina_digestible_base else 0,
                'en_mcal': float(self.req_en_base) if self.req_en_base else 0,
                'ed_mcal': float(self.req_ed_base) if self.req_ed_base else 0,
                'em_mcal': float(self.req_em_base) if self.req_em_base else 0,
                'tnd_kg': float(self.req_tnd_base) if self.req_tnd_base else 0,
                'calcio_kg': float(self.req_calcio_base) if self.req_calcio_base else 0,
                'fosforo_kg': float(self.req_fosforo_base) if self.req_fosforo_base else 0
            },
            
            # Requerimientos por producción
            'requerimientos_produccion': {
                'proteina_total': float(self.req_proteina_total_produccion) if self.req_proteina_total_produccion else 0,
                'proteina_digestible': float(self.req_proteina_digestible_produccion) if self.req_proteina_digestible_produccion else 0,
                'en_mcal': float(self.req_en_produccion) if self.req_en_produccion else 0,
                'ed_mcal': float(self.req_ed_produccion) if self.req_ed_produccion else 0,
                'em_mcal': float(self.req_em_produccion) if self.req_em_produccion else 0,
                'tnd_kg': float(self.req_tnd_produccion) if self.req_tnd_produccion else 0,
                'calcio_kg': float(self.req_calcio_produccion) if self.req_calcio_produccion else 0,
                'fosforo_kg': float(self.req_fosforo_produccion) if self.req_fosforo_produccion else 0
            },
            
            # Requerimientos por gestación
            'requerimientos_gestacion': {
                'proteina_total': float(self.req_proteina_total_gestacion) if self.req_proteina_total_gestacion else 0,
                'proteina_digestible': float(self.req_proteina_digestible_gestacion) if self.req_proteina_digestible_gestacion else 0,
                'en_mcal': float(self.req_en_gestacion) if self.req_en_gestacion else 0,
                'ed_mcal': float(self.req_ed_gestacion) if self.req_ed_gestacion else 0,
                'em_mcal': float(self.req_em_gestacion) if self.req_em_gestacion else 0,
                'tnd_kg': float(self.req_tnd_gestacion) if self.req_tnd_gestacion else 0,
                'calcio_kg': float(self.req_calcio_gestacion) if self.req_calcio_gestacion else 0,
                'fosforo_kg': float(self.req_fosforo_gestacion) if self.req_fosforo_gestacion else 0
            },
            
            # Totales
            'requerimientos_totales': {
                'materia_seca': float(self.req_total_materia_seca) if self.req_total_materia_seca else 0,
                'proteina_total': float(self.req_total_proteina_total) if self.req_total_proteina_total else 0,
                'proteina_digestible': float(self.req_total_proteina_digestible) if self.req_total_proteina_digestible else 0,
                'en_mcal': float(self.req_total_en) if self.req_total_en else 0,
                'ed_mcal': float(self.req_total_ed) if self.req_total_ed else 0,
                'em_mcal': float(self.req_total_em) if self.req_total_em else 0,
                'tnd_kg': float(self.req_total_tnd) if self.req_total_tnd else 0,
                'calcio_kg': float(self.req_total_calcio) if self.req_total_calcio else 0,
                'fosforo_kg': float(self.req_total_fosforo) if self.req_total_fosforo else 0
            },
            
            'observaciones': self.observaciones,
            'calculado_por': self.calculado_por,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'total_ingredientes': len(self.detalles) if self.detalles else 0
        }
        
        if include_detalles:
            data['detalles'] = [d.to_dict() for d in self.detalles]
        
        return data
    
    def calcular_aporte_nutricional_total(self):
        """Calcula el aporte nutricional total de la ración"""
        if not self.detalles:
            return None
        
        aporte_total = {
            'materia_seca_kg': 0,
            'proteina_cruda_kg': 0,
            'ndt_kg': 0,
            'calcio_kg': 0,
            'fosforo_kg': 0,
            'ed_mcal': 0,
            'em_mcal': 0,
            'costo_total': 0
        }
        
        for detalle in self.detalles:
            if detalle.ingrediente:
                caracteristica = detalle.ingrediente.obtener_caracteristica_promedio()
                if caracteristica:
                    cantidad_ms = detalle.cantidad_kg * (caracteristica['materia_seca'] / 100)
                    aporte_total['materia_seca_kg'] += cantidad_ms
                    aporte_total['proteina_cruda_kg'] += cantidad_ms * (caracteristica['proteina_cruda'] / 100)
                    aporte_total['ndt_kg'] += cantidad_ms * (caracteristica['ndt'] / 100)
                    aporte_total['calcio_kg'] += cantidad_ms * (caracteristica['calcio'] / 100)
                    aporte_total['fosforo_kg'] += cantidad_ms * (caracteristica['fosforo'] / 100)
                    aporte_total['ed_mcal'] += cantidad_ms * caracteristica['ed_mcal_kg']
                    aporte_total['em_mcal'] += cantidad_ms * caracteristica['em_mcal_kg']
        
        return aporte_total
    
    def calcular_balance_nutricional(self):
        """Calcula el balance entre requerimientos y aportes"""
        aporte = self.calcular_aporte_nutricional_total()
        if not aporte:
            return None
        
        balance = {
            'materia_seca': {
                'requerimiento': float(self.req_total_materia_seca) if self.req_total_materia_seca else 0,
                'aporte': aporte['materia_seca_kg'],
                'diferencia': aporte['materia_seca_kg'] - (float(self.req_total_materia_seca) if self.req_total_materia_seca else 0),
                'porcentaje_cubrimiento': (aporte['materia_seca_kg'] / float(self.req_total_materia_seca) * 100) if self.req_total_materia_seca else 0
            },
            'proteina_total': {
                'requerimiento': float(self.req_total_proteina_total) if self.req_total_proteina_total else 0,
                'aporte': aporte['proteina_cruda_kg'],
                'diferencia': aporte['proteina_cruda_kg'] - (float(self.req_total_proteina_total) if self.req_total_proteina_total else 0),
                'porcentaje_cubrimiento': (aporte['proteina_cruda_kg'] / float(self.req_total_proteina_total) * 100) if self.req_total_proteina_total else 0
            },
            'tnd': {
                'requerimiento': float(self.req_total_tnd) if self.req_total_tnd else 0,
                'aporte': aporte['ndt_kg'],
                'diferencia': aporte['ndt_kg'] - (float(self.req_total_tnd) if self.req_total_tnd else 0),
                'porcentaje_cubrimiento': (aporte['ndt_kg'] / float(self.req_total_tnd) * 100) if self.req_total_tnd else 0
            }
        }
        
        return balance


class RacionCeba(db.Model):
    """
    Modelo para raciones calculadas de animales en ceba
    """
    __tablename__ = 'raciones_ceba'
    
    idracion_ceba = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idanimal = db.Column(db.Integer, db.ForeignKey('animales.idanimal'), nullable=False)
    idnrc_ceba = db.Column(db.Integer, db.ForeignKey('nrc_ceba.idnrc_ceba'), nullable=False)
    fecha_calculo = db.Column(db.Date, nullable=False)
    peso_animal = db.Column(db.Numeric(8,2), nullable=False)
    gdp_objetivo = db.Column(db.Numeric(5,3), nullable=False)  # Ganancia diaria de peso objetivo
    observaciones = db.Column(db.Text)
    calculado_por = db.Column(db.Integer, db.ForeignKey('usuarios.idusuario'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    detalles = db.relationship('DetalleRacionCeba', backref='racion_ceba', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RacionCeba {self.animal.hierro if self.animal else "N/A"} - {self.fecha_calculo}>'
    
    def to_dict(self, include_detalles=False):
        data = {
            'idracion_ceba': self.idracion_ceba,
            'idanimal': self.idanimal,
            'idnrc_ceba': self.idnrc_ceba,
            'fecha_calculo': self.fecha_calculo.isoformat() if self.fecha_calculo else None,
            'peso_animal': float(self.peso_animal),
            'gdp_objetivo': float(self.gdp_objetivo),
            'observaciones': self.observaciones,
            'calculado_por': self.calculado_por,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            
            # Información del animal
            'animal': {
                'hierro': self.animal.hierro if self.animal else None,
                'sexo': self.animal.sexo if self.animal else None,
                'raza': self.animal.raza if self.animal else None,
                'hacienda': self.animal.hacienda.nombre if self.animal and self.animal.hacienda else None
            } if self.animal else None,
            
            # Requerimientos NRC
            'requerimientos_nrc': self.nrc_ceba.to_dict() if self.nrc_ceba else None,
            
            'total_ingredientes': len(self.detalles) if self.detalles else 0
        }
        
        if include_detalles:
            data['detalles'] = [d.to_dict() for d in self.detalles]
        
        return data


class DetalleRacionLactancia(db.Model):
    """
    Modelo para ingredientes que componen una ración de lactancia
    """
    __tablename__ = 'detalle_racion_lactancia'
    
    iddetalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idracion_lactancia = db.Column(db.Integer, db.ForeignKey('raciones_lactancia.idracion_lactancia'), nullable=False)
    idingrediente = db.Column(db.Integer, db.ForeignKey('ingredientes.idingrediente'), nullable=False)
    cantidad_kg = db.Column(db.Numeric(8,3), nullable=False)
    porcentaje_racion = db.Column(db.Numeric(5,2), nullable=False)
    costo_kg = db.Column(db.Numeric(10,2), default=0)  # Costo por kg del ingrediente
    
    def __repr__(self):
        return f'<DetalleRacionLactancia {self.ingrediente.nombre_ingrediente if self.ingrediente else "N/A"} - {self.cantidad_kg}kg>'
    
    def to_dict(self):
        return {
            'iddetalle': self.iddetalle,
            'idracion_lactancia': self.idracion_lactancia,
            'idingrediente': self.idingrediente,
            'cantidad_kg': float(self.cantidad_kg),
            'porcentaje_racion': float(self.porcentaje_racion),
            'costo_kg': float(self.costo_kg) if self.costo_kg else 0,
            'costo_total': float(self.cantidad_kg * (self.costo_kg or 0)),
            'ingrediente': {
                'nombre': self.ingrediente.nombre_ingrediente if self.ingrediente else None,
                'tipo': self.ingrediente.tipo_ingrediente if self.ingrediente else None,
                'descripcion': self.ingrediente.descripcion if self.ingrediente else None
            } if self.ingrediente else None
        }
    
    def calcular_aporte_nutricional(self):
        """Calcula el aporte nutricional de este ingrediente en la ración"""
        if not self.ingrediente:
            return None
        
        caracteristica = self.ingrediente.obtener_caracteristica_promedio()
        if not caracteristica:
            return None
        
        cantidad_ms = self.cantidad_kg * (caracteristica['materia_seca'] / 100)
        
        return {
            'materia_seca_kg': cantidad_ms,
            'proteina_cruda_kg': cantidad_ms * (caracteristica['proteina_cruda'] / 100),
            'ndt_kg': cantidad_ms * (caracteristica['ndt'] / 100),
            'calcio_kg': cantidad_ms * (caracteristica['calcio'] / 100),
            'fosforo_kg': cantidad_ms * (caracteristica['fosforo'] / 100),
            'ed_mcal': cantidad_ms * caracteristica['ed_mcal_kg'],
            'em_mcal': cantidad_ms * caracteristica['em_mcal_kg']
        }


class DetalleRacionCeba(db.Model):
    """
    Modelo para ingredientes que componen una ración de ceba
    """
    __tablename__ = 'detalle_racion_ceba'
    
    iddetalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idracion_ceba = db.Column(db.Integer, db.ForeignKey('raciones_ceba.idracion_ceba'), nullable=False)
    idingrediente = db.Column(db.Integer, db.ForeignKey('ingredientes.idingrediente'), nullable=False)
    cantidad_kg = db.Column(db.Numeric(8,3), nullable=False)
    porcentaje_racion = db.Column(db.Numeric(5,2), nullable=False)
    costo_kg = db.Column(db.Numeric(10,2), default=0)
    
    def __repr__(self):
        return f'<DetalleRacionCeba {self.ingrediente.nombre_ingrediente if self.ingrediente else "N/A"} - {self.cantidad_kg}kg>'
    
    def to_dict(self):
        return {
            'iddetalle': self.iddetalle,
            'idracion_ceba': self.idracion_ceba,
            'idingrediente': self.idingrediente,
            'cantidad_kg': float(self.cantidad_kg),
            'porcentaje_racion': float(self.porcentaje_racion),
            'costo_kg': float(self.costo_kg) if self.costo_kg else 0,
            'costo_total': float(self.cantidad_kg * (self.costo_kg or 0)),
            'ingrediente': {
                'nombre': self.ingrediente.nombre_ingrediente if self.ingrediente else None,
                'tipo': self.ingrediente.tipo_ingrediente if self.ingrediente else None,
                'descripcion': self.ingrediente.descripcion if self.ingrediente else None
            } if self.ingrediente else None
        }
    
    def calcular_aporte_nutricional(self):
        """Calcula el aporte nutricional de este ingrediente en la ración"""
        if not self.ingrediente:
            return None
        
        caracteristica = self.ingrediente.obtener_caracteristica_promedio()
        if not caracteristica:
            return None
        
        cantidad_ms = self.cantidad_kg * (caracteristica['materia_seca'] / 100)
        
        return {
            'materia_seca_kg': cantidad_ms,
            'proteina_cruda_kg': cantidad_ms * (caracteristica['proteina_cruda'] / 100),
            'ndt_kg': cantidad_ms * (caracteristica['ndt'] / 100),
            'calcio_kg': cantidad_ms * (caracteristica['calcio'] / 100),
            'fosforo_kg': cantidad_ms * (caracteristica['fosforo'] / 100),
            'ed_mcal': cantidad_ms * caracteristica['ed_mcal_kg'],
            'em_mcal': cantidad_ms * caracteristica['em_mcal_kg']
        }