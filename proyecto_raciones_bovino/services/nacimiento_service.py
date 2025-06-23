from models import db, Animal, Nacimiento, Usuario, Hacienda
from datetime import datetime, date, timedelta
import re

class NacimientoService:
    """
    Servicio para gestión de nacimientos
    Contiene toda la lógica de negocio relacionada con nacimientos de animales
    """
    
    @staticmethod
    def crear_nacimiento(datos, usuario_id):
        """Registra un nuevo nacimiento"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden registrar nacimientos',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos básicos
            errores = Nacimiento.validar_datos_nacimiento(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Verificar compatibilidad de animales
            errores_compatibilidad = Nacimiento.verificar_animales_compatibles(
                datos['idanimal_cria'],
                datos['idanimal_madre'],
                datos.get('idanimal_padre')
            )
            if errores_compatibilidad:
                return {
                    'error': 'Errores de compatibilidad',
                    'status': 'error',
                    'code': 'COMPATIBILITY_ERROR',
                    'details': errores_compatibilidad
                }, 400
            
            # Verificar que no exista ya un nacimiento para esta cría
            nacimiento_existente = Nacimiento.query.filter_by(
                idanimal_cria=datos['idanimal_cria']
            ).first()
            if nacimiento_existente:
                return {
                    'error': 'Ya existe un registro de nacimiento para esta cría',
                    'status': 'error',
                    'code': 'DUPLICATE_BIRTH'
                }, 409
            
            # Crear el nacimiento
            nacimiento = Nacimiento(
                idanimal_cria=datos['idanimal_cria'],
                idanimal_madre=datos['idanimal_madre'],
                idanimal_padre=datos.get('idanimal_padre'),
                tipo_parto=datos.get('tipo_parto', 'Natural'),
                complicaciones=str(datos.get('complicaciones', '')).strip() or None,
                numero_registro=str(datos.get('numero_registro', '')).strip() or None,
                vacunas_aplicadas=bool(datos.get('vacunas_aplicadas', False)),
                observaciones=str(datos.get('observaciones', '')).strip() or None,
                peso_nacimiento=float(datos['peso_nacimiento']) if datos.get('peso_nacimiento') else None
            )
            
            # Manejar fecha de nacimiento
            if isinstance(datos['fecha_nacimiento'], str):
                nacimiento.fecha_nacimiento = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
            else:
                nacimiento.fecha_nacimiento = datos['fecha_nacimiento']
            
            db.session.add(nacimiento)
            db.session.commit()
            
            # Actualizar el registro de la cría con la fecha de nacimiento
            nacimiento.actualizar_registro_cria()
            
            # Actualizar número de partos de la madre si es necesario
            madre = Animal.query.get(datos['idanimal_madre'])
            if madre:
                # Contar nacimientos de esta madre
                total_partos = Nacimiento.query.filter_by(idanimal_madre=madre.idanimal).count()
                if total_partos > madre.numero_partos:
                    madre.numero_partos = total_partos
                    madre.ultimo_parto = nacimiento.fecha_nacimiento
                    db.session.commit()
            
            return {
                'message': f'Nacimiento registrado exitosamente',
                'status': 'success',
                'nacimiento': nacimiento.to_dict(),
                'registrado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al registrar nacimiento: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_nacimiento(nacimiento_id):
        """Obtiene un nacimiento por ID"""
        try:
            nacimiento = Nacimiento.query.get(nacimiento_id)
            
            if not nacimiento:
                return {
                    'error': 'Nacimiento no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            return {
                'nacimiento': nacimiento.to_dict(),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener nacimiento: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def listar_nacimientos(filtros=None, pagina=1, por_pagina=50):
        """Lista nacimientos con filtros y paginación"""
        try:
            query = Nacimiento.query.join(
                Animal, Nacimiento.idanimal_cria == Animal.idanimal
            ).join(Hacienda)
            
            # Aplicar filtros
            if filtros:
                if filtros.get('hacienda_id'):
                    query = query.filter(Animal.idhacienda == filtros['hacienda_id'])
                
                if filtros.get('madre_id'):
                    query = query.filter(Nacimiento.idanimal_madre == filtros['madre_id'])
                
                if filtros.get('padre_id'):
                    query = query.filter(Nacimiento.idanimal_padre == filtros['padre_id'])
                
                if filtros.get('tipo_parto'):
                    query = query.filter(Nacimiento.tipo_parto == filtros['tipo_parto'])
                
                if filtros.get('fecha_desde'):
                    fecha_desde = datetime.strptime(filtros['fecha_desde'], '%Y-%m-%d').date()
                    query = query.filter(Nacimiento.fecha_nacimiento >= fecha_desde)
                
                if filtros.get('fecha_hasta'):
                    fecha_hasta = datetime.strptime(filtros['fecha_hasta'], '%Y-%m-%d').date()
                    query = query.filter(Nacimiento.fecha_nacimiento <= fecha_hasta)
                
                if filtros.get('vacunas_aplicadas') is not None:
                    query = query.filter(Nacimiento.vacunas_aplicadas == filtros['vacunas_aplicadas'])
                
                if filtros.get('buscar'):
                    termino = filtros['buscar']
                    query = query.filter(
                        db.or_(
                            Nacimiento.numero_registro.ilike(f'%{termino}%'),
                            Animal.hierro.ilike(f'%{termino}%'),
                            Nacimiento.observaciones.ilike(f'%{termino}%')
                        )
                    )
            
            # Ordenar por fecha de nacimiento descendente
            query = query.order_by(Nacimiento.fecha_nacimiento.desc())
            
            # Paginación
            nacimientos_paginados = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'nacimientos': [n.to_dict() for n in nacimientos_paginados.items],
                'total': nacimientos_paginados.total,
                'pagina_actual': pagina,
                'total_paginas': nacimientos_paginados.pages,
                'por_pagina': por_pagina,
                'tiene_siguiente': nacimientos_paginados.has_next,
                'tiene_anterior': nacimientos_paginados.has_prev,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar nacimientos: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def actualizar_nacimiento(nacimiento_id, datos, usuario_id):
        """Actualiza un nacimiento existente"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden actualizar nacimientos',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar el nacimiento
            nacimiento = Nacimiento.query.get(nacimiento_id)
            if not nacimiento:
                return {
                    'error': 'Nacimiento no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Validar datos si se están cambiando campos críticos
            campos_criticos = ['idanimal_cria', 'idanimal_madre', 'idanimal_padre', 'fecha_nacimiento']
            cambios_criticos = any(campo in datos for campo in campos_criticos)
            
            if cambios_criticos:
                # Crear datos temporales para validación
                datos_validacion = nacimiento.to_dict(include_related=False)
                datos_validacion.update(datos)
                
                errores = Nacimiento.validar_datos_nacimiento(datos_validacion)
                if errores:
                    return {
                        'error': 'Errores de validación',
                        'status': 'error',
                        'code': 'VALIDATION_ERROR',
                        'details': errores
                    }, 400
                
                # Verificar compatibilidad si se cambian los animales
                if any(campo in datos for campo in ['idanimal_cria', 'idanimal_madre', 'idanimal_padre']):
                    errores_compatibilidad = Nacimiento.verificar_animales_compatibles(
                        datos.get('idanimal_cria', nacimiento.idanimal_cria),
                        datos.get('idanimal_madre', nacimiento.idanimal_madre),
                        datos.get('idanimal_padre', nacimiento.idanimal_padre)
                    )
                    if errores_compatibilidad:
                        return {
                            'error': 'Errores de compatibilidad',
                            'status': 'error',
                            'code': 'COMPATIBILITY_ERROR',
                            'details': errores_compatibilidad
                        }, 400
            
            # Actualizar campos
            campos_actualizables = [
                'idanimal_padre', 'peso_nacimiento', 'tipo_parto', 'complicaciones',
                'numero_registro', 'vacunas_aplicadas', 'observaciones'
            ]
            
            actualizado = False
            for campo in campos_actualizables:
                if campo in datos:
                    if campo == 'peso_nacimiento':
                        if datos[campo] is not None:
                            setattr(nacimiento, campo, float(datos[campo]))
                        else:
                            setattr(nacimiento, campo, None)
                    elif campo == 'vacunas_aplicadas':
                        setattr(nacimiento, campo, bool(datos[campo]))
                    elif campo == 'idanimal_padre':
                        setattr(nacimiento, campo, datos[campo] if datos[campo] else None)
                    else:
                        valor = str(datos[campo]).strip() if datos[campo] else None
                        setattr(nacimiento, campo, valor)
                    actualizado = True
            
            # Manejar fecha de nacimiento (campo crítico, solo admin)
            if 'fecha_nacimiento' in datos and usuario.es_administrador():
                if datos['fecha_nacimiento']:
                    try:
                        if isinstance(datos['fecha_nacimiento'], str):
                            fecha = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
                        else:
                            fecha = datos['fecha_nacimiento']
                        setattr(nacimiento, 'fecha_nacimiento', fecha)
                        actualizado = True
                    except (ValueError, TypeError):
                        pass
            
            if actualizado:
                db.session.commit()
            
            return {
                'message': f'Nacimiento actualizado exitosamente',
                'status': 'success',
                'nacimiento': nacimiento.to_dict(),
                'actualizado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al actualizar nacimiento: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def eliminar_nacimiento(nacimiento_id, usuario_id):
        """Elimina un nacimiento (solo administradores)"""
        try:
            # Verificar permisos del usuario (solo administradores)
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden eliminar nacimientos',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar el nacimiento
            nacimiento = Nacimiento.query.get(nacimiento_id)
            if not nacimiento:
                return {
                    'error': 'Nacimiento no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            cria_hierro = nacimiento.cria.hierro if nacimiento.cria else "N/A"
            
            db.session.delete(nacimiento)
            db.session.commit()
            
            return {
                'message': f'Nacimiento de la cría "{cria_hierro}" eliminado exitosamente',
                'status': 'success',
                'eliminado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al eliminar nacimiento: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_nacimientos_por_madre(madre_id):
        """Obtiene todos los nacimientos de una madre específica"""
        try:
            # Verificar que la madre existe
            madre = Animal.query.get(madre_id)
            if not madre:
                return {
                    'error': 'Animal madre no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            nacimientos = Nacimiento.obtener_por_madre(madre_id)
            
            return {
                'madre': {
                    'idanimal': madre.idanimal,
                    'hierro': madre.hierro,
                    'sexo': madre.sexo,
                    'raza': madre.raza,
                    'numero_partos': madre.numero_partos,
                    'hacienda': madre.hacienda.nombre if madre.hacienda else None
                },
                'nacimientos': [n.to_dict() for n in nacimientos],
                'total': len(nacimientos),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener nacimientos de la madre: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_nacimientos_por_padre(padre_id):
        """Obtiene todos los nacimientos de un padre específico"""
        try:
            # Verificar que el padre existe
            padre = Animal.query.get(padre_id)
            if not padre:
                return {
                    'error': 'Animal padre no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            nacimientos = Nacimiento.obtener_por_padre(padre_id)
            
            return {
                'padre': {
                    'idanimal': padre.idanimal,
                    'hierro': padre.hierro,
                    'sexo': padre.sexo,
                    'raza': padre.raza,
                    'hacienda': padre.hacienda.nombre if padre.hacienda else None
                },
                'nacimientos': [n.to_dict() for n in nacimientos],
                'total': len(nacimientos),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener nacimientos del padre: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_crias_sin_vacunar(hacienda_id=None):
        """Obtiene crías que necesitan vacunación inicial"""
        try:
            crias_sin_vacunar = Nacimiento.obtener_crias_sin_vacunar(hacienda_id)
            
            return {
                'crias_sin_vacunar': [n.to_dict() for n in crias_sin_vacunar],
                'total': len(crias_sin_vacunar),
                'hacienda_id': hacienda_id,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener crías sin vacunar: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_nacimientos_recientes(dias=30, hacienda_id=None):
        """Obtiene nacimientos recientes"""
        try:
            nacimientos_recientes = Nacimiento.obtener_recientes(dias, hacienda_id)
            
            return {
                'nacimientos_recientes': [n.to_dict() for n in nacimientos_recientes],
                'total': len(nacimientos_recientes),
                'dias': dias,
                'hacienda_id': hacienda_id,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener nacimientos recientes: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_estadisticas_nacimientos(hacienda_id=None):
        """Obtiene estadísticas de nacimientos"""
        try:
            estadisticas = Nacimiento.obtener_estadisticas_generales(hacienda_id)
            
            return {
                'estadisticas': estadisticas,
                'hacienda_id': hacienda_id,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener estadísticas: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def buscar_nacimientos(termino, hacienda_id=None):
        """Búsqueda general de nacimientos"""
        try:
            if not termino or len(termino.strip()) < 2:
                return {
                    'error': 'El término de búsqueda debe tener al menos 2 caracteres',
                    'status': 'error',
                    'code': 'INVALID_SEARCH_TERM'
                }, 400
            
            nacimientos = Nacimiento.buscar_general(termino.strip(), hacienda_id)
            
            return {
                'nacimientos': [n.to_dict() for n in nacimientos],
                'total': len(nacimientos),
                'termino_busqueda': termino.strip(),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error en búsqueda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def marcar_vacunas_aplicadas(nacimiento_id, usuario_id):
        """Marca las vacunas como aplicadas en un nacimiento"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden marcar vacunas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar el nacimiento
            nacimiento = Nacimiento.query.get(nacimiento_id)
            if not nacimiento:
                return {
                    'error': 'Nacimiento no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            nacimiento.vacunas_aplicadas = True
            db.session.commit()
            
            return {
                'message': f'Vacunas marcadas como aplicadas para la cría "{nacimiento.cria.hierro if nacimiento.cria else "N/A"}"',
                'status': 'success',
                'nacimiento': nacimiento.to_dict(),
                'actualizado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al marcar vacunas: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500