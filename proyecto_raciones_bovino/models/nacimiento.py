from . import db
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, func

class Nacimiento(db.Model):
    """
    Modelo para la tabla nacimientos
    Representa los registros de nacimientos de animales
    """
    __tablename__ = 'nacimientos'
    
    # Campos de la tabla
    idnacimiento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idanimal_cria = db.Column(db.Integer, db.ForeignKey('animales.idanimal'), nullable=False)
    idanimal_madre = db.Column(db.Integer, db.ForeignKey('animales.idanimal'), nullable=False)
    idanimal_padre = db.Column(db.Integer, db.ForeignKey('animales.idanimal'), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    peso_nacimiento = db.Column(db.Numeric(6, 2))
    tipo_parto = db.Column(db.Enum('Natural', 'Asistido', 'Cesarea', name='tipo_parto_enum'), default='Natural')
    complicaciones = db.Column(db.Text)
    numero_registro = db.Column(db.String(30))
    vacunas_aplicadas = db.Column(db.Boolean, default=False)
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # RELACIONES CORREGIDAS: Solo la relación con la cría
    # Las relaciones 'madre' y 'padre' se crean automáticamente desde Animal.py via backref
    cria = db.relationship('Animal', foreign_keys=[idanimal_cria], lazy=True)
    
    def __repr__(self):
        return f'<Nacimiento {self.numero_registro or self.idnacimiento} - Cría: {self.cria.hierro if self.cria else "N/A"}>'
    
    def to_dict(self, include_related=True):
        """Convierte el objeto a diccionario para JSON"""
        data = {
            'idnacimiento': self.idnacimiento,
            'idanimal_cria': self.idanimal_cria,
            'idanimal_madre': self.idanimal_madre,
            'idanimal_padre': self.idanimal_padre,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'peso_nacimiento': float(self.peso_nacimiento) if self.peso_nacimiento else None,
            'tipo_parto': self.tipo_parto,
            'complicaciones': self.complicaciones,
            'numero_registro': self.numero_registro,
            'vacunas_aplicadas': self.vacunas_aplicadas,
            'observaciones': self.observaciones,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
        
        if include_related:
            # Información de los animales relacionados
            if self.cria:
                data['cria'] = {
                    'hierro': self.cria.hierro,
                    'sexo': self.cria.sexo,
                    'raza': self.cria.raza,
                    'hacienda_nombre': self.cria.hacienda.nombre if self.cria.hacienda else None
                }
            
            # Acceder a madre y padre a través de los backrefs creados en Animal
            if hasattr(self, 'madre') and self.madre:
                data['madre'] = {
                    'hierro': self.madre.hierro,
                    'raza': self.madre.raza,
                    'numero_partos': self.madre.numero_partos,
                    'hacienda_nombre': self.madre.hacienda.nombre if self.madre.hacienda else None
                }
            
            if hasattr(self, 'padre') and self.padre:
                data['padre'] = {
                    'hierro': self.padre.hierro,
                    'raza': self.padre.raza,
                    'hacienda_nombre': self.padre.hacienda.nombre if self.padre.hacienda else None
                }
            
            # Información adicional calculada
            data['edad_dias'] = self.calcular_edad_dias()
            data['estado_vacunacion'] = 'Aplicadas' if self.vacunas_aplicadas else 'Pendientes'
        
        return data
    
    def calcular_edad_dias(self):
        """Calcula la edad de la cría en días"""
        if not self.fecha_nacimiento:
            return None
        return (date.today() - self.fecha_nacimiento).days
    
    def calcular_edad_meses(self):
        """Calcula la edad aproximada en meses"""
        dias = self.calcular_edad_dias()
        if dias is None:
            return None
        return round(dias / 30.44, 1)  # Promedio de días por mes
    
    def necesita_vacunas_iniciales(self):
        """Determina si la cría necesita vacunas iniciales"""
        if self.vacunas_aplicadas:
            return False
        
        edad_dias = self.calcular_edad_dias()
        if edad_dias is None:
            return False
        
        # Generalmente se vacuna a los 3-4 meses
        return edad_dias >= 90
    
    def actualizar_registro_cria(self):
        """Actualiza el registro del animal cría con datos del nacimiento"""
        if self.cria and self.fecha_nacimiento:
            # Actualizar fecha de nacimiento del animal si no la tiene
            if not self.cria.fecha_nacimiento:
                self.cria.fecha_nacimiento = self.fecha_nacimiento
                db.session.commit()
    
    @staticmethod
    def obtener_por_hacienda(hacienda_id, limite_dias=None):
        """Obtiene nacimientos de una hacienda específica"""
        from .animal import Animal
        
        query = Nacimiento.query.join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
            Animal.idhacienda == hacienda_id
        )
        
        if limite_dias:
            fecha_limite = date.today() - timedelta(days=limite_dias)
            query = query.filter(Nacimiento.fecha_nacimiento >= fecha_limite)
        
        return query.order_by(Nacimiento.fecha_nacimiento.desc()).all()
    
    @staticmethod
    def obtener_por_madre(madre_id):
        """Obtiene todos los nacimientos de una madre específica"""
        return Nacimiento.query.filter_by(idanimal_madre=madre_id).order_by(
            Nacimiento.fecha_nacimiento.desc()
        ).all()
    
    @staticmethod
    def obtener_por_padre(padre_id):
        """Obtiene todos los nacimientos de un padre específico"""
        return Nacimiento.query.filter_by(idanimal_padre=padre_id).order_by(
            Nacimiento.fecha_nacimiento.desc()
        ).all()
    
    @staticmethod
    def obtener_recientes(dias=30, hacienda_id=None):
        """Obtiene nacimientos recientes"""
        from .animal import Animal
        
        fecha_limite = date.today() - timedelta(days=dias)
        query = Nacimiento.query.filter(Nacimiento.fecha_nacimiento >= fecha_limite)
        
        if hacienda_id:
            query = query.join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
                Animal.idhacienda == hacienda_id
            )
        
        return query.order_by(Nacimiento.fecha_nacimiento.desc()).all()
    
    @staticmethod
    def obtener_crias_sin_vacunar(hacienda_id=None):
        """Obtiene crías que necesitan vacunación inicial"""
        from .animal import Animal
        
        # Crías de más de 3 meses sin vacunar
        fecha_limite = date.today() - timedelta(days=90)
        
        query = Nacimiento.query.filter(
            and_(
                Nacimiento.fecha_nacimiento <= fecha_limite,
                Nacimiento.vacunas_aplicadas == False
            )
        )
        
        if hacienda_id:
            query = query.join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
                Animal.idhacienda == hacienda_id
            )
        
        return query.order_by(Nacimiento.fecha_nacimiento).all()
    
    @staticmethod
    def obtener_estadisticas_generales(hacienda_id=None):
        """Obtiene estadísticas generales de nacimientos"""
        from .animal import Animal
        
        query_base = Nacimiento.query
        
        if hacienda_id:
            query_base = query_base.join(Animal, Nacimiento.idanimal_cria == Animal.idanimal).filter(
                Animal.idhacienda == hacienda_id
            )
        
        # Estadísticas básicas
        total_nacimientos = query_base.count()
        
        # Nacimientos por mes (últimos 12 meses)
        from sqlalchemy import extract
        fecha_inicio = date.today() - timedelta(days=365)
        
        nacimientos_por_mes = db.session.query(
            extract('year', Nacimiento.fecha_nacimiento).label('año'),
            extract('month', Nacimiento.fecha_nacimiento).label('mes'),
            func.count(Nacimiento.idnacimiento).label('cantidad')
        ).filter(Nacimiento.fecha_nacimiento >= fecha_inicio)
        
        if hacienda_id:
            nacimientos_por_mes = nacimientos_por_mes.join(
                Animal, Nacimiento.idanimal_cria == Animal.idanimal
            ).filter(Animal.idhacienda == hacienda_id)
        
        nacimientos_por_mes = nacimientos_por_mes.group_by('año', 'mes').all()
        
        # Por tipo de parto
        por_tipo_parto = db.session.query(
            Nacimiento.tipo_parto,
            func.count(Nacimiento.idnacimiento).label('cantidad')
        )
        
        if hacienda_id:
            por_tipo_parto = por_tipo_parto.join(
                Animal, Nacimiento.idanimal_cria == Animal.idanimal
            ).filter(Animal.idhacienda == hacienda_id)
        
        por_tipo_parto = por_tipo_parto.group_by(Nacimiento.tipo_parto).all()
        
        # Nacimientos recientes (30 días)
        nacimientos_recientes = len(Nacimiento.obtener_recientes(30, hacienda_id))
        
        # Crías pendientes de vacunar
        crias_sin_vacunar = len(Nacimiento.obtener_crias_sin_vacunar(hacienda_id))
        
        # Peso promedio al nacer
        peso_promedio = db.session.query(
            func.avg(Nacimiento.peso_nacimiento)
        ).filter(Nacimiento.peso_nacimiento.isnot(None))
        
        if hacienda_id:
            peso_promedio = peso_promedio.join(
                Animal, Nacimiento.idanimal_cria == Animal.idanimal
            ).filter(Animal.idhacienda == hacienda_id)
        
        peso_promedio = peso_promedio.scalar()
        
        return {
            'total_nacimientos': total_nacimientos,
            'nacimientos_recientes_30d': nacimientos_recientes,
            'crias_pendientes_vacunacion': crias_sin_vacunar,
            'peso_promedio_nacimiento': float(peso_promedio) if peso_promedio else 0,
            'nacimientos_por_mes': [
                {
                    'año': int(año),
                    'mes': int(mes),
                    'cantidad': cantidad
                }
                for año, mes, cantidad in nacimientos_por_mes
            ],
            'por_tipo_parto': [
                {
                    'tipo': tipo,
                    'cantidad': cantidad
                }
                for tipo, cantidad in por_tipo_parto
            ]
        }
    
    @staticmethod
    def buscar_general(termino, hacienda_id=None):
        """Búsqueda general en nacimientos"""
        from .animal import Animal
        
        query = Nacimiento.query.join(
            Animal, Nacimiento.idanimal_cria == Animal.idanimal
        )
        
        if hacienda_id:
            query = query.filter(Animal.idhacienda == hacienda_id)
        
        # Buscar en varios campos
        query = query.filter(
            or_(
                Nacimiento.numero_registro.ilike(f'%{termino}%'),
                Animal.hierro.ilike(f'%{termino}%'),
                Nacimiento.observaciones.ilike(f'%{termino}%'),
                Nacimiento.complicaciones.ilike(f'%{termino}%')
            )
        )
        
        return query.order_by(Nacimiento.fecha_nacimiento.desc()).all()
    
    @staticmethod
    def validar_datos_nacimiento(datos):
        """Valida los datos de un nacimiento"""
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = ['idanimal_cria', 'idanimal_madre', 'fecha_nacimiento']
        for campo in campos_requeridos:
            if not datos.get(campo):
                errores.append(f'{campo.replace("_", " ").capitalize()} es requerido')
        
        # Validar fecha de nacimiento
        if datos.get('fecha_nacimiento'):
            try:
                if isinstance(datos['fecha_nacimiento'], str):
                    fecha_nacimiento = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
                else:
                    fecha_nacimiento = datos['fecha_nacimiento']
                
                if fecha_nacimiento > date.today():
                    errores.append('La fecha de nacimiento no puede ser futura')
            except (ValueError, TypeError):
                errores.append('Formato de fecha de nacimiento inválido (YYYY-MM-DD)')
        
        # Validar peso de nacimiento
        if datos.get('peso_nacimiento') is not None:
            try:
                peso = float(datos['peso_nacimiento'])
                if peso < 0:
                    errores.append('El peso de nacimiento no puede ser negativo')
                if peso > 999.99:
                    errores.append('Peso de nacimiento demasiado grande')
            except (ValueError, TypeError):
                errores.append('Peso de nacimiento debe ser un número válido')
        
        # Validar tipo de parto
        if datos.get('tipo_parto'):
            tipos_validos = ['Natural', 'Asistido', 'Cesarea']
            if datos['tipo_parto'] not in tipos_validos:
                errores.append(f'Tipo de parto debe ser uno de: {", ".join(tipos_validos)}')
        
        # Validar campos de texto
        campos_texto = ['numero_registro', 'complicaciones', 'observaciones']
        for campo in campos_texto:
            if datos.get(campo):
                valor = str(datos[campo]).strip()
                if campo == 'numero_registro' and len(valor) > 30:
                    errores.append('Número de registro no puede exceder 30 caracteres')
                elif campo in ['complicaciones', 'observaciones'] and len(valor) > 1000:
                    errores.append(f'{campo.capitalize()} no puede exceder 1000 caracteres')
        
        return errores
    
    @staticmethod
    def verificar_animales_compatibles(cria_id, madre_id, padre_id=None):
        """Verifica que los animales sean compatibles para el registro"""
        from .animal import Animal
        
        errores = []
        
        # Verificar que los animales existen
        cria = Animal.query.get(cria_id) if cria_id else None
        madre = Animal.query.get(madre_id) if madre_id else None
        padre = Animal.query.get(padre_id) if padre_id else None
        
        if not cria:
            errores.append('Animal cría no encontrado')
        if not madre:
            errores.append('Animal madre no encontrado')
        if padre_id and not padre:
            errores.append('Animal padre no encontrado')
        
        if cria and madre:
            # Verificar que la madre sea hembra
            if madre.sexo != 'Hembra':
                errores.append('La madre debe ser una hembra')
            
            # Verificar que la cría no sea la misma que la madre
            if cria.idanimal == madre.idanimal:
                errores.append('La cría no puede ser la misma que la madre')
            
            # Verificar que estén en la misma hacienda
            if cria.idhacienda != madre.idhacienda:
                errores.append('La cría y la madre deben estar en la misma hacienda')
        
        if padre and madre:
            # Verificar que el padre sea macho
            if padre.sexo != 'Macho':
                errores.append('El padre debe ser un macho')
            
            # Verificar que el padre no sea la misma que la madre
            if padre.idanimal == madre.idanimal:
                errores.append('El padre no puede ser el mismo que la madre')
        
        if padre and cria:
            # Verificar que el padre no sea la misma que la cría
            if padre.idanimal == cria.idanimal:
                errores.append('El padre no puede ser el mismo que la cría')
        
        return errores