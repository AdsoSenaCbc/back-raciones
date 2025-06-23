# services/raciones_service.py
from models import db, Animal, RacionLactancia, RacionCeba, DetalleRacionLactancia, DetalleRacionCeba
from models import NrcLactanciaBase, NrcProduccionLeche, NrcGestacion, NrcCeba, Ingrediente, Usuario
from services.nrc_service import NrcService
from datetime import datetime, date
import json

class RacionesService:
    """
    Servicio para gestión y formulación de raciones bovinas
    """
    
    # ===============================
    # RACIONES DE LACTANCIA
    # ===============================
    
    @staticmethod
    def calcular_racion_lactancia(datos, usuario_id):
        """Calcula y guarda una ración para vacas en lactancia"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden calcular raciones',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = RacionesService.validar_datos_lactancia(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'details': errores
                }, 400
            
            # Verificar que el animal existe y es hembra
            animal = Animal.query.get(datos['idanimal'])
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'ANIMAL_NOT_FOUND'
                }, 404
            
            if animal.sexo != 'Hembra':
                return {
                    'error': 'Solo se pueden calcular raciones de lactancia para hembras',
                    'status': 'error',
                    'code': 'INVALID_SEX'
                }, 400
            
            # Calcular requerimientos nutricionales usando NrcService
            requerimientos_result, status_code = NrcService.calcular_requerimientos_lactancia_completos(
                peso_kg=datos['peso_animal'],
                produccion_leche_kg=datos['produccion_leche_dia'],
                porcentaje_grasa=datos['porcentaje_grasa'],
                dias_gestacion=datos.get('dias_gestacion', 0)
            )
            
            if status_code != 200:
                return requerimientos_result, status_code
            
            requerimientos = requerimientos_result['requerimientos']
            
            # Crear registro de ración
            racion = RacionLactancia(
                idanimal=datos['idanimal'],
                fecha_calculo=datetime.strptime(datos['fecha_calculo'], '%Y-%m-%d').date() if datos.get('fecha_calculo') else date.today(),
                peso_animal=datos['peso_animal'],
                produccion_leche_dia=datos['produccion_leche_dia'],
                porcentaje_grasa=datos['porcentaje_grasa'],
                dias_gestacion=datos.get('dias_gestacion', 0),
                
                # Requerimientos base
                req_materia_seca_base=requerimientos['base'].get('materia_seca_kg', 0),
                req_proteina_total_base=requerimientos['base'].get('proteina_total_kg', 0),
                req_proteina_digestible_base=requerimientos['base'].get('proteina_digestible_kg', 0),
                req_en_base=requerimientos['base'].get('en_mcal', 0),
                req_ed_base=requerimientos['base'].get('ed_mcal', 0),
                req_em_base=requerimientos['base'].get('em_mcal', 0),
                req_tnd_base=requerimientos['base'].get('tnd_kg', 0),
                req_calcio_base=requerimientos['base'].get('calcio_kg', 0),
                req_fosforo_base=requerimientos['base'].get('fosforo_kg', 0),
                
                # Requerimientos por producción
                req_proteina_total_produccion=requerimientos['produccion'].get('proteina_total_kg', 0),
                req_proteina_digestible_produccion=requerimientos['produccion'].get('proteina_digestible_kg', 0),
                req_en_produccion=requerimientos['produccion'].get('en_mcal', 0),
                req_ed_produccion=requerimientos['produccion'].get('ed_mcal', 0),
                req_em_produccion=requerimientos['produccion'].get('em_mcal', 0),
                req_tnd_produccion=requerimientos['produccion'].get('tnd_kg', 0),
                req_calcio_produccion=requerimientos['produccion'].get('calcio_kg', 0),
                req_fosforo_produccion=requerimientos['produccion'].get('fosforo_kg', 0),
                
                # Requerimientos por gestación
                req_proteina_total_gestacion=requerimientos['gestacion'].get('proteina_total_kg', 0),
                req_proteina_digestible_gestacion=requerimientos['gestacion'].get('proteina_digestible_kg', 0),
                req_en_gestacion=requerimientos['gestacion'].get('en_mcal', 0),
                req_ed_gestacion=requerimientos['gestacion'].get('ed_mcal', 0),
                req_em_gestacion=requerimientos['gestacion'].get('em_mcal', 0),
                req_tnd_gestacion=requerimientos['gestacion'].get('tnd_kg', 0),
                req_calcio_gestacion=requerimientos['gestacion'].get('calcio_kg', 0),
                req_fosforo_gestacion=requerimientos['gestacion'].get('fosforo_kg', 0),
                
                # Totales
                req_total_materia_seca=requerimientos['totales'].get('materia_seca_kg', 0),
                req_total_proteina_total=requerimientos['totales'].get('proteina_total_kg', 0),
                req_total_proteina_digestible=requerimientos['totales'].get('proteina_digestible_kg', 0),
                req_total_en=requerimientos['totales'].get('en_mcal', 0),
                req_total_ed=requerimientos['totales'].get('ed_mcal', 0),
                req_total_em=requerimientos['totales'].get('em_mcal', 0),
                req_total_tnd=requerimientos['totales'].get('tnd_kg', 0),
                req_total_calcio=requerimientos['totales'].get('calcio_kg', 0),
                req_total_fosforo=requerimientos['totales'].get('fosforo_kg', 0),
                
                observaciones=datos.get('observaciones', '').strip() or None,
                calculado_por=usuario_id
            )
            
            db.session.add(racion)
            db.session.flush()  # Para obtener el ID antes del commit
            
            # Procesar ingredientes si se proporcionaron
            if datos.get('ingredientes'):
                for ingrediente_data in datos['ingredientes']:
                    detalle = DetalleRacionLactancia(
                        idracion_lactancia=racion.idracion_lactancia,
                        idingrediente=ingrediente_data['idingrediente'],
                        cantidad_kg=ingrediente_data['cantidad_kg'],
                        porcentaje_racion=ingrediente_data['porcentaje_racion'],
                        costo_kg=ingrediente_data.get('costo_kg', 0)
                    )
                    db.session.add(detalle)
            
            db.session.commit()
            
            # Calcular balance nutricional si hay ingredientes
            balance = None
            if datos.get('ingredientes'):
                balance = racion.calcular_balance_nutricional()
            
            response_data = {
                'message': f'Ración de lactancia calculada para {animal.hierro}',
                'status': 'success',
                'racion': racion.to_dict(include_detalles=True),
                'requerimientos_detallados': requerimientos
            }
            
            if balance:
                response_data['balance_nutricional'] = balance
            
            return response_data, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al calcular ración: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def listar_raciones_lactancia(filtros=None, pagina=1, por_pagina=50):
        """Lista raciones de lactancia con filtros"""
        try:
            query = RacionLactancia.query.join(Animal)
            
            # Aplicar filtros
            if filtros:
                if filtros.get('hacienda_id'):
                    query = query.filter(Animal.idhacienda == filtros['hacienda_id'])
                
                if filtros.get('animal_id'):
                    query = query.filter(RacionLactancia.idanimal == filtros['animal_id'])
                
                if filtros.get('fecha_desde'):
                    fecha_desde = datetime.strptime(filtros['fecha_desde'], '%Y-%m-%d').date()
                    query = query.filter(RacionLactancia.fecha_calculo >= fecha_desde)
                
                if filtros.get('fecha_hasta'):
                    fecha_hasta = datetime.strptime(filtros['fecha_hasta'], '%Y-%m-%d').date()
                    query = query.filter(RacionLactancia.fecha_calculo <= fecha_hasta)
            
            # Ordenar por fecha descendente
            query = query.order_by(RacionLactancia.fecha_calculo.desc())
            
            # Paginación
            raciones_paginadas = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'raciones': [r.to_dict() for r in raciones_paginadas.items],
                'total': raciones_paginadas.total,
                'pagina_actual': pagina,
                'total_paginas': raciones_paginadas.pages,
                'por_pagina': por_pagina,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar raciones: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_racion_lactancia(racion_id, include_balance=False):
        """Obtiene una ración de lactancia específica"""
        try:
            racion = RacionLactancia.query.get(racion_id)
            if not racion:
                return {
                    'error': 'Ración no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            data = racion.to_dict(include_detalles=True)
            
            if include_balance and racion.detalles:
                balance = racion.calcular_balance_nutricional()
                if balance:
                    data['balance_nutricional'] = balance
                
                aporte = racion.calcular_aporte_nutricional_total()
                if aporte:
                    data['aporte_total'] = aporte
            
            return {
                'racion': data,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener ración: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # RACIONES DE CEBA
    # ===============================
    
    @staticmethod
    def calcular_racion_ceba(datos, usuario_id):
        """Calcula y guarda una ración para animales en ceba"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden calcular raciones',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = RacionesService.validar_datos_ceba(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'details': errores
                }, 400
            
            # Verificar que el animal existe
            animal = Animal.query.get(datos['idanimal'])
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'ANIMAL_NOT_FOUND'
                }, 404
            
            # Obtener requerimientos NRC para ceba
            nrc_ceba = NrcCeba.obtener_por_peso_y_gdp(
                datos['peso_animal'], 
                datos['gdp_objetivo']
            )
            
            if not nrc_ceba:
                return {
                    'error': 'No se encontraron requerimientos NRC para los parámetros especificados',
                    'status': 'error',
                    'code': 'NRC_NOT_FOUND'
                }, 404
            
            # Crear registro de ración
            racion = RacionCeba(
                idanimal=datos['idanimal'],
                idnrc_ceba=nrc_ceba.idnrc_ceba,
                fecha_calculo=datetime.strptime(datos['fecha_calculo'], '%Y-%m-%d').date() if datos.get('fecha_calculo') else date.today(),
                peso_animal=datos['peso_animal'],
                gdp_objetivo=datos['gdp_objetivo'],
                observaciones=datos.get('observaciones', '').strip() or None,
                calculado_por=usuario_id
            )
            
            db.session.add(racion)
            db.session.flush()
            
            # Procesar ingredientes si se proporcionaron
            if datos.get('ingredientes'):
                for ingrediente_data in datos['ingredientes']:
                    detalle = DetalleRacionCeba(
                        idracion_ceba=racion.idracion_ceba,
                        idingrediente=ingrediente_data['idingrediente'],
                        cantidad_kg=ingrediente_data['cantidad_kg'],
                        porcentaje_racion=ingrediente_data['porcentaje_racion'],
                        costo_kg=ingrediente_data.get('costo_kg', 0)
                    )
                    db.session.add(detalle)
            
            db.session.commit()
            
            return {
                'message': f'Ración de ceba calculada para {animal.hierro}',
                'status': 'success',
                'racion': racion.to_dict(include_detalles=True),
                'requerimientos_nrc': nrc_ceba.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al calcular ración de ceba: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def listar_raciones_ceba(filtros=None, pagina=1, por_pagina=50):
        """Lista raciones de ceba con filtros"""
        try:
            query = RacionCeba.query.join(Animal)
            
            # Aplicar filtros
            if filtros:
                if filtros.get('hacienda_id'):
                    query = query.filter(Animal.idhacienda == filtros['hacienda_id'])
                
                if filtros.get('animal_id'):
                    query = query.filter(RacionCeba.idanimal == filtros['animal_id'])
                
                if filtros.get('fecha_desde'):
                    fecha_desde = datetime.strptime(filtros['fecha_desde'], '%Y-%m-%d').date()
                    query = query.filter(RacionCeba.fecha_calculo >= fecha_desde)
                
                if filtros.get('fecha_hasta'):
                    fecha_hasta = datetime.strptime(filtros['fecha_hasta'], '%Y-%m-%d').date()
                    query = query.filter(RacionCeba.fecha_calculo <= fecha_hasta)
            
            # Ordenar por fecha descendente
            query = query.order_by(RacionCeba.fecha_calculo.desc())
            
            # Paginación
            raciones_paginadas = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'raciones': [r.to_dict() for r in raciones_paginadas.items],
                'total': raciones_paginadas.total,
                'pagina_actual': pagina,
                'total_paginas': raciones_paginadas.pages,
                'por_pagina': por_pagina,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar raciones de ceba: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # FORMULACIÓN AUTOMÁTICA
    # ===============================
    
    @staticmethod
    def formular_racion_automatica(datos, usuario_id):
        """Formulación automática de ración basada en ingredientes disponibles"""
        try:
            # Esta es una implementación básica de formulación automática
            # En un sistema más avanzado, se usaría programación lineal
            
            # Obtener ingredientes disponibles
            ingredientes_disponibles = Ingrediente.query.filter_by(disponible=True).all()
            
            if not ingredientes_disponibles:
                return {
                    'error': 'No hay ingredientes disponibles para formular',
                    'status': 'error'
                }, 400
            
            # Separar ingredientes por tipo
            forrajes = [i for i in ingredientes_disponibles if i.tipo_ingrediente == 'Forraje']
            concentrados = [i for i in ingredientes_disponibles if i.tipo_ingrediente == 'Concentrado']
            minerales = [i for i in ingredientes_disponibles if i.tipo_ingrediente == 'Mineral']
            
            # Formulación básica (60% forraje, 35% concentrado, 5% mineral)
            formulacion = []
            
            if forrajes:
                # Seleccionar el primer forraje con análisis nutricional
                forraje_principal = next((f for f in forrajes if f.obtener_caracteristica_promedio()), None)
                if forraje_principal:
                    formulacion.append({
                        'idingrediente': forraje_principal.idingrediente,
                        'cantidad_kg': datos.get('cantidad_total', 20) * 0.6,
                        'porcentaje_racion': 60.0,
                        'ingrediente': forraje_principal.nombre_ingrediente
                    })
            
            if concentrados:
                concentrado_principal = next((c for c in concentrados if c.obtener_caracteristica_promedio()), None)
                if concentrado_principal:
                    formulacion.append({
                        'idingrediente': concentrado_principal.idingrediente,
                        'cantidad_kg': datos.get('cantidad_total', 20) * 0.35,
                        'porcentaje_racion': 35.0,
                        'ingrediente': concentrado_principal.nombre_ingrediente
                    })
            
            if minerales:
                mineral_principal = next((m for m in minerales if m.obtener_caracteristica_promedio()), None)
                if mineral_principal:
                    formulacion.append({
                        'idingrediente': mineral_principal.idingrediente,
                        'cantidad_kg': datos.get('cantidad_total', 20) * 0.05,
                        'porcentaje_racion': 5.0,
                        'ingrediente': mineral_principal.nombre_ingrediente
                    })
            
            # Agregar la formulación a los datos
            datos['ingredientes'] = formulacion
            
            # Calcular la ración con la formulación automática
            if datos.get('tipo_racion') == 'lactancia':
                return RacionesService.calcular_racion_lactancia(datos, usuario_id)
            else:
                return RacionesService.calcular_racion_ceba(datos, usuario_id)
            
        except Exception as e:
            return {
                'error': f'Error en formulación automática: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # ANÁLISIS Y REPORTES
    # ===============================
    
    @staticmethod
    def analizar_racion(racion_id, tipo_racion):
        """Analiza una ración y proporciona recomendaciones"""
        try:
            if tipo_racion == 'lactancia':
                racion = RacionLactancia.query.get(racion_id)
            else:
                racion = RacionCeba.query.get(racion_id)
            
            if not racion:
                return {
                    'error': 'Ración no encontrada',
                    'status': 'error'
                }, 404
            
            analisis = {
                'balance_nutricional': None,
                'recomendaciones': [],
                'alertas': [],
                'calidad_nutricional': 'Buena',
                'costo_estimado': 0
            }
            
            if tipo_racion == 'lactancia' and racion.detalles:
                balance = racion.calcular_balance_nutricional()
                if balance:
                    analisis['balance_nutricional'] = balance
                    
                    # Generar recomendaciones basadas en el balance
                    for nutriente, datos_nutriente in balance.items():
                        cubrimiento = datos_nutriente.get('porcentaje_cubrimiento', 0)
                        
                        if cubrimiento < 90:
                            analisis['alertas'].append(f'Déficit en {nutriente}: {cubrimiento:.1f}% de cobertura')
                        elif cubrimiento > 120:
                            analisis['recomendaciones'].append(f'Exceso en {nutriente}: {cubrimiento:.1f}% de cobertura - considerar reducir')
                    
                    # Calcular costo
                    costo_total = sum(
                        detalle.cantidad_kg * (detalle.costo_kg or 0) 
                        for detalle in racion.detalles
                    )
                    analisis['costo_estimado'] = float(costo_total)
            
            # Determinar calidad nutricional
            if len(analisis['alertas']) > 2:
                analisis['calidad_nutricional'] = 'Deficiente'
            elif len(analisis['alertas']) > 0:
                analisis['calidad_nutricional'] = 'Regular'
            
            return {
                'analisis': analisis,
                'racion': racion.to_dict(include_detalles=True),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al analizar ración: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_estadisticas_raciones(hacienda_id=None):
        """Obtiene estadísticas de raciones"""
        try:
            estadisticas = {
                'lactancia': {},
                'ceba': {},
                'generales': {}
            }
            
            # Estadísticas de lactancia
            query_lactancia = RacionLactancia.query
            if hacienda_id:
                query_lactancia = query_lactancia.join(Animal).filter(Animal.idhacienda == hacienda_id)
            
            estadisticas['lactancia'] = {
                'total_raciones': query_lactancia.count(),
                'promedio_produccion': query_lactancia.with_entities(
                    db.func.avg(RacionLactancia.produccion_leche_dia)
                ).scalar() or 0,
                'promedio_peso': query_lactancia.with_entities(
                    db.func.avg(RacionLactancia.peso_animal)
                ).scalar() or 0
            }
            
            # Estadísticas de ceba
            query_ceba = RacionCeba.query
            if hacienda_id:
                query_ceba = query_ceba.join(Animal).filter(Animal.idhacienda == hacienda_id)
            
            estadisticas['ceba'] = {
                'total_raciones': query_ceba.count(),
                'promedio_gdp': query_ceba.with_entities(
                    db.func.avg(RacionCeba.gdp_objetivo)
                ).scalar() or 0,
                'promedio_peso': query_ceba.with_entities(
                    db.func.avg(RacionCeba.peso_animal)
                ).scalar() or 0
            }
            
            # Estadísticas generales
            estadisticas['generales'] = {
                'total_raciones': estadisticas['lactancia']['total_raciones'] + estadisticas['ceba']['total_raciones'],
                'raciones_ultimo_mes': 0  # Se puede calcular con filtros de fecha
            }
            
            return {
                'estadisticas': estadisticas,
                'hacienda_id': hacienda_id,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener estadísticas: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # MÉTODOS DE VALIDACIÓN
    # ===============================
    
    @staticmethod
    def validar_datos_lactancia(datos):
        """Valida los datos para ración de lactancia"""
        errores = []
        
        # Campos requeridos
        campos_requeridos = ['idanimal', 'peso_animal', 'produccion_leche_dia', 'porcentaje_grasa']
        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None:
                errores.append(f'{campo.replace("_", " ").title()} es requerido')
        
        # Validar rangos
        if datos.get('peso_animal'):
            if datos['peso_animal'] <= 0 or datos['peso_animal'] > 1000:
                errores.append('Peso del animal debe estar entre 1 y 1000 kg')
        
        if datos.get('produccion_leche_dia'):
            if datos['produccion_leche_dia'] <= 0 or datos['produccion_leche_dia'] > 80:
                errores.append('Producción de leche debe estar entre 1 y 80 litros/día')
        
        if datos.get('porcentaje_grasa'):
            if datos['porcentaje_grasa'] <= 0 or datos['porcentaje_grasa'] > 10:
                errores.append('Porcentaje de grasa debe estar entre 0.1 y 10%')
        
        if datos.get('dias_gestacion'):
            if datos['dias_gestacion'] < 0 or datos['dias_gestacion'] > 285:
                errores.append('Días de gestación debe estar entre 0 y 285')
        
        # Validar ingredientes si se proporcionan
        if datos.get('ingredientes'):
            total_porcentaje = sum(ing.get('porcentaje_racion', 0) for ing in datos['ingredientes'])
            if abs(total_porcentaje - 100) > 0.1:
                errores.append('La suma de porcentajes de ingredientes debe ser 100%')
        
        return errores
    
    @staticmethod
    def validar_datos_ceba(datos):
        """Valida los datos para ración de ceba"""
        errores = []
        
        # Campos requeridos
        campos_requeridos = ['idanimal', 'peso_animal', 'gdp_objetivo']
        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None:
                errores.append(f'{campo.replace("_", " ").title()} es requerido')
        
        # Validar rangos
        if datos.get('peso_animal'):
            if datos['peso_animal'] <= 0 or datos['peso_animal'] > 1000:
                errores.append('Peso del animal debe estar entre 1 y 1000 kg')
        
        if datos.get('gdp_objetivo'):
            if datos['gdp_objetivo'] <= 0 or datos['gdp_objetivo'] > 3:
                errores.append('GDP objetivo debe estar entre 0.1 y 3 kg/día')
        
        # Validar ingredientes si se proporcionan
        if datos.get('ingredientes'):
            total_porcentaje = sum(ing.get('porcentaje_racion', 0) for ing in datos['ingredientes'])
            if abs(total_porcentaje - 100) > 0.1:
                errores.append('La suma de porcentajes de ingredientes debe ser 100%')
        
        return errores
    
    # ===============================
    # UTILIDADES
    # ===============================
    
    @staticmethod
    def eliminar_racion(racion_id, tipo_racion, usuario_id):
        """Elimina una ración (solo administradores)"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden eliminar raciones',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar y eliminar la ración
            if tipo_racion == 'lactancia':
                racion = RacionLactancia.query.get(racion_id)
            else:
                racion = RacionCeba.query.get(racion_id)
            
            if not racion:
                return {
                    'error': 'Ración no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            animal_hierro = racion.animal.hierro if racion.animal else 'N/A'
            
            db.session.delete(racion)
            db.session.commit()
            
            return {
                'message': f'Ración de {tipo_racion} para {animal_hierro} eliminada exitosamente',
                'status': 'success'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al eliminar ración: {str(e)}',
                'status': 'error'
            }, 500