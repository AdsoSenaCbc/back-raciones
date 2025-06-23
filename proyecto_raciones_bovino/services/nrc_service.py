# services/nrc_service.py
from models import db, NrcLactanciaBase, NrcProduccionLeche, NrcGestacion, NrcCeba, Usuario
from datetime import datetime

class NrcService:
    """
    Servicio para gestión de tablas NRC (National Research Council)
    Contiene la lógica de negocio para requerimientos nutricionales
    """
    
    # ===============================
    # GESTIÓN DE NRC LACTANCIA BASE
    # ===============================
    
    @staticmethod
    def crear_nrc_lactancia_base(datos, usuario_id):
        """Crea un registro de requerimientos base de lactancia"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden crear registros NRC',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = NrcService.validar_datos_lactancia_base(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Verificar si ya existe el peso
            peso_existente = NrcLactanciaBase.query.filter_by(peso_kg=datos['peso_kg']).first()
            if peso_existente:
                return {
                    'error': 'Ya existe un registro para este peso',
                    'status': 'error',
                    'code': 'DUPLICATE_WEIGHT'
                }, 409
            
            # Crear el registro
            nrc = NrcLactanciaBase(
                peso_kg=datos['peso_kg'],
                materia_seca_kg=datos['materia_seca_kg'],
                proteina_total_kg=datos['proteina_total_kg'],
                proteina_digestible_kg=datos['proteina_digestible_kg'],
                en_mcal=datos['en_mcal'],
                ed_mcal=datos['ed_mcal'],
                em_mcal=datos['em_mcal'],
                tnd_kg=datos['tnd_kg'],
                calcio_kg=datos['calcio_kg'],
                fosforo_kg=datos['fosforo_kg']
            )
            
            db.session.add(nrc)
            db.session.commit()
            
            return {
                'message': f'Registro NRC lactancia base para {datos["peso_kg"]}kg creado exitosamente',
                'status': 'success',
                'nrc_lactancia': nrc.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear registro NRC: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def listar_nrc_lactancia_base(pagina=1, por_pagina=50):
        """Lista los registros de NRC lactancia base"""
        try:
            query = NrcLactanciaBase.query.order_by(NrcLactanciaBase.peso_kg)
            
            registros_paginados = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'registros': [r.to_dict() for r in registros_paginados.items],
                'total': registros_paginados.total,
                'pagina_actual': pagina,
                'total_paginas': registros_paginados.pages,
                'por_pagina': por_pagina,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar registros NRC: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_requerimientos_lactancia(peso_kg):
        """Obtiene requerimientos de lactancia para un peso específico"""
        try:
            nrc = NrcLactanciaBase.obtener_por_peso(peso_kg)
            if not nrc:
                return {
                    'error': 'No se encontraron requerimientos para ese peso',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            return {
                'requerimientos': nrc.to_dict() if hasattr(nrc, 'to_dict') else {
                    'peso_kg': float(nrc.peso_kg),
                    'materia_seca_kg': float(nrc.materia_seca_kg),
                    'proteina_total_kg': float(nrc.proteina_total_kg),
                    'proteina_digestible_kg': float(nrc.proteina_digestible_kg),
                    'en_mcal': float(nrc.en_mcal),
                    'ed_mcal': float(nrc.ed_mcal),
                    'em_mcal': float(nrc.em_mcal),
                    'tnd_kg': float(nrc.tnd_kg),
                    'calcio_kg': float(nrc.calcio_kg),
                    'fosforo_kg': float(nrc.fosforo_kg)
                },
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener requerimientos: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # GESTIÓN DE NRC PRODUCCIÓN LECHE
    # ===============================
    
    @staticmethod
    def crear_nrc_produccion_leche(datos, usuario_id):
        """Crea un registro de requerimientos por producción de leche"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden crear registros NRC',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = NrcService.validar_datos_produccion_leche(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'details': errores
                }, 400
            
            # Verificar duplicados
            existente = NrcProduccionLeche.query.filter_by(porcentaje_grasa=datos['porcentaje_grasa']).first()
            if existente:
                return {
                    'error': 'Ya existe un registro para este porcentaje de grasa',
                    'status': 'error',
                    'code': 'DUPLICATE_GRASA'
                }, 409
            
            # Crear registro
            nrc = NrcProduccionLeche(
                porcentaje_grasa=datos['porcentaje_grasa'],
                proteina_total_kg=datos['proteina_total_kg'],
                proteina_digestible_kg=datos['proteina_digestible_kg'],
                en_mcal=datos['en_mcal'],
                ed_mcal=datos['ed_mcal'],
                em_mcal=datos['em_mcal'],
                tnd_kg=datos['tnd_kg'],
                calcio_kg=datos['calcio_kg'],
                fosforo_kg=datos['fosforo_kg']
            )
            
            db.session.add(nrc)
            db.session.commit()
            
            return {
                'message': f'Registro NRC producción leche {datos["porcentaje_grasa"]}% grasa creado exitosamente',
                'status': 'success',
                'nrc_produccion': nrc.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear registro NRC: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_requerimientos_produccion(porcentaje_grasa):
        """Obtiene requerimientos por kg de leche según % grasa"""
        try:
            nrc = NrcProduccionLeche.obtener_por_grasa(porcentaje_grasa)
            if not nrc:
                return {
                    'error': 'No se encontraron requerimientos para ese porcentaje de grasa',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            requerimientos = nrc.to_dict() if hasattr(nrc, 'to_dict') else {
                'porcentaje_grasa': float(nrc.porcentaje_grasa),
                'proteina_total_kg': float(nrc.proteina_total_kg),
                'proteina_digestible_kg': float(nrc.proteina_digestible_kg),
                'en_mcal': float(nrc.en_mcal),
                'ed_mcal': float(nrc.ed_mcal),
                'em_mcal': float(nrc.em_mcal),
                'tnd_kg': float(nrc.tnd_kg),
                'calcio_kg': float(nrc.calcio_kg),
                'fosforo_kg': float(nrc.fosforo_kg)
            }
            
            return {
                'requerimientos': requerimientos,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener requerimientos: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # GESTIÓN DE NRC GESTACIÓN
    # ===============================
    
    @staticmethod
    def obtener_requerimientos_gestacion(peso_kg):
        """Obtiene requerimientos adicionales por gestación"""
        try:
            nrc = NrcGestacion.obtener_por_peso(peso_kg)
            if not nrc:
                return {
                    'error': 'No se encontraron requerimientos de gestación para ese peso',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            requerimientos = nrc.to_dict() if hasattr(nrc, 'to_dict') else {
                'peso_kg': float(nrc.peso_kg),
                'materia_seca_kg': float(nrc.materia_seca_kg),
                'proteina_total_kg': float(nrc.proteina_total_kg),
                'proteina_digestible_kg': float(nrc.proteina_digestible_kg),
                'en_mcal': float(nrc.en_mcal),
                'ed_mcal': float(nrc.ed_mcal),
                'em_mcal': float(nrc.em_mcal),
                'tnd_kg': float(nrc.tnd_kg),
                'calcio_kg': float(nrc.calcio_kg),
                'fosforo_kg': float(nrc.fosforo_kg)
            }
            
            return {
                'requerimientos': requerimientos,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener requerimientos: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # GESTIÓN DE NRC CEBA
    # ===============================
    
    @staticmethod
    def listar_nrc_ceba():
        """Lista todos los registros de NRC para ceba"""
        try:
            registros = NrcCeba.query.order_by(NrcCeba.peso_minimo).all()
            
            return {
                'registros': [r.to_dict() for r in registros],
                'total': len(registros),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar registros NRC ceba: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_requerimientos_ceba(peso_kg, gdp_objetivo=None):
        """Obtiene requerimientos para ceba"""
        try:
            if gdp_objetivo:
                nrc = NrcCeba.obtener_por_peso_y_gdp(peso_kg, gdp_objetivo)
            else:
                nrc = NrcCeba.obtener_por_peso(peso_kg)
            
            if not nrc:
                return {
                    'error': 'No se encontraron requerimientos de ceba para esos parámetros',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            return {
                'requerimientos': nrc.to_dict(),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener requerimientos: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # MÉTODOS DE VALIDACIÓN
    # ===============================
    
    @staticmethod
    def validar_datos_lactancia_base(datos):
        """Valida los datos para NRC lactancia base"""
        errores = []
        
        # Campos requeridos
        campos_requeridos = [
            'peso_kg', 'materia_seca_kg', 'proteina_total_kg', 
            'proteina_digestible_kg', 'en_mcal', 'ed_mcal', 
            'em_mcal', 'tnd_kg', 'calcio_kg', 'fosforo_kg'
        ]
        
        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None:
                errores.append(f'{campo.replace("_", " ").title()} es requerido')
        
        # Validar rangos
        if datos.get('peso_kg'):
            if datos['peso_kg'] <= 0 or datos['peso_kg'] > 1000:
                errores.append('Peso debe estar entre 1 y 1000 kg')
        
        # Validar valores positivos
        campos_positivos = [
            'materia_seca_kg', 'proteina_total_kg', 'proteina_digestible_kg',
            'en_mcal', 'ed_mcal', 'em_mcal', 'tnd_kg', 'calcio_kg', 'fosforo_kg'
        ]
        
        for campo in campos_positivos:
            if datos.get(campo) is not None and datos[campo] < 0:
                errores.append(f'{campo.replace("_", " ").title()} debe ser positivo')
        
        return errores
    
    @staticmethod
    def validar_datos_produccion_leche(datos):
        """Valida los datos para NRC producción leche"""
        errores = []
        
        # Campos requeridos
        campos_requeridos = [
            'porcentaje_grasa', 'proteina_total_kg', 'proteina_digestible_kg',
            'en_mcal', 'ed_mcal', 'em_mcal', 'tnd_kg', 'calcio_kg', 'fosforo_kg'
        ]
        
        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None:
                errores.append(f'{campo.replace("_", " ").title()} es requerido')
        
        # Validar porcentaje de grasa
        if datos.get('porcentaje_grasa'):
            if datos['porcentaje_grasa'] <= 0 or datos['porcentaje_grasa'] > 10:
                errores.append('Porcentaje de grasa debe estar entre 0.1 y 10%')
        
        return errores
    
    # ===============================
    # CALCULADORA INTEGRADA
    # ===============================
    
    @staticmethod
    def calcular_requerimientos_lactancia_completos(peso_kg, produccion_leche_kg, porcentaje_grasa, dias_gestacion=0):
        """Calcula requerimientos completos para una vaca en lactancia"""
        try:
            requerimientos_totales = {
                'base': {},
                'produccion': {},
                'gestacion': {},
                'totales': {}
            }
            
            # 1. Requerimientos base por peso
            nrc_base = NrcLactanciaBase.obtener_por_peso(peso_kg)
            if nrc_base:
                requerimientos_totales['base'] = {
                    'materia_seca_kg': float(nrc_base.materia_seca_kg),
                    'proteina_total_kg': float(nrc_base.proteina_total_kg),
                    'proteina_digestible_kg': float(nrc_base.proteina_digestible_kg),
                    'en_mcal': float(nrc_base.en_mcal),
                    'ed_mcal': float(nrc_base.ed_mcal),
                    'em_mcal': float(nrc_base.em_mcal),
                    'tnd_kg': float(nrc_base.tnd_kg),
                    'calcio_kg': float(nrc_base.calcio_kg),
                    'fosforo_kg': float(nrc_base.fosforo_kg)
                }
            
            # 2. Requerimientos por producción de leche
            nrc_produccion = NrcProduccionLeche.obtener_por_grasa(porcentaje_grasa)
            if nrc_produccion:
                requerimientos_totales['produccion'] = {
                    'proteina_total_kg': float(nrc_produccion.proteina_total_kg) * produccion_leche_kg,
                    'proteina_digestible_kg': float(nrc_produccion.proteina_digestible_kg) * produccion_leche_kg,
                    'en_mcal': float(nrc_produccion.en_mcal) * produccion_leche_kg,
                    'ed_mcal': float(nrc_produccion.ed_mcal) * produccion_leche_kg,
                    'em_mcal': float(nrc_produccion.em_mcal) * produccion_leche_kg,
                    'tnd_kg': float(nrc_produccion.tnd_kg) * produccion_leche_kg,
                    'calcio_kg': float(nrc_produccion.calcio_kg) * produccion_leche_kg,
                    'fosforo_kg': float(nrc_produccion.fosforo_kg) * produccion_leche_kg
                }
            
            # 3. Requerimientos adicionales por gestación (si aplica)
            if dias_gestacion >= 210:  # Últimos 2 meses de gestación
                nrc_gestacion = NrcGestacion.obtener_por_peso(peso_kg)
                if nrc_gestacion:
                    requerimientos_totales['gestacion'] = {
                        'materia_seca_kg': float(nrc_gestacion.materia_seca_kg),
                        'proteina_total_kg': float(nrc_gestacion.proteina_total_kg),
                        'proteina_digestible_kg': float(nrc_gestacion.proteina_digestible_kg),
                        'en_mcal': float(nrc_gestacion.en_mcal),
                        'ed_mcal': float(nrc_gestacion.ed_mcal),
                        'em_mcal': float(nrc_gestacion.em_mcal),
                        'tnd_kg': float(nrc_gestacion.tnd_kg),
                        'calcio_kg': float(nrc_gestacion.calcio_kg),
                        'fosforo_kg': float(nrc_gestacion.fosforo_kg)
                    }
            
            # 4. Calcular totales
            requerimientos_totales['totales'] = {
                'materia_seca_kg': (
                    requerimientos_totales['base'].get('materia_seca_kg', 0) +
                    requerimientos_totales['gestacion'].get('materia_seca_kg', 0)
                ),
                'proteina_total_kg': (
                    requerimientos_totales['base'].get('proteina_total_kg', 0) +
                    requerimientos_totales['produccion'].get('proteina_total_kg', 0) +
                    requerimientos_totales['gestacion'].get('proteina_total_kg', 0)
                ),
                'proteina_digestible_kg': (
                    requerimientos_totales['base'].get('proteina_digestible_kg', 0) +
                    requerimientos_totales['produccion'].get('proteina_digestible_kg', 0) +
                    requerimientos_totales['gestacion'].get('proteina_digestible_kg', 0)
                ),
                'en_mcal': (
                    requerimientos_totales['base'].get('en_mcal', 0) +
                    requerimientos_totales['produccion'].get('en_mcal', 0) +
                    requerimientos_totales['gestacion'].get('en_mcal', 0)
                ),
                'ed_mcal': (
                    requerimientos_totales['base'].get('ed_mcal', 0) +
                    requerimientos_totales['produccion'].get('ed_mcal', 0) +
                    requerimientos_totales['gestacion'].get('ed_mcal', 0)
                ),
                'em_mcal': (
                    requerimientos_totales['base'].get('em_mcal', 0) +
                    requerimientos_totales['produccion'].get('em_mcal', 0) +
                    requerimientos_totales['gestacion'].get('em_mcal', 0)
                ),
                'tnd_kg': (
                    requerimientos_totales['base'].get('tnd_kg', 0) +
                    requerimientos_totales['produccion'].get('tnd_kg', 0) +
                    requerimientos_totales['gestacion'].get('tnd_kg', 0)
                ),
                'calcio_kg': (
                    requerimientos_totales['base'].get('calcio_kg', 0) +
                    requerimientos_totales['produccion'].get('calcio_kg', 0) +
                    requerimientos_totales['gestacion'].get('calcio_kg', 0)
                ),
                'fosforo_kg': (
                    requerimientos_totales['base'].get('fosforo_kg', 0) +
                    requerimientos_totales['produccion'].get('fosforo_kg', 0) +
                    requerimientos_totales['gestacion'].get('fosforo_kg', 0)
                )
            }
            
            return {
                'requerimientos': requerimientos_totales,
                'parametros': {
                    'peso_kg': peso_kg,
                    'produccion_leche_kg': produccion_leche_kg,
                    'porcentaje_grasa': porcentaje_grasa,
                    'dias_gestacion': dias_gestacion
                },
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al calcular requerimientos: {str(e)}',
                'status': 'error'
            }, 500