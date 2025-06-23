# models/nrc.py
from . import db
from datetime import datetime

class NrcLactanciaBase(db.Model):
    """
    Modelo para requerimientos base de lactancia por peso corporal (NRC)
    """
    __tablename__ = 'nrc_lactancia_base'
    
    idnrc_lactancia_base = db.Column(db.Integer, primary_key=True, autoincrement=True)
    peso_kg = db.Column(db.Numeric(6,2), nullable=False, unique=True)
    materia_seca_kg = db.Column(db.Numeric(6,3), nullable=False)
    proteina_total_kg = db.Column(db.Numeric(8,4), nullable=False)
    proteina_digestible_kg = db.Column(db.Numeric(8,4), nullable=False)
    en_mcal = db.Column(db.Numeric(8,3), nullable=False)
    ed_mcal = db.Column(db.Numeric(8,3), nullable=False)
    em_mcal = db.Column(db.Numeric(8,3), nullable=False)
    tnd_kg = db.Column(db.Numeric(6,3), nullable=False)
    calcio_kg = db.Column(db.Numeric(8,5), nullable=False)
    fosforo_kg = db.Column(db.Numeric(8,5), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NrcLactanciaBase {self.peso_kg}kg>'
    
    def to_dict(self):
        return {
            'idnrc_lactancia_base': self.idnrc_lactancia_base,
            'peso_kg': float(self.peso_kg),
            'materia_seca_kg': float(self.materia_seca_kg),
            'proteina_total_kg': float(self.proteina_total_kg),
            'proteina_digestible_kg': float(self.proteina_digestible_kg),
            'en_mcal': float(self.en_mcal),
            'ed_mcal': float(self.ed_mcal),
            'em_mcal': float(self.em_mcal),
            'tnd_kg': float(self.tnd_kg),
            'calcio_kg': float(self.calcio_kg),
            'fosforo_kg': float(self.fosforo_kg),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def obtener_por_peso(peso_kg):
        """Obtiene requerimientos por peso exacto o el más cercano"""
        # Buscar peso exacto
        nrc = NrcLactanciaBase.query.filter_by(peso_kg=peso_kg).first()
        if nrc:
            return nrc
        
        # Si no existe peso exacto, buscar el más cercano
        menor = NrcLactanciaBase.query.filter(NrcLactanciaBase.peso_kg <= peso_kg).order_by(NrcLactanciaBase.peso_kg.desc()).first()
        mayor = NrcLactanciaBase.query.filter(NrcLactanciaBase.peso_kg > peso_kg).order_by(NrcLactanciaBase.peso_kg.asc()).first()
        
        if menor and mayor:
            # Interpolación lineal
            return NrcLactanciaBase._interpolar_requerimientos(menor, mayor, peso_kg)
        elif menor:
            return menor
        elif mayor:
            return mayor
        
        return None
    
    @staticmethod
    def _interpolar_requerimientos(nrc_menor, nrc_mayor, peso_objetivo):
        """Interpolación lineal entre dos registros NRC"""
        factor = (peso_objetivo - nrc_menor.peso_kg) / (nrc_mayor.peso_kg - nrc_menor.peso_kg)
        
        # Crear objeto temporal con valores interpolados
        class NrcInterpolado:
            def __init__(self):
                self.peso_kg = peso_objetivo
                self.materia_seca_kg = nrc_menor.materia_seca_kg + factor * (nrc_mayor.materia_seca_kg - nrc_menor.materia_seca_kg)
                self.proteina_total_kg = nrc_menor.proteina_total_kg + factor * (nrc_mayor.proteina_total_kg - nrc_menor.proteina_total_kg)
                self.proteina_digestible_kg = nrc_menor.proteina_digestible_kg + factor * (nrc_mayor.proteina_digestible_kg - nrc_menor.proteina_digestible_kg)
                self.en_mcal = nrc_menor.en_mcal + factor * (nrc_mayor.en_mcal - nrc_menor.en_mcal)
                self.ed_mcal = nrc_menor.ed_mcal + factor * (nrc_mayor.ed_mcal - nrc_menor.ed_mcal)
                self.em_mcal = nrc_menor.em_mcal + factor * (nrc_mayor.em_mcal - nrc_menor.em_mcal)
                self.tnd_kg = nrc_menor.tnd_kg + factor * (nrc_mayor.tnd_kg - nrc_menor.tnd_kg)
                self.calcio_kg = nrc_menor.calcio_kg + factor * (nrc_mayor.calcio_kg - nrc_menor.calcio_kg)
                self.fosforo_kg = nrc_menor.fosforo_kg + factor * (nrc_mayor.fosforo_kg - nrc_menor.fosforo_kg)
        
        return NrcInterpolado()


class NrcProduccionLeche(db.Model):
    """
    Modelo para requerimientos por kilogramo de leche producida según % grasa
    """
    __tablename__ = 'nrc_produccion_leche'
    
    idnrc_produccion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    porcentaje_grasa = db.Column(db.Numeric(3,1), nullable=False, unique=True)
    proteina_total_kg = db.Column(db.Numeric(8,4), nullable=False)
    proteina_digestible_kg = db.Column(db.Numeric(8,4), nullable=False)
    en_mcal = db.Column(db.Numeric(8,3), nullable=False)
    ed_mcal = db.Column(db.Numeric(8,3), nullable=False)
    em_mcal = db.Column(db.Numeric(8,3), nullable=False)
    tnd_kg = db.Column(db.Numeric(8,4), nullable=False)
    calcio_kg = db.Column(db.Numeric(8,5), nullable=False)
    fosforo_kg = db.Column(db.Numeric(8,5), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NrcProduccionLeche {self.porcentaje_grasa}% grasa>'
    
    def to_dict(self):
        return {
            'idnrc_produccion': self.idnrc_produccion,
            'porcentaje_grasa': float(self.porcentaje_grasa),
            'proteina_total_kg': float(self.proteina_total_kg),
            'proteina_digestible_kg': float(self.proteina_digestible_kg),
            'en_mcal': float(self.en_mcal),
            'ed_mcal': float(self.ed_mcal),
            'em_mcal': float(self.em_mcal),
            'tnd_kg': float(self.tnd_kg),
            'calcio_kg': float(self.calcio_kg),
            'fosforo_kg': float(self.fosforo_kg),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def obtener_por_grasa(porcentaje_grasa):
        """Obtiene requerimientos por % grasa exacto o interpolado"""
        # Buscar porcentaje exacto
        nrc = NrcProduccionLeche.query.filter_by(porcentaje_grasa=porcentaje_grasa).first()
        if nrc:
            return nrc
        
        # Interpolación si no existe el porcentaje exacto
        menor = NrcProduccionLeche.query.filter(NrcProduccionLeche.porcentaje_grasa <= porcentaje_grasa).order_by(NrcProduccionLeche.porcentaje_grasa.desc()).first()
        mayor = NrcProduccionLeche.query.filter(NrcProduccionLeche.porcentaje_grasa > porcentaje_grasa).order_by(NrcProduccionLeche.porcentaje_grasa.asc()).first()
        
        if menor and mayor:
            return NrcProduccionLeche._interpolar_por_grasa(menor, mayor, porcentaje_grasa)
        elif menor:
            return menor
        elif mayor:
            return mayor
        
        return None
    
    @staticmethod
    def _interpolar_por_grasa(nrc_menor, nrc_mayor, grasa_objetivo):
        """Interpolación lineal entre dos registros por % grasa"""
        factor = (grasa_objetivo - nrc_menor.porcentaje_grasa) / (nrc_mayor.porcentaje_grasa - nrc_menor.porcentaje_grasa)
        
        class NrcGrasaInterpolado:
            def __init__(self):
                self.porcentaje_grasa = grasa_objetivo
                self.proteina_total_kg = nrc_menor.proteina_total_kg + factor * (nrc_mayor.proteina_total_kg - nrc_menor.proteina_total_kg)
                self.proteina_digestible_kg = nrc_menor.proteina_digestible_kg + factor * (nrc_mayor.proteina_digestible_kg - nrc_menor.proteina_digestible_kg)
                self.en_mcal = nrc_menor.en_mcal + factor * (nrc_mayor.en_mcal - nrc_menor.en_mcal)
                self.ed_mcal = nrc_menor.ed_mcal + factor * (nrc_mayor.ed_mcal - nrc_menor.ed_mcal)
                self.em_mcal = nrc_menor.em_mcal + factor * (nrc_mayor.em_mcal - nrc_menor.em_mcal)
                self.tnd_kg = nrc_menor.tnd_kg + factor * (nrc_mayor.tnd_kg - nrc_menor.tnd_kg)
                self.calcio_kg = nrc_menor.calcio_kg + factor * (nrc_mayor.calcio_kg - nrc_menor.calcio_kg)
                self.fosforo_kg = nrc_menor.fosforo_kg + factor * (nrc_mayor.fosforo_kg - nrc_menor.fosforo_kg)
        
        return NrcGrasaInterpolado()


class NrcGestacion(db.Model):
    """
    Modelo para requerimientos adicionales por gestación (últimos 2 meses)
    """
    __tablename__ = 'nrc_gestacion'
    
    idnrc_gestacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    peso_kg = db.Column(db.Numeric(6,2), nullable=False, unique=True)
    materia_seca_kg = db.Column(db.Numeric(6,3), nullable=False)
    proteina_total_kg = db.Column(db.Numeric(8,4), nullable=False)
    proteina_digestible_kg = db.Column(db.Numeric(8,4), nullable=False)
    en_mcal = db.Column(db.Numeric(8,3), nullable=False)
    ed_mcal = db.Column(db.Numeric(8,3), nullable=False)
    em_mcal = db.Column(db.Numeric(8,3), nullable=False)
    tnd_kg = db.Column(db.Numeric(6,3), nullable=False)
    calcio_kg = db.Column(db.Numeric(8,5), nullable=False)
    fosforo_kg = db.Column(db.Numeric(8,5), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NrcGestacion {self.peso_kg}kg>'
    
    def to_dict(self):
        return {
            'idnrc_gestacion': self.idnrc_gestacion,
            'peso_kg': float(self.peso_kg),
            'materia_seca_kg': float(self.materia_seca_kg),
            'proteina_total_kg': float(self.proteina_total_kg),
            'proteina_digestible_kg': float(self.proteina_digestible_kg),
            'en_mcal': float(self.en_mcal),
            'ed_mcal': float(self.ed_mcal),
            'em_mcal': float(self.em_mcal),
            'tnd_kg': float(self.tnd_kg),
            'calcio_kg': float(self.calcio_kg),
            'fosforo_kg': float(self.fosforo_kg),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def obtener_por_peso(peso_kg):
        """Obtiene requerimientos de gestación por peso"""
        nrc = NrcGestacion.query.filter_by(peso_kg=peso_kg).first()
        if nrc:
            return nrc
        
        # Interpolación si no existe peso exacto
        menor = NrcGestacion.query.filter(NrcGestacion.peso_kg <= peso_kg).order_by(NrcGestacion.peso_kg.desc()).first()
        mayor = NrcGestacion.query.filter(NrcGestacion.peso_kg > peso_kg).order_by(NrcGestacion.peso_kg.asc()).first()
        
        if menor and mayor:
            return NrcGestacion._interpolar_gestacion(menor, mayor, peso_kg)
        elif menor:
            return menor
        elif mayor:
            return mayor
        
        return None
    
    @staticmethod
    def _interpolar_gestacion(nrc_menor, nrc_mayor, peso_objetivo):
        """Interpolación lineal para gestación"""
        factor = (peso_objetivo - nrc_menor.peso_kg) / (nrc_mayor.peso_kg - nrc_menor.peso_kg)
        
        class NrcGestacionInterpolado:
            def __init__(self):
                self.peso_kg = peso_objetivo
                self.materia_seca_kg = nrc_menor.materia_seca_kg + factor * (nrc_mayor.materia_seca_kg - nrc_menor.materia_seca_kg)
                self.proteina_total_kg = nrc_menor.proteina_total_kg + factor * (nrc_mayor.proteina_total_kg - nrc_menor.proteina_total_kg)
                self.proteina_digestible_kg = nrc_menor.proteina_digestible_kg + factor * (nrc_mayor.proteina_digestible_kg - nrc_menor.proteina_digestible_kg)
                self.en_mcal = nrc_menor.en_mcal + factor * (nrc_mayor.en_mcal - nrc_menor.en_mcal)
                self.ed_mcal = nrc_menor.ed_mcal + factor * (nrc_mayor.ed_mcal - nrc_menor.ed_mcal)
                self.em_mcal = nrc_menor.em_mcal + factor * (nrc_mayor.em_mcal - nrc_menor.em_mcal)
                self.tnd_kg = nrc_menor.tnd_kg + factor * (nrc_mayor.tnd_kg - nrc_menor.tnd_kg)
                self.calcio_kg = nrc_menor.calcio_kg + factor * (nrc_mayor.calcio_kg - nrc_menor.calcio_kg)
                self.fosforo_kg = nrc_menor.fosforo_kg + factor * (nrc_mayor.fosforo_kg - nrc_menor.fosforo_kg)
        
        return NrcGestacionInterpolado()


class NrcCeba(db.Model):
    """
    Modelo para requerimientos de animales en ceba
    """
    __tablename__ = 'nrc_ceba'
    
    idnrc_ceba = db.Column(db.Integer, primary_key=True, autoincrement=True)
    peso_minimo = db.Column(db.Numeric(6,2), nullable=False)
    peso_maximo = db.Column(db.Numeric(6,2), nullable=False)
    gdp_min = db.Column(db.Numeric(5,3), nullable=False)  # Ganancia diaria de peso mínima
    gdp_max = db.Column(db.Numeric(5,3), nullable=False)  # Ganancia diaria de peso máxima
    pb_g = db.Column(db.Numeric(8,2), nullable=False)     # Proteína bruta en gramos
    pd_g = db.Column(db.Numeric(8,2), nullable=False)     # Proteína digestible en gramos
    em_mcal = db.Column(db.Numeric(8,3), nullable=False)  # Energía metabolizable
    ca_g = db.Column(db.Numeric(8,2), nullable=False)     # Calcio en gramos
    p_g = db.Column(db.Numeric(8,2), nullable=False)      # Fósforo en gramos
    ms_kg = db.Column(db.Numeric(6,2), nullable=False)    # Materia seca en kg
    
    def __repr__(self):
        return f'<NrcCeba {self.peso_minimo}-{self.peso_maximo}kg>'
    
    def to_dict(self):
        return {
            'idnrc_ceba': self.idnrc_ceba,
            'peso_minimo': float(self.peso_minimo),
            'peso_maximo': float(self.peso_maximo),
            'gdp_min': float(self.gdp_min),
            'gdp_max': float(self.gdp_max),
            'pb_g': float(self.pb_g),
            'pd_g': float(self.pd_g),
            'em_mcal': float(self.em_mcal),
            'ca_g': float(self.ca_g),
            'p_g': float(self.p_g),
            'ms_kg': float(self.ms_kg)
        }
    
    @staticmethod
    def obtener_por_peso(peso_kg):
        """Obtiene requerimientos de ceba para un peso específico"""
        return NrcCeba.query.filter(
            NrcCeba.peso_minimo <= peso_kg,
            NrcCeba.peso_maximo >= peso_kg
        ).first()
    
    @staticmethod
    def obtener_por_peso_y_gdp(peso_kg, gdp_objetivo):
        """Obtiene requerimientos considerando peso y ganancia diaria objetivo"""
        return NrcCeba.query.filter(
            NrcCeba.peso_minimo <= peso_kg,
            NrcCeba.peso_maximo >= peso_kg,
            NrcCeba.gdp_min <= gdp_objetivo,
            NrcCeba.gdp_max >= gdp_objetivo
        ).first()