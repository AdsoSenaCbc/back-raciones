from . import db
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, func

class VacunacionAnimal(db.Model):
    """
    Modelo para la tabla vacunacion_animales
    Representa los registros de vacunación aplicados a los animales
    """
    __tablename__ = 'vacunacion_animales'
    
    # Campos de la tabla
    idvacunacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idanimal = db.Column(db.Integer, db.ForeignKey('animales.idanimal'), nullable=False)
    idvacuna = db.Column(db.Integer, db.ForeignKey('catalogo_vacunas.idvacuna'), nullable=False)
    fecha_aplicacion = db.Column(db.Date, nullable=False)
    dosis = db.Column(db.String(50))
    lote_vacuna = db.Column(db.String(50))
    veterinario = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    proxima_dosis = db.Column(db.Date)
    
    def __repr__(self):
        return f'<VacunacionAnimal {self.animal.hierro if self.animal else "N/A"} - {self.vacuna.nombre_vacuna if self.vacuna else "N/A"}>'
    
    def to_dict(self, include_related=True):
        """Convierte el objeto a diccionario para JSON"""
        data = {
            'idvacunacion': self.idvacunacion,
            'idanimal': self.idanimal,
            'idvacuna': self.idvacuna,
            'fecha_aplicacion': self.fecha_aplicacion.isoformat() if self.fecha_aplicacion else None,
            'dosis': self.dosis,
            'lote_vacuna': self.lote_vacuna,
            'veterinario': self.veterinario,
            'observaciones': self.observaciones,
            'proxima_dosis': self.proxima_dosis.isoformat() if self.proxima_dosis else None
        }
        
        if include_related:
            # Información del animal
            if self.animal:
                data['animal'] = {
                    'hierro': self.animal.hierro,
                    'sexo': self.animal.sexo,
                    'raza': self.animal.raza,
                    'hacienda_nombre': self.animal.hacienda.nombre if self.animal.hacienda else None
                }
            
            # Información de la vacuna
            if self.vacuna:
                data['vacuna'] = {
                    'nombre_vacuna': self.vacuna.nombre_vacuna,
                    'descripcion': self.vacuna.descripcion,
                    'frecuencia_dias': self.vacuna.frecuencia_dias
                }
            
            # Información adicional calculada
            data['dias_desde_aplicacion'] = self.dias_desde_aplicacion()
            data['estado_proxima_dosis'] = self.estado_proxima_dosis()
            data['dias_para_proxima'] = self.dias_para_proxima_dosis()
        
        return data
    
    def dias_desde_aplicacion(self):
        """Calcula días transcurridos desde la aplicación"""
        if not self.fecha_aplicacion:
            return None
        return (date.today() - self.fecha_aplicacion).days
    
    def dias_para_proxima_dosis(self):
        """Calcula días restantes para la próxima dosis"""
        if not self.proxima_dosis:
            return None
        return (self.proxima_dosis - date.today()).days
    
    def estado_proxima_dosis(self):
        """Determina el estado de la próxima dosis"""
        if not self.proxima_dosis:
            return 'sin_programar'
        
        dias_restantes = self.dias_para_proxima_dosis()
        
        if dias_restantes < 0:
            return 'vencida'
        elif dias_restantes <= 7:
            return 'proxima'
        elif dias_restantes <= 30:
            return 'cercana'
        else:
            return 'programada'
    
    def calcular_proxima_dosis_automatica(self):
        """Calcula automáticamente la fecha de próxima dosis basada en la frecuencia"""
        if self.vacuna and self.vacuna.frecuencia_dias and self.fecha_aplicacion:
            return self.fecha_aplicacion + timedelta(days=self.vacuna.frecuencia_dias)
        return None
    
    def actualizar_proxima_dosis_automatica(self):
        """Actualiza automáticamente la próxima dosis si no está establecida"""
        if not self.proxima_dosis:
            proxima = self.calcular_proxima_dosis_automatica()
            if proxima:
                self.proxima_dosis = proxima
                db.session.commit()
    
    @staticmethod
    def obtener_por_animal(animal_id, incluir_vencidas=True):
        """Obtiene todas las vacunaciones de un animal"""
        query = VacunacionAnimal.query.filter_by(idanimal=animal_id)
        
        if not incluir_vencidas:
            # Solo vacunaciones vigentes (próxima dosis no vencida)
            hoy = date.today()
            query = query.filter(
                or_(
                    VacunacionAnimal.proxima_dosis.is_(None),
                    VacunacionAnimal.proxima_dosis >= hoy
                )
            )
        
        return query.order_by(VacunacionAnimal.fecha_aplicacion.desc()).all()
    
    @staticmethod
    def obtener_por_hacienda(hacienda_id, limite_dias=None):
        """Obtiene vacunaciones de una hacienda específica"""
        from .animal import Animal
        
        query = VacunacionAnimal.query.join(Animal).filter(
            Animal.idhacienda == hacienda_id
        )
        
        if limite_dias:
            fecha_limite = date.today() - timedelta(days=limite_dias)
            query = query.filter(VacunacionAnimal.fecha_aplicacion >= fecha_limite)
        
        return query.order_by(VacunacionAnimal.fecha_aplicacion.desc()).all()
    
    @staticmethod
    def obtener_proximas_dosis(dias_adelante=30, hacienda_id=None):
        """Obtiene animales que necesitan próximas dosis"""
        fecha_limite = date.today() + timedelta(days=dias_adelante)
        
        query = VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.proxima_dosis.isnot(None),
                VacunacionAnimal.proxima_dosis <= fecha_limite
            )
        )
        
        if hacienda_id:
            from .animal import Animal
            query = query.join(Animal).filter(Animal.idhacienda == hacienda_id)
        
        return query.order_by(VacunacionAnimal.proxima_dosis).all()
    
    @staticmethod
    def obtener_vencidas(hacienda_id=None):
        """Obtiene vacunaciones con dosis vencidas"""
        hoy = date.today()
        
        query = VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.proxima_dosis.isnot(None),
                VacunacionAnimal.proxima_dosis < hoy
            )
        )
        
        if hacienda_id:
            from .animal import Animal
            query = query.join(Animal).filter(Animal.idhacienda == hacienda_id)
        
        return query.order_by(VacunacionAnimal.proxima_dosis).all()
    
    @staticmethod
    def obtener_estadisticas_generales(hacienda_id=None):
        """Obtiene estadísticas generales de vacunación"""
        query_base = VacunacionAnimal.query
        
        if hacienda_id:
            from .animal import Animal
            query_base = query_base.join(Animal).filter(Animal.idhacienda == hacienda_id)
        
        # Estadísticas básicas
        total_vacunaciones = query_base.count()
        
        # Vacunaciones por mes (últimos 12 meses)
        from sqlalchemy import extract
        fecha_inicio = date.today() - timedelta(days=365)
        
        vacunaciones_por_mes = db.session.query(
            extract('year', VacunacionAnimal.fecha_aplicacion).label('año'),
            extract('month', VacunacionAnimal.fecha_aplicacion).label('mes'),
            func.count(VacunacionAnimal.idvacunacion).label('cantidad')
        ).filter(VacunacionAnimal.fecha_aplicacion >= fecha_inicio)
        
        if hacienda_id:
            from .animal import Animal
            vacunaciones_por_mes = vacunaciones_por_mes.join(Animal).filter(
                Animal.idhacienda == hacienda_id
            )
        
        vacunaciones_por_mes = vacunaciones_por_mes.group_by('año', 'mes').all()
        
        # Vacunas más aplicadas
        from .catalogo_vacuna import CatalogoVacuna
        vacunas_mas_aplicadas = db.session.query(
            CatalogoVacuna.nombre_vacuna,
            func.count(VacunacionAnimal.idvacunacion).label('cantidad')
        ).join(VacunacionAnimal)
        
        if hacienda_id:
            from .animal import Animal
            vacunas_mas_aplicadas = vacunas_mas_aplicadas.join(Animal).filter(
                Animal.idhacienda == hacienda_id
            )
        
        vacunas_mas_aplicadas = vacunas_mas_aplicadas.group_by(
            CatalogoVacuna.idvacuna, CatalogoVacuna.nombre_vacuna
        ).order_by(func.count(VacunacionAnimal.idvacunacion).desc()).limit(10).all()
        
        # Próximas dosis
        proximas_7_dias = len(VacunacionAnimal.obtener_proximas_dosis(7, hacienda_id))
        proximas_30_dias = len(VacunacionAnimal.obtener_proximas_dosis(30, hacienda_id))
        vencidas = len(VacunacionAnimal.obtener_vencidas(hacienda_id))
        
        return {
            'total_vacunaciones': total_vacunaciones,
            'proximas_7_dias': proximas_7_dias,
            'proximas_30_dias': proximas_30_dias,
            'dosis_vencidas': vencidas,
            'vacunaciones_por_mes': [
                {
                    'año': int(año),
                    'mes': int(mes),
                    'cantidad': cantidad
                }
                for año, mes, cantidad in vacunaciones_por_mes
            ],
            'vacunas_mas_aplicadas': [
                {
                    'vacuna': nombre,
                    'cantidad': cantidad
                }
                for nombre, cantidad in vacunas_mas_aplicadas
            ]
        }
    
    @staticmethod
    def buscar_general(termino, hacienda_id=None):
        """Búsqueda general en vacunaciones"""
        from .animal import Animal
        from .catalogo_vacuna import CatalogoVacuna
        
        query = VacunacionAnimal.query.join(Animal).join(CatalogoVacuna)
        
        if hacienda_id:
            query = query.filter(Animal.idhacienda == hacienda_id)
        
        query = query.filter(
            or_(
                Animal.hierro.ilike(f'%{termino}%'),
                CatalogoVacuna.nombre_vacuna.ilike(f'%{termino}%'),
                VacunacionAnimal.veterinario.ilike(f'%{termino}%'),
                VacunacionAnimal.lote_vacuna.ilike(f'%{termino}%'),
                VacunacionAnimal.observaciones.ilike(f'%{termino}%')
            )
        )
        
        return query.order_by(VacunacionAnimal.fecha_aplicacion.desc()).all()
    
    @staticmethod
    def validar_datos_vacunacion(datos):
        """Valida los datos de una vacunación"""
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = ['idanimal', 'idvacuna', 'fecha_aplicacion']
        for campo in campos_requeridos:
            if not datos.get(campo):
                errores.append(f'{campo.replace("_", " ").capitalize()} es requerido')
        
        # Validar fecha de aplicación
        if datos.get('fecha_aplicacion'):
            try:
                if isinstance(datos['fecha_aplicacion'], str):
                    fecha_aplicacion = datetime.strptime(datos['fecha_aplicacion'], '%Y-%m-%d').date()
                else:
                    fecha_aplicacion = datos['fecha_aplicacion']
                
                if fecha_aplicacion > date.today():
                    errores.append('La fecha de aplicación no puede ser futura')
            except (ValueError, TypeError):
                errores.append('Formato de fecha de aplicación inválido (YYYY-MM-DD)')
        
        # Validar próxima dosis
        if datos.get('proxima_dosis'):
            try:
                if isinstance(datos['proxima_dosis'], str):
                    proxima_dosis = datetime.strptime(datos['proxima_dosis'], '%Y-%m-%d').date()
                else:
                    proxima_dosis = datos['proxima_dosis']
                
                # La próxima dosis debe ser posterior a la aplicación
                if datos.get('fecha_aplicacion'):
                    if isinstance(datos['fecha_aplicacion'], str):
                        fecha_aplicacion = datetime.strptime(datos['fecha_aplicacion'], '%Y-%m-%d').date()
                    else:
                        fecha_aplicacion = datos['fecha_aplicacion']
                    
                    if proxima_dosis <= fecha_aplicacion:
                        errores.append('La próxima dosis debe ser posterior a la fecha de aplicación')
            except (ValueError, TypeError):
                errores.append('Formato de fecha de próxima dosis inválido (YYYY-MM-DD)')
        
        # Validar campos de texto
        campos_texto = ['dosis', 'lote_vacuna', 'veterinario']
        for campo in campos_texto:
            if datos.get(campo):
                valor = str(datos[campo]).strip()
                longitud_maxima = 100 if campo == 'veterinario' else 50
                if len(valor) > longitud_maxima:
                    errores.append(f'{campo.replace("_", " ").capitalize()} no puede exceder {longitud_maxima} caracteres')
        
        return errores
    
    @staticmethod
    def verificar_duplicado(idanimal, idvacuna, fecha_aplicacion, excluir_id=None):
        """Verifica si ya existe una vacunación similar reciente"""
        # Buscar vacunaciones de la misma vacuna en los últimos 30 días
        fecha_inicio = fecha_aplicacion - timedelta(days=30)
        fecha_fin = fecha_aplicacion + timedelta(days=30)
        
        query = VacunacionAnimal.query.filter(
            and_(
                VacunacionAnimal.idanimal == idanimal,
                VacunacionAnimal.idvacuna == idvacuna,
                VacunacionAnimal.fecha_aplicacion >= fecha_inicio,
                VacunacionAnimal.fecha_aplicacion <= fecha_fin
            )
        )
        
        if excluir_id:
            query = query.filter(VacunacionAnimal.idvacunacion != excluir_id)
        
        return query.first() is not None