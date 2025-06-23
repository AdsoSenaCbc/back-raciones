from . import db
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, func

class Animal(db.Model):
    """
    Modelo para la tabla animales
    Representa los animales registrados en las haciendas
    """
    __tablename__ = 'animales'
    
    # Campos de la tabla
    idanimal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idhacienda = db.Column(db.Integer, db.ForeignKey('haciendas.idhacienda'), nullable=False)
    idestado = db.Column(db.Integer, db.ForeignKey('estados_animal.idestado'), default=1)
    hierro = db.Column(db.String(20), nullable=False)
    sexo = db.Column(db.Enum('Macho', 'Hembra', name='sexo_enum'), nullable=False)
    raza = db.Column(db.String(50))
    peso_actual = db.Column(db.Numeric(8, 2))
    fecha_nacimiento = db.Column(db.Date)
    numero_partos = db.Column(db.Integer, default=0)
    ultimo_parto = db.Column(db.Date)
    ultimo_aborto = db.Column(db.Date)
    preñada = db.Column(db.Boolean, default=False)
    fecha_preñez = db.Column(db.Date)
    preñada_por = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraint único para hierro por hacienda
    __table_args__ = (
        db.UniqueConstraint('idhacienda', 'hierro', name='unique_hierro_hacienda'),
    )
    
    # Relación con vacunaciones
    vacunaciones = db.relationship('VacunacionAnimal', backref='animal', lazy=True, cascade='all, delete-orphan')
    
    # NUEVAS RELACIONES CON NACIMIENTOS
    # Relación cuando el animal es una cría
    nacimiento_cria = db.relationship('Nacimiento', foreign_keys='Nacimiento.idanimal_cria', 
                                   back_populates='cria', uselist=False, lazy=True)
    
    # Relación cuando el animal es madre
    nacimientos_como_madre = db.relationship('Nacimiento', foreign_keys='Nacimiento.idanimal_madre', 
                                           backref='madre', lazy=True, cascade='all, delete-orphan')
    
    # Relación cuando el animal es padre
    nacimientos_como_padre = db.relationship('Nacimiento', foreign_keys='Nacimiento.idanimal_padre', 
                                           backref='padre', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Animal {self.hierro} - {self.sexo}>'
    
    def to_dict(self, include_sensitive=False, include_vacunacion=False, include_nacimientos=False):
        """Convierte el objeto a diccionario para JSON"""
        data = {
            'idanimal': self.idanimal,
            'idhacienda': self.idhacienda,
            'idestado': self.idestado,
            'hierro': self.hierro,
            'sexo': self.sexo,
            'raza': self.raza,
            'peso_actual': float(self.peso_actual) if self.peso_actual else None,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'numero_partos': self.numero_partos,
            'ultimo_parto': self.ultimo_parto.isoformat() if self.ultimo_parto else None,
            'ultimo_aborto': self.ultimo_aborto.isoformat() if self.ultimo_aborto else None,
            'preñada': self.preñada,
            'fecha_preñez': self.fecha_preñez.isoformat() if self.fecha_preñez else None,
            'preñada_por': self.preñada_por,
            'observaciones': self.observaciones,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            # Información relacionada
            'hacienda_nombre': self.hacienda.nombre if self.hacienda else None,
            'estado_nombre': self.estado.nombre_estado if self.estado else None,
            'edad_aproximada': self.calcular_edad()
        }
        
        # Incluir información de vacunación si se solicita
        if include_vacunacion:
            data['estadisticas_vacunacion'] = self.estadisticas_vacunacion()
            data['proximas_vacunas'] = len(self.obtener_proximas_vacunas(30))
            data['total_vacunaciones'] = len(self.vacunaciones) if self.vacunaciones else 0
        
        # NUEVA: Incluir información de nacimientos si se solicita
        if include_nacimientos:
            data['estadisticas_nacimientos'] = self.estadisticas_nacimientos()
            if self.sexo == 'Hembra':
                data['total_crias'] = len(self.nacimientos_como_madre) if self.nacimientos_como_madre else 0
                data['ultima_cria'] = self.obtener_ultima_cria()
            if self.sexo == 'Macho':
                data['total_descendencia'] = len(self.nacimientos_como_padre) if self.nacimientos_como_padre else 0
            
            # Información del propio nacimiento si existe
            if self.nacimiento_cria:
                data['datos_nacimiento'] = {
                    'fecha_nacimiento': self.nacimiento_cria.fecha_nacimiento.isoformat() if self.nacimiento_cria.fecha_nacimiento else None,
                    'peso_nacimiento': float(self.nacimiento_cria.peso_nacimiento) if self.nacimiento_cria.peso_nacimiento else None,
                    'tipo_parto': self.nacimiento_cria.tipo_parto,
                    'madre_hierro': self.nacimiento_cria.madre.hierro if self.nacimiento_cria.madre else None,
                    'padre_hierro': self.nacimiento_cria.padre.hierro if self.nacimiento_cria.padre else None,
                }
        
        return data
    
    def calcular_edad(self):
        """Calcula la edad aproximada del animal en años"""
        if not self.fecha_nacimiento:
            return None
        
        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year
        
        # Ajustar si aún no ha cumplido años este año
        if hoy.month < self.fecha_nacimiento.month or \
           (hoy.month == self.fecha_nacimiento.month and hoy.day < self.fecha_nacimiento.day):
            edad -= 1
            
        return max(0, edad)
    
    def es_hembra_reproductiva(self):
        """Verifica si es una hembra en edad reproductiva"""
        if self.sexo != 'Hembra':
            return False
        
        edad = self.calcular_edad()
        if not edad:
            return False
            
        # Consideramos reproductiva entre 2 y 15 años aproximadamente
        return 2 <= edad <= 15
    
    def dias_desde_ultimo_parto(self):
        """Calcula días desde el último parto"""
        if not self.ultimo_parto:
            return None
        
        return (date.today() - self.ultimo_parto).days
    
    def dias_gestacion(self):
        """Calcula días de gestación si está preñada"""
        if not self.preñada or not self.fecha_preñez:
            return None
            
        return (date.today() - self.fecha_preñez).days
    
    def actualizar_estado(self, nuevo_estado_id):
        """Actualiza el estado del animal"""
        self.idestado = nuevo_estado_id
        db.session.commit()
    
    def marcar_preñada(self, fecha_preñez, preñada_por=None):
        """Marca el animal como preñado"""
        if self.sexo != 'Hembra':
            raise ValueError("Solo las hembras pueden estar preñadas")
        
        self.preñada = True
        self.fecha_preñez = fecha_preñez
        self.preñada_por = preñada_por
        db.session.commit()
    
    def registrar_parto(self, fecha_parto):
        """Registra un parto"""
        if self.sexo != 'Hembra':
            raise ValueError("Solo las hembras pueden parir")
        
        self.ultimo_parto = fecha_parto
        self.numero_partos += 1
        self.preñada = False
        self.fecha_preñez = None
        self.preñada_por = None
        db.session.commit()
    
    def registrar_aborto(self, fecha_aborto):
        """Registra un aborto"""
        if self.sexo != 'Hembra':
            raise ValueError("Solo las hembras pueden abortar")
        
        self.ultimo_aborto = fecha_aborto
        self.preñada = False
        self.fecha_preñez = None
        self.preñada_por = None
        db.session.commit()
    
    # ===============================
    # NUEVOS MÉTODOS DE NACIMIENTOS
    # ===============================
    
    def obtener_crias(self):
        """Obtiene todas las crías de este animal (si es hembra)"""
        if self.sexo != 'Hembra':
            return []
        return self.nacimientos_como_madre or []
    
    def obtener_descendencia(self):
        """Obtiene toda la descendencia de este animal (si es macho)"""
        if self.sexo != 'Macho':
            return []
        return self.nacimientos_como_padre or []
    
    def obtener_ultima_cria(self):
        """Obtiene información de la última cría"""
        if self.sexo != 'Hembra' or not self.nacimientos_como_madre:
            return None
        
        ultimo_nacimiento = max(self.nacimientos_como_madre, 
                               key=lambda n: n.fecha_nacimiento)
        
        return {
            'fecha_nacimiento': ultimo_nacimiento.fecha_nacimiento.isoformat(),
            'cria_hierro': ultimo_nacimiento.cria.hierro if ultimo_nacimiento.cria else None,
            'peso_nacimiento': float(ultimo_nacimiento.peso_nacimiento) if ultimo_nacimiento.peso_nacimiento else None,
            'tipo_parto': ultimo_nacimiento.tipo_parto,
            'edad_dias': ultimo_nacimiento.calcular_edad_dias()
        }
    
    def es_apta_para_monta(self):
        """Verifica si una hembra está apta para monta"""
        if self.sexo != 'Hembra':
            return False, "Solo aplica para hembras"
        
        if self.preñada:
            return False, "Actualmente preñada"
        
        if not self.es_hembra_reproductiva():
            return False, "Fuera del rango de edad reproductiva"
        
        # Verificar tiempo desde último parto
        if self.ultimo_parto:
            dias_desde_parto = self.dias_desde_ultimo_parto()
            if dias_desde_parto and dias_desde_parto < 60:  # Mínimo 2 meses
                return False, f"Muy poco tiempo desde último parto ({dias_desde_parto} días)"
        
        return True, "Apta para monta"
    
    def calcular_productividad_reproductiva(self):
        """Calcula métricas de productividad reproductiva"""
        if self.sexo != 'Hembra':
            return None
        
        edad = self.calcular_edad()
        if not edad or edad < 2:
            return None
        
        # Años reproductivos (desde los 2 años)
        años_reproductivos = max(0, edad - 2)
        
        # Intervalo entre partos promedio
        intervalo_promedio = None
        if self.numero_partos > 1 and self.nacimientos_como_madre:
            nacimientos_ordenados = sorted(self.nacimientos_como_madre, 
                                         key=lambda n: n.fecha_nacimiento)
            if len(nacimientos_ordenados) >= 2:
                primer_parto = nacimientos_ordenados[0].fecha_nacimiento
                ultimo_parto = nacimientos_ordenados[-1].fecha_nacimiento
                dias_total = (ultimo_parto - primer_parto).days
                intervalo_promedio = dias_total / (len(nacimientos_ordenados) - 1)
        
        return {
            'edad_años': edad,
            'años_reproductivos': años_reproductivos,
            'total_partos': self.numero_partos,
            'partos_por_año': round(self.numero_partos / años_reproductivos, 2) if años_reproductivos > 0 else 0,
            'intervalo_promedio_dias': round(intervalo_promedio) if intervalo_promedio else None,
            'eficiencia_reproductiva': 'Alta' if self.numero_partos / años_reproductivos > 0.8 else 'Media' if self.numero_partos / años_reproductivos > 0.5 else 'Baja' if años_reproductivos > 0 else 'Sin datos'
        }
    
    def estadisticas_nacimientos(self):
        """Obtiene estadísticas de nacimientos relacionadas con este animal"""
        stats = {
            'como_cria': None,
            'como_madre': None,
            'como_padre': None
        }
        
        # Como cría
        if self.nacimiento_cria:
            stats['como_cria'] = {
                'tiene_registro_nacimiento': True,
                'fecha_nacimiento': self.nacimiento_cria.fecha_nacimiento.isoformat(),
                'peso_nacimiento': float(self.nacimiento_cria.peso_nacimiento) if self.nacimiento_cria.peso_nacimiento else None,
                'tipo_parto': self.nacimiento_cria.tipo_parto,
                'edad_actual_dias': self.nacimiento_cria.calcular_edad_dias()
            }
        else:
            stats['como_cria'] = {'tiene_registro_nacimiento': False}
        
        # Como madre
        if self.sexo == 'Hembra':
            crias = self.obtener_crias()
            stats['como_madre'] = {
                'total_crias': len(crias),
                'partos_registrados': len(crias),
                'ultima_cria': self.obtener_ultima_cria(),
                'productividad': self.calcular_productividad_reproductiva()
            }
        
        # Como padre
        if self.sexo == 'Macho':
            descendencia = self.obtener_descendencia()
            stats['como_padre'] = {
                'total_descendencia': len(descendencia),
                'crias_registradas': len(descendencia)
            }
        
        return stats
    
    # ===============================
    # MÉTODOS DE VACUNACIÓN (EXISTENTES)
    # ===============================
    
    def obtener_vacunaciones(self, incluir_vencidas=True):
        """Obtiene las vacunaciones del animal"""
        from .vacunacion_animal import VacunacionAnimal
        return VacunacionAnimal.obtener_por_animal(self.idanimal, incluir_vencidas)
    
    def obtener_proximas_vacunas(self, dias_adelante=30):
        """Obtiene las próximas vacunas que necesita el animal"""
        from .vacunacion_animal import VacunacionAnimal
        
        fecha_limite = date.today() + timedelta(days=dias_adelante)
        
        return VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.idanimal == self.idanimal,
                VacunacionAnimal.proxima_dosis.isnot(None),
                VacunacionAnimal.proxima_dosis <= fecha_limite
            )
        ).order_by(VacunacionAnimal.proxima_dosis).all()
    
    def obtener_vacunas_vencidas(self):
        """Obtiene las vacunas vencidas del animal"""
        from .vacunacion_animal import VacunacionAnimal
        
        hoy = date.today()
        
        return VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.idanimal == self.idanimal,
                VacunacionAnimal.proxima_dosis.isnot(None),
                VacunacionAnimal.proxima_dosis < hoy
            )
        ).order_by(VacunacionAnimal.proxima_dosis).all()
    
    def tiene_vacuna_vigente(self, idvacuna):
        """Verifica si el animal tiene una vacuna específica vigente"""
        from .vacunacion_animal import VacunacionAnimal
        
        hoy = date.today()
        
        vacunacion = VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.idanimal == self.idanimal,
                VacunacionAnimal.idvacuna == idvacuna,
                or_(
                    VacunacionAnimal.proxima_dosis.is_(None),
                    VacunacionAnimal.proxima_dosis >= hoy
                )
            )
        ).order_by(VacunacionAnimal.fecha_aplicacion.desc()).first()
        
        return vacunacion is not None
    
    def obtener_ultima_vacunacion(self, idvacuna):
        """Obtiene la última vacunación de una vacuna específica"""
        from .vacunacion_animal import VacunacionAnimal
        
        return VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.idanimal == self.idanimal,
                VacunacionAnimal.idvacuna == idvacuna
            )
        ).order_by(VacunacionAnimal.fecha_aplicacion.desc()).first()
    
    def necesita_vacuna(self, idvacuna, dias_anticipacion=30):
        """Verifica si el animal necesita una vacuna específica"""
        ultima_vacunacion = self.obtener_ultima_vacunacion(idvacuna)
        
        if not ultima_vacunacion:
            return True, "Nunca ha sido vacunado"
        
        if not ultima_vacunacion.proxima_dosis:
            return False, "Sin próxima dosis programada"
        
        fecha_limite = date.today() + timedelta(days=dias_anticipacion)
        
        if ultima_vacunacion.proxima_dosis <= fecha_limite:
            dias_restantes = (ultima_vacunacion.proxima_dosis - date.today()).days
            
            if dias_restantes < 0:
                return True, f"Vacuna vencida hace {abs(dias_restantes)} días"
            elif dias_restantes == 0:
                return True, "Vacuna vence hoy"
            else:
                return True, f"Vacuna vence en {dias_restantes} días"
        
        return False, f"Vigente hasta {ultima_vacunacion.proxima_dosis.isoformat()}"
    
    def obtener_calendario_vacunacion(self, meses_adelante=12):
        """Obtiene el calendario de vacunación del animal"""
        from .vacunacion_animal import VacunacionAnimal
        from .catalogo_vacuna import CatalogoVacuna
        
        fecha_limite = date.today() + timedelta(days=meses_adelante * 30)
        
        # Obtener todas las vacunas activas
        vacunas_activas = CatalogoVacuna.obtener_activas()
        
        calendario = []
        
        for vacuna in vacunas_activas:
            ultima_vacunacion = self.obtener_ultima_vacunacion(vacuna.idvacuna)
            
            if ultima_vacunacion and ultima_vacunacion.proxima_dosis:
                if ultima_vacunacion.proxima_dosis <= fecha_limite:
                    calendario.append({
                        'vacuna': vacuna.to_dict(),
                        'fecha_programada': ultima_vacunacion.proxima_dosis.isoformat(),
                        'ultima_aplicacion': ultima_vacunacion.fecha_aplicacion.isoformat(),
                        'estado': self.necesita_vacuna(vacuna.idvacuna)[1],
                        'urgencia': self._calcular_urgencia_vacuna(ultima_vacunacion.proxima_dosis)
                    })
            else:
                # Animal nunca vacunado con esta vacuna
                calendario.append({
                    'vacuna': vacuna.to_dict(),
                    'fecha_programada': None,
                    'ultima_aplicacion': None,
                    'estado': 'Nunca vacunado',
                    'urgencia': 'alta'
                })
        
        # Ordenar por urgencia y fecha
        orden_urgencia = {'alta': 0, 'media': 1, 'baja': 2}
        calendario.sort(key=lambda x: (
            orden_urgencia.get(x['urgencia'], 3),
            x['fecha_programada'] or '9999-12-31'
        ))
        
        return calendario
    
    def _calcular_urgencia_vacuna(self, fecha_proxima):
        """Calcula la urgencia de una vacuna basada en la fecha"""
        if not fecha_proxima:
            return 'alta'
        
        dias_restantes = (fecha_proxima - date.today()).days
        
        if dias_restantes < 0:
            return 'alta'  # Vencida
        elif dias_restantes <= 7:
            return 'alta'  # Próxima semana
        elif dias_restantes <= 30:
            return 'media'  # Próximo mes
        else:
            return 'baja'  # Más de un mes
    
    def estadisticas_vacunacion(self):
        """Obtiene estadísticas de vacunación del animal"""
        from .vacunacion_animal import VacunacionAnimal
        
        total_vacunaciones = VacunacionAnimal.query.filter_by(idanimal=self.idanimal).count()
        
        # Próximas en 30 días
        proximas = len(self.obtener_proximas_vacunas(30))
        
        # Vencidas
        vencidas = len(self.obtener_vacunas_vencidas())
        
        # Última vacunación
        ultima_vacunacion = VacunacionAnimal.query.filter_by(
            idanimal=self.idanimal
        ).order_by(VacunacionAnimal.fecha_aplicacion.desc()).first()
        
        # Vacunas aplicadas este año
        inicio_año = date(date.today().year, 1, 1)
        vacunaciones_año = VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.idanimal == self.idanimal,
                VacunacionAnimal.fecha_aplicacion >= inicio_año
            )
        ).count()
        
        return {
            'total_vacunaciones': total_vacunaciones,
            'proximas_30_dias': proximas,
            'dosis_vencidas': vencidas,
            'vacunaciones_este_año': vacunaciones_año,
            'ultima_vacunacion': {
                'fecha': ultima_vacunacion.fecha_aplicacion.isoformat() if ultima_vacunacion else None,
                'vacuna': ultima_vacunacion.vacuna.nombre_vacuna if ultima_vacunacion and ultima_vacunacion.vacuna else None
            }
        }
    
    def obtener_historial_vacunacion_completo(self):
        """Obtiene el historial completo de vacunación organizado por vacuna"""
        from .vacunacion_animal import VacunacionAnimal
        from .catalogo_vacuna import CatalogoVacuna
        
        # Obtener todas las vacunaciones del animal
        vacunaciones = VacunacionAnimal.query.filter_by(
            idanimal=self.idanimal
        ).join(CatalogoVacuna).order_by(
            CatalogoVacuna.nombre_vacuna,
            VacunacionAnimal.fecha_aplicacion.desc()
        ).all()
        
        # Agrupar por vacuna
        historial = {}
        for vacunacion in vacunaciones:
            vacuna_nombre = vacunacion.vacuna.nombre_vacuna
            
            if vacuna_nombre not in historial:
                historial[vacuna_nombre] = {
                    'vacuna': vacunacion.vacuna.to_dict(),
                    'aplicaciones': [],
                    'total_aplicaciones': 0,
                    'ultima_aplicacion': None,
                    'proxima_dosis': None,
                    'estado_actual': 'vigente'
                }
            
            aplicacion_data = vacunacion.to_dict(include_related=False)
            historial[vacuna_nombre]['aplicaciones'].append(aplicacion_data)
            historial[vacuna_nombre]['total_aplicaciones'] += 1
            
            # Actualizar información de la más reciente
            if not historial[vacuna_nombre]['ultima_aplicacion']:
                historial[vacuna_nombre]['ultima_aplicacion'] = aplicacion_data['fecha_aplicacion']
                historial[vacuna_nombre]['proxima_dosis'] = aplicacion_data['proxima_dosis']
                
                # Determinar estado actual
                if vacunacion.proxima_dosis:
                    if vacunacion.proxima_dosis < date.today():
                        historial[vacuna_nombre]['estado_actual'] = 'vencida'
                    elif vacunacion.proxima_dosis <= date.today() + timedelta(days=30):
                        historial[vacuna_nombre]['estado_actual'] = 'proxima'
                    else:
                        historial[vacuna_nombre]['estado_actual'] = 'vigente'
                else:
                    historial[vacuna_nombre]['estado_actual'] = 'sin_programar'
        
        return historial
    
    # ===============================
    # MÉTODOS ESTÁTICOS ORIGINALES + ACTUALIZADOS
    # ===============================
    
    @staticmethod
    def buscar_por_hierro(hacienda_id, hierro):
        """Busca un animal por hierro en una hacienda específica"""
        return Animal.query.filter_by(idhacienda=hacienda_id, hierro=hierro).first()
    
    @staticmethod
    def buscar_por_hacienda(hacienda_id, filtros=None):
        """Busca animales de una hacienda con filtros opcionales"""
        query = Animal.query.filter_by(idhacienda=hacienda_id)
        
        if filtros:
            if filtros.get('sexo'):
                query = query.filter(Animal.sexo == filtros['sexo'])
            
            if filtros.get('estado'):
                query = query.filter(Animal.idestado == filtros['estado'])
            
            if filtros.get('raza'):
                query = query.filter(Animal.raza.ilike(f"%{filtros['raza']}%"))
            
            if filtros.get('preñada') is not None:
                query = query.filter(Animal.preñada == filtros['preñada'])
        
        return query.order_by(Animal.hierro).all()
    
    @staticmethod
    def obtener_estadisticas_hacienda(hacienda_id):
        """Obtiene estadísticas de animales por hacienda (ACTUALIZADO CON NACIMIENTOS)"""
        total = Animal.query.filter_by(idhacienda=hacienda_id).count()
        
        # Por sexo
        machos = Animal.query.filter_by(idhacienda=hacienda_id, sexo='Macho').count()
        hembras = Animal.query.filter_by(idhacienda=hacienda_id, sexo='Hembra').count()
        
        # Por estado
        por_estado = db.session.query(
            Animal.idestado,
            func.count(Animal.idanimal).label('cantidad')
        ).filter_by(idhacienda=hacienda_id).group_by(Animal.idestado).all()
        
        # Hembras preñadas
        preñadas = Animal.query.filter_by(
            idhacienda=hacienda_id,
            sexo='Hembra',
            preñada=True
        ).count()
        
        # Peso promedio
        peso_promedio = db.session.query(
            func.avg(Animal.peso_actual)
        ).filter(
            and_(Animal.idhacienda == hacienda_id, Animal.peso_actual.isnot(None))
        ).scalar()
        
        # Estadísticas de vacunación
        try:
            from .vacunacion_animal import VacunacionAnimal
            
            total_vacunaciones = db.session.query(
                func.count(VacunacionAnimal.idvacunacion)
            ).join(Animal).filter(Animal.idhacienda == hacienda_id).scalar() or 0
            
            animales_al_dia = db.session.query(
                func.count(func.distinct(Animal.idanimal))
            ).outerjoin(VacunacionAnimal).filter(
                and_(
                    Animal.idhacienda == hacienda_id,
                    or_(
                        VacunacionAnimal.proxima_dosis.is_(None),
                        VacunacionAnimal.proxima_dosis >= date.today()
                    )
                )
            ).scalar() or 0
            
            proximas_vacunaciones = db.session.query(
                func.count(VacunacionAnimal.idvacunacion)
            ).join(Animal).filter(
                and_(
                    Animal.idhacienda == hacienda_id,
                    VacunacionAnimal.proxima_dosis.isnot(None),
                    VacunacionAnimal.proxima_dosis <= date.today() + timedelta(days=30),
                    VacunacionAnimal.proxima_dosis >= date.today()
                )
            ).scalar() or 0
            
        except ImportError:
            total_vacunaciones = 0
            animales_al_dia = 0
            proximas_vacunaciones = 0
        
        # NUEVAS ESTADÍSTICAS DE NACIMIENTOS
        try:
            from .nacimiento import Nacimiento
            
            # Total de nacimientos en la hacienda
            total_nacimientos = db.session.query(
                func.count(Nacimiento.idnacimiento)
            ).join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
                Animal.idhacienda == hacienda_id
            ).scalar() or 0
            
            # Nacimientos este año
            inicio_año = date(date.today().year, 1, 1)
            nacimientos_año = db.session.query(
                func.count(Nacimiento.idnacimiento)
            ).join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
                and_(
                    Animal.idhacienda == hacienda_id,
                    Nacimiento.fecha_nacimiento >= inicio_año
                )
            ).scalar() or 0
            
            # Crías sin vacunar
            crias_sin_vacunar = db.session.query(
                func.count(Nacimiento.idnacimiento)
            ).join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
                and_(
                    Animal.idhacienda == hacienda_id,
                    Nacimiento.vacunas_aplicadas == False,
                    Nacimiento.fecha_nacimiento <= date.today() - timedelta(days=90)
                )
            ).scalar() or 0
            
        except ImportError:
            total_nacimientos = 0
            nacimientos_año = 0
            crias_sin_vacunar = 0
        
        return {
            'total_animales': total,
            'machos': machos,
            'hembras': hembras,
            'preñadas': preñadas,
            'peso_promedio': float(peso_promedio) if peso_promedio else 0,
            'por_estado': [
                {'idestado': estado, 'cantidad': cantidad}
                for estado, cantidad in por_estado
            ],
            'vacunacion': {
                'total_vacunaciones': total_vacunaciones,
                'animales_al_dia': animales_al_dia,
                'proximas_vacunaciones': proximas_vacunaciones
            },
            'nacimientos': {
                'total_nacimientos': total_nacimientos,
                'nacimientos_este_año': nacimientos_año,
                'crias_pendientes_vacunacion': crias_sin_vacunar
            }
        }
    
    @staticmethod
    def buscar_general(termino, hacienda_id=None):
        """Búsqueda general en múltiples campos"""
        query = Animal.query
        
        if hacienda_id:
            query = query.filter(Animal.idhacienda == hacienda_id)
        
        return query.filter(
            or_(
                Animal.hierro.ilike(f'%{termino}%'),
                Animal.raza.ilike(f'%{termino}%'),
                Animal.preñada_por.ilike(f'%{termino}%'),
                Animal.observaciones.ilike(f'%{termino}%')
            )
        ).all()
    
    @staticmethod
    def validar_hierro(hierro, hacienda_id, animal_id=None):
        """Valida que el hierro sea único en la hacienda"""
        if not hierro or not hierro.strip():
            return False, "Hierro es requerido"
        
        # Verificar longitud
        hierro = hierro.strip()
        if len(hierro) < 1 or len(hierro) > 20:
            return False, "Hierro debe tener entre 1 y 20 caracteres"
        
        # Verificar unicidad en la hacienda
        animal_existente = Animal.query.filter_by(
            idhacienda=hacienda_id,
            hierro=hierro
        ).first()
        
        if animal_existente and (not animal_id or animal_existente.idanimal != animal_id):
            return False, "Ya existe un animal con ese hierro en la hacienda"
        
        return True, "Hierro válido"
    
    @staticmethod
    def validar_peso(peso):
        """Valida el peso del animal"""
        if peso is None:
            return True, "Campo opcional"
        
        try:
            peso_float = float(peso)
            if peso_float < 0:
                return False, "El peso no puede ser negativo"
            if peso_float > 999999.99:
                return False, "Peso demasiado grande"
            return True, "Peso válido"
        except (ValueError, TypeError):
            return False, "Peso debe ser un número válido"
    
    @staticmethod
    def validar_fechas(fecha_nacimiento, ultimo_parto=None, ultimo_aborto=None, fecha_preñez=None):
        """Valida las fechas del animal"""
        hoy = date.today()
        
        # Validar fecha de nacimiento
        if fecha_nacimiento and fecha_nacimiento > hoy:
            return False, "La fecha de nacimiento no puede ser futura"
        
        # Validar último parto
        if ultimo_parto:
            if ultimo_parto > hoy:
                return False, "La fecha del último parto no puede ser futura"
            if fecha_nacimiento and ultimo_parto < fecha_nacimiento:
                return False, "El último parto no puede ser antes del nacimiento"
        
        # Validar último aborto
        if ultimo_aborto:
            if ultimo_aborto > hoy:
                return False, "La fecha del último aborto no puede ser futura"
            if fecha_nacimiento and ultimo_aborto < fecha_nacimiento:
                return False, "El último aborto no puede ser antes del nacimiento"
        
        # Validar fecha de preñez
        if fecha_preñez:
            if fecha_preñez > hoy:
                return False, "La fecha de preñez no puede ser futura"
            if fecha_nacimiento and fecha_preñez < fecha_nacimiento:
                return False, "La fecha de preñez no puede ser antes del nacimiento"
        
        return True, "Fechas válidas"