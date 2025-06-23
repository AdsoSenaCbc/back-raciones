# services/ingredientes_service.py
from models import db, Departamento, Municipio, ConsultaBromatologica, Ingrediente, CaracteristicaNutricional, Usuario
from datetime import datetime, date
import re

class IngredientesService:
    """
    Servicio para gestión de ingredientes y análisis bromatológicos
    """
    
    # ===============================
    # GESTIÓN DE DEPARTAMENTOS Y MUNICIPIOS
    # ===============================
    
    @staticmethod
    def listar_departamentos():
        """Lista todos los departamentos"""
        try:
            departamentos = Departamento.query.order_by(Departamento.nombre_departamento).all()
            
            return {
                'departamentos': [d.to_dict() for d in departamentos],
                'total': len(departamentos),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar departamentos: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_municipios_por_departamento(departamento_id):
        """Obtiene municipios de un departamento específico"""
        try:
            departamento = Departamento.query.get(departamento_id)
            if not departamento:
                return {
                    'error': 'Departamento no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            municipios = Municipio.query.filter_by(iddepartamento=departamento_id).order_by(Municipio.nombre_municipio).all()
            
            return {
                'municipios': [m.to_dict() for m in municipios],
                'departamento': departamento.to_dict(),
                'total': len(municipios),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener municipios: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def crear_municipio(datos, usuario_id):
        """Crea un nuevo municipio"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear municipios',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            if not datos.get('nombre_municipio') or not datos.get('iddepartamento'):
                return {
                    'error': 'Nombre del municipio y departamento son requeridos',
                    'status': 'error'
                }, 400
            
            # Verificar que el departamento existe
            departamento = Departamento.query.get(datos['iddepartamento'])
            if not departamento:
                return {
                    'error': 'Departamento no encontrado',
                    'status': 'error'
                }, 404
            
            # Verificar duplicados
            municipio_existente = Municipio.query.filter_by(
                iddepartamento=datos['iddepartamento'],
                nombre_municipio=datos['nombre_municipio'].strip()
            ).first()
            
            if municipio_existente:
                return {
                    'error': 'Ya existe un municipio con ese nombre en el departamento',
                    'status': 'error',
                    'code': 'DUPLICATE_MUNICIPIO'
                }, 409
            
            # Crear municipio
            municipio = Municipio(
                iddepartamento=datos['iddepartamento'],
                nombre_municipio=datos['nombre_municipio'].strip()
            )
            
            db.session.add(municipio)
            db.session.commit()
            
            return {
                'message': f'Municipio "{municipio.nombre_municipio}" creado exitosamente',
                'status': 'success',
                'municipio': municipio.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear municipio: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # GESTIÓN DE CONSULTAS BROMATOLÓGICAS
    # ===============================
    
    @staticmethod
    def crear_consulta_bromatologica(datos, usuario_id):
        """Crea una nueva consulta bromatológica"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear consultas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            if not datos.get('iddepartamento') or not datos.get('idmunicipio'):
                return {
                    'error': 'Departamento y municipio son requeridos',
                    'status': 'error'
                }, 400
            
            # Verificar que departamento y municipio existen
            departamento = Departamento.query.get(datos['iddepartamento'])
            municipio = Municipio.query.get(datos['idmunicipio'])
            
            if not departamento or not municipio:
                return {
                    'error': 'Departamento o municipio no encontrado',
                    'status': 'error'
                }, 404
            
            # Verificar que el municipio pertenece al departamento
            if municipio.iddepartamento != datos['iddepartamento']:
                return {
                    'error': 'El municipio no pertenece al departamento seleccionado',
                    'status': 'error'
                }, 400
            
            # Crear consulta
            consulta = ConsultaBromatologica(
                iddepartamento=datos['iddepartamento'],
                idmunicipio=datos['idmunicipio'],
                fecha_consulta=datetime.strptime(datos['fecha_consulta'], '%Y-%m-%d').date() if datos.get('fecha_consulta') else date.today(),
                laboratorio=datos.get('laboratorio', '').strip() or None,
                observaciones=datos.get('observaciones', '').strip() or None,
                activo=True
            )
            
            db.session.add(consulta)
            db.session.commit()
            
            return {
                'message': 'Consulta bromatológica creada exitosamente',
                'status': 'success',
                'consulta': consulta.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear consulta: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def listar_consultas_bromatologicas(filtros=None, pagina=1, por_pagina=50):
        """Lista consultas bromatológicas con filtros"""
        try:
            query = ConsultaBromatologica.query.join(Departamento).join(Municipio)
            
            # Aplicar filtros
            if filtros:
                if filtros.get('departamento_id'):
                    query = query.filter(ConsultaBromatologica.iddepartamento == filtros['departamento_id'])
                
                if filtros.get('municipio_id'):
                    query = query.filter(ConsultaBromatologica.idmunicipio == filtros['municipio_id'])
                
                if filtros.get('activo') is not None:
                    query = query.filter(ConsultaBromatologica.activo == filtros['activo'])
                
                if filtros.get('laboratorio'):
                    query = query.filter(ConsultaBromatologica.laboratorio.ilike(f"%{filtros['laboratorio']}%"))
            
            # Ordenar por fecha descendente
            query = query.order_by(ConsultaBromatologica.fecha_consulta.desc())
            
            # Paginación
            consultas_paginadas = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'consultas': [c.to_dict() for c in consultas_paginadas.items],
                'total': consultas_paginadas.total,
                'pagina_actual': pagina,
                'total_paginas': consultas_paginadas.pages,
                'por_pagina': por_pagina,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar consultas: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # GESTIÓN DE INGREDIENTES
    # ===============================
    
    @staticmethod
    def crear_ingrediente(datos, usuario_id):
        """Crea un nuevo ingrediente"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear ingredientes',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = IngredientesService.validar_datos_ingrediente(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'details': errores
                }, 400
            
            # Verificar duplicados
            ingrediente_existente = Ingrediente.query.filter_by(
                nombre_ingrediente=datos['nombre_ingrediente'].strip()
            ).first()
            
            if ingrediente_existente:
                return {
                    'error': 'Ya existe un ingrediente con ese nombre',
                    'status': 'error',
                    'code': 'DUPLICATE_NOMBRE'
                }, 409
            
            # Crear ingrediente
            ingrediente = Ingrediente(
                nombre_ingrediente=datos['nombre_ingrediente'].strip(),
                tipo_ingrediente=datos['tipo_ingrediente'],
                descripcion=datos.get('descripcion', '').strip() or None,
                disponible=bool(datos.get('disponible', True))
            )
            
            db.session.add(ingrediente)
            db.session.commit()
            
            return {
                'message': f'Ingrediente "{ingrediente.nombre_ingrediente}" creado exitosamente',
                'status': 'success',
                'ingrediente': ingrediente.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear ingrediente: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def listar_ingredientes(filtros=None, pagina=1, por_pagina=50):
        """Lista ingredientes con filtros"""
        try:
            query = Ingrediente.query
            
            # Aplicar filtros
            if filtros:
                if filtros.get('tipo_ingrediente'):
                    query = query.filter(Ingrediente.tipo_ingrediente == filtros['tipo_ingrediente'])
                
                if filtros.get('disponible') is not None:
                    query = query.filter(Ingrediente.disponible == filtros['disponible'])
                
                if filtros.get('buscar'):
                    termino = filtros['buscar']
                    query = query.filter(
                        db.or_(
                            Ingrediente.nombre_ingrediente.ilike(f'%{termino}%'),
                            Ingrediente.descripcion.ilike(f'%{termino}%')
                        )
                    )
            
            # Ordenar por nombre
            query = query.order_by(Ingrediente.nombre_ingrediente)
            
            # Paginación
            ingredientes_paginados = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'ingredientes': [i.to_dict() for i in ingredientes_paginados.items],
                'total': ingredientes_paginados.total,
                'pagina_actual': pagina,
                'total_paginas': ingredientes_paginados.pages,
                'por_pagina': por_pagina,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar ingredientes: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_ingrediente(ingrediente_id, include_caracteristicas=False):
        """Obtiene un ingrediente específico"""
        try:
            ingrediente = Ingrediente.query.get(ingrediente_id)
            if not ingrediente:
                return {
                    'error': 'Ingrediente no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            data = ingrediente.to_dict(include_caracteristicas=include_caracteristicas)
            
            # Agregar promedio nutricional
            promedio = ingrediente.obtener_caracteristica_promedio()
            if promedio:
                data['promedio_nutricional'] = promedio
            
            return {
                'ingrediente': data,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener ingrediente: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def actualizar_ingrediente(ingrediente_id, datos, usuario_id):
        """Actualiza un ingrediente existente"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden actualizar ingredientes',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar ingrediente
            ingrediente = Ingrediente.query.get(ingrediente_id)
            if not ingrediente:
                return {
                    'error': 'Ingrediente no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Validar datos
            errores = IngredientesService.validar_datos_ingrediente(datos, ingrediente_id)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'details': errores
                }, 400
            
            # Actualizar campos
            campos_actualizables = ['nombre_ingrediente', 'tipo_ingrediente', 'descripcion', 'disponible']
            actualizado = False
            
            for campo in campos_actualizables:
                if campo in datos:
                    if campo == 'disponible':
                        setattr(ingrediente, campo, bool(datos[campo]))
                    else:
                        valor = str(datos[campo]).strip() if datos[campo] else None
                        setattr(ingrediente, campo, valor)
                    actualizado = True
            
            if actualizado:
                db.session.commit()
            
            return {
                'message': f'Ingrediente "{ingrediente.nombre_ingrediente}" actualizado exitosamente',
                'status': 'success',
                'ingrediente': ingrediente.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al actualizar ingrediente: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # GESTIÓN DE CARACTERÍSTICAS NUTRICIONALES
    # ===============================
    
    @staticmethod
    def crear_caracteristica_nutricional(datos, usuario_id):
        """Crea una nueva característica nutricional"""
        try:
            # Verificar permisos
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear análisis',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = CaracteristicaNutricional.validar_datos_nutricionales(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'details': errores
                }, 400
            
            # Verificar que ingrediente y consulta existen
            ingrediente = Ingrediente.query.get(datos['idingrediente'])
            consulta = ConsultaBromatologica.query.get(datos['idconsulta'])
            
            if not ingrediente:
                return {
                    'error': 'Ingrediente no encontrado',
                    'status': 'error'
                }, 404
            
            if not consulta:
                return {
                    'error': 'Consulta bromatológica no encontrada',
                    'status': 'error'
                }, 404
            
            # Crear característica nutricional
            caracteristica = CaracteristicaNutricional(
                idingrediente=datos['idingrediente'],
                idconsulta=datos['idconsulta'],
                materia_seca=datos['materia_seca'],
                proteina_cruda=datos['proteina_cruda'],
                ceniza=datos.get('ceniza', 0),
                extracto_etereo=datos.get('extracto_etereo', 0),
                fdn=datos.get('fdn', 0),
                fda=datos.get('fda', 0),
                lignina=datos.get('lignina', 0),
                hemicelulosa=datos.get('hemicelulosa', 0),
                almidon=datos.get('almidon', 0),
                carbohidratos_no_estructurales=datos.get('carbohidratos_no_estructurales', 0),
                carbohidratos_solubles=datos.get('carbohidratos_solubles', 0),
                calcio=datos.get('calcio', 0),
                fosforo=datos.get('fosforo', 0),
                magnesio=datos.get('magnesio', 0),
                potasio=datos.get('potasio', 0),
                azufre=datos.get('azufre', 0),
                ndt=datos.get('ndt', 0),
                digestibilidad_ms=datos.get('digestibilidad_ms', 0),
                energia_bruta_mcal_kg=datos.get('energia_bruta_mcal_kg', 0),
                ed_mcal_kg=datos.get('ed_mcal_kg', 0),
                em_mcal_kg=datos.get('em_mcal_kg', 0),
                enm_mcal_kg=datos.get('enm_mcal_kg', 0),
                eng_mcal_kg=datos.get('eng_mcal_kg', 0),
                enl_mcal_kg=datos.get('enl_mcal_kg', 0)
            )
            
            db.session.add(caracteristica)
            db.session.commit()
            
            return {
                'message': f'Análisis nutricional de "{ingrediente.nombre_ingrediente}" creado exitosamente',
                'status': 'success',
                'caracteristica': caracteristica.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear análisis: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def listar_caracteristicas_por_ingrediente(ingrediente_id):
        """Lista todas las características nutricionales de un ingrediente"""
        try:
            ingrediente = Ingrediente.query.get(ingrediente_id)
            if not ingrediente:
                return {
                    'error': 'Ingrediente no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            caracteristicas = CaracteristicaNutricional.query.filter_by(
                idingrediente=ingrediente_id
            ).join(ConsultaBromatologica).order_by(
                CaracteristicaNutricional.fecha_analisis.desc()
            ).all()
            
            # Calcular promedio
            promedio = ingrediente.obtener_caracteristica_promedio()
            
            return {
                'ingrediente': ingrediente.to_dict(),
                'caracteristicas': [c.to_dict() for c in caracteristicas],
                'promedio': promedio,
                'total_analisis': len(caracteristicas),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener características: {str(e)}',
                'status': 'error'
            }, 500
    
    @staticmethod
    def obtener_ingredientes_disponibles():
        """Obtiene ingredientes disponibles para formulación de raciones"""
        try:
            ingredientes = Ingrediente.query.filter_by(disponible=True).order_by(
                Ingrediente.tipo_ingrediente, Ingrediente.nombre_ingrediente
            ).all()
            
            # Agrupar por tipo
            ingredientes_por_tipo = {}
            for ingrediente in ingredientes:
                tipo = ingrediente.tipo_ingrediente
                if tipo not in ingredientes_por_tipo:
                    ingredientes_por_tipo[tipo] = []
                
                # Incluir promedio nutricional
                data = ingrediente.to_dict()
                promedio = ingrediente.obtener_caracteristica_promedio()
                if promedio:
                    data['promedio_nutricional'] = promedio
                
                ingredientes_por_tipo[tipo].append(data)
            
            return {
                'ingredientes_por_tipo': ingredientes_por_tipo,
                'total_ingredientes': len(ingredientes),
                'tipos_disponibles': list(ingredientes_por_tipo.keys()),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener ingredientes disponibles: {str(e)}',
                'status': 'error'
            }, 500
    
    # ===============================
    # MÉTODOS DE VALIDACIÓN
    # ===============================
    
    @staticmethod
    def validar_datos_ingrediente(datos, ingrediente_id=None):
        """Valida los datos de un ingrediente"""
        errores = []
        
        # Campos requeridos
        if not datos.get('nombre_ingrediente'):
            errores.append('Nombre del ingrediente es requerido')
        elif len(datos['nombre_ingrediente'].strip()) < 3:
            errores.append('El nombre debe tener al menos 3 caracteres')
        elif len(datos['nombre_ingrediente'].strip()) > 100:
            errores.append('El nombre no puede exceder 100 caracteres')
        
        if not datos.get('tipo_ingrediente'):
            errores.append('Tipo de ingrediente es requerido')
        elif datos['tipo_ingrediente'] not in ['Forraje', 'Concentrado', 'Suplemento', 'Mineral']:
            errores.append('Tipo de ingrediente no válido')
        
        # Verificar unicidad del nombre
        if datos.get('nombre_ingrediente'):
            ingrediente_existente = Ingrediente.query.filter_by(
                nombre_ingrediente=datos['nombre_ingrediente'].strip()
            ).first()
            
            if ingrediente_existente and (not ingrediente_id or ingrediente_existente.idingrediente != ingrediente_id):
                errores.append('Ya existe un ingrediente con ese nombre')
        
        return errores
    
    @staticmethod
    def obtener_estadisticas_ingredientes():
        """Obtiene estadísticas generales de ingredientes"""
        try:
            total = Ingrediente.query.count()
            disponibles = Ingrediente.query.filter_by(disponible=True).count()
            
            # Por tipo
            por_tipo = db.session.query(
                Ingrediente.tipo_ingrediente,
                db.func.count(Ingrediente.idingrediente).label('cantidad')
            ).group_by(Ingrediente.tipo_ingrediente).all()
            
            # Con análisis
            con_analisis = db.session.query(
                db.func.count(db.distinct(CaracteristicaNutricional.idingrediente))
            ).scalar() or 0
            
            # Total de análisis
            total_analisis = CaracteristicaNutricional.query.count()
            
            return {
                'estadisticas': {
                    'total_ingredientes': total,
                    'ingredientes_disponibles': disponibles,
                    'ingredientes_no_disponibles': total - disponibles,
                    'ingredientes_con_analisis': con_analisis,
                    'ingredientes_sin_analisis': total - con_analisis,
                    'total_analisis_nutricionales': total_analisis,
                    'por_tipo': [
                        {'tipo': tipo, 'cantidad': cantidad}
                        for tipo, cantidad in por_tipo
                    ]
                },
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener estadísticas: {str(e)}',
                'status': 'error'
            }, 500