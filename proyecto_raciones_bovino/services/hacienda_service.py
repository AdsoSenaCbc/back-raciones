from models import db, Hacienda, Usuario
from datetime import datetime
import re

class HaciendaService:
    """
    Servicio para gestión de haciendas
    Contiene toda la lógica de negocio relacionada con haciendas
    """
    
    @staticmethod
    def validar_datos_hacienda(datos, validar_nit_unico=True, hacienda_id=None):
        """Valida los datos de una hacienda"""
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = ['nit', 'nombre', 'propietario']
        for campo in campos_requeridos:
            if not datos.get(campo) or not str(datos[campo]).strip():
                errores.append(f'{campo.capitalize()} es requerido')
        
        # Validar NIT
        if datos.get('nit'):
            nit = str(datos['nit']).strip()
            es_valido, mensaje = Hacienda.validar_nit(nit)
            if not es_valido:
                errores.append(mensaje)
            elif validar_nit_unico:
                # Verificar unicidad del NIT
                hacienda_existente = Hacienda.query.filter_by(nit=nit).first()
                if hacienda_existente and (not hacienda_id or hacienda_existente.idhacienda != hacienda_id):
                    errores.append('Ya existe una hacienda registrada con este NIT')
        
        # Validar nombre
        if datos.get('nombre'):
            nombre = str(datos['nombre']).strip()
            if len(nombre) < 3:
                errores.append('El nombre debe tener al menos 3 caracteres')
            elif len(nombre) > 100:
                errores.append('El nombre no puede exceder 100 caracteres')
        
        # Validar propietario
        if datos.get('propietario'):
            propietario = str(datos['propietario']).strip()
            if len(propietario) < 3:
                errores.append('El nombre del propietario debe tener al menos 3 caracteres')
            elif len(propietario) > 100:
                errores.append('El nombre del propietario no puede exceder 100 caracteres')
            
            # Solo letras, espacios y algunos caracteres especiales
            patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-\.]+$'
            if not re.match(patron, propietario):
                errores.append('El nombre del propietario solo puede contener letras')
        
        # Validar teléfono
        if datos.get('telefono'):
            telefono = str(datos['telefono']).strip()
            if telefono:
                patron_telefono = r'^[0-9\+\-\(\)\s]{7,15}$'
                if not re.match(patron_telefono, telefono):
                    errores.append('Formato de teléfono inválido')
        
        # Validar hectáreas
        if datos.get('hectareas') is not None:
            es_valido, mensaje = Hacienda.validar_hectareas(datos['hectareas'])
            if not es_valido:
                errores.append(mensaje)
        
        # Validar campos de texto opcional
        campos_texto = ['poblacion', 'municipio', 'departamento', 'direccion', 'localizacion', 'hierro']
        for campo in campos_texto:
            if datos.get(campo):
                valor = str(datos[campo]).strip()
                if len(valor) > 150:  # Longitud máxima general
                    errores.append(f'{campo.capitalize()} no puede exceder 150 caracteres')
        
        return errores
    
    @staticmethod
    def crear_hacienda(datos, usuario_id):
        """Crea una nueva hacienda"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear haciendas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = HaciendaService.validar_datos_hacienda(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Crear la hacienda
            hacienda = Hacienda(
                nit=str(datos['nit']).strip(),
                nombre=str(datos['nombre']).strip(),
                propietario=str(datos['propietario']).strip(),
                telefono=str(datos.get('telefono', '')).strip() or None,
                poblacion=str(datos.get('poblacion', '')).strip() or None,
                municipio=str(datos.get('municipio', '')).strip() or None,
                departamento=str(datos.get('departamento', '')).strip() or None,
                direccion=str(datos.get('direccion', '')).strip() or None,
                localizacion=str(datos.get('localizacion', '')).strip() or None,
                hierro=str(datos.get('hierro', '')).strip() or None,
                hectareas=float(datos['hectareas']) if datos.get('hectareas') else None,
                activo=True  # Por defecto activa
            )
            
            db.session.add(hacienda)
            db.session.commit()
            
            return {
                'message': f'Hacienda "{hacienda.nombre}" creada exitosamente',
                'status': 'success',
                'hacienda': hacienda.to_dict(),
                'creado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear hacienda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_hacienda(hacienda_id):
        """Obtiene una hacienda por ID"""
        try:
            hacienda = Hacienda.query.get(hacienda_id)
            
            if not hacienda:
                return {
                    'error': 'Hacienda no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            return {
                'hacienda': hacienda.to_dict(),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener hacienda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def listar_haciendas(filtros=None, pagina=1, por_pagina=50):
        """Lista haciendas con filtros y paginación"""
        try:
            query = Hacienda.query
            
            # Aplicar filtros
            if filtros:
                if filtros.get('activo') is not None:
                    query = query.filter(Hacienda.activo == filtros['activo'])
                
                if filtros.get('departamento'):
                    query = query.filter(
                        Hacienda.departamento.ilike(f"%{filtros['departamento']}%")
                    )
                
                if filtros.get('municipio'):
                    query = query.filter(
                        Hacienda.municipio.ilike(f"%{filtros['municipio']}%")
                    )
                
                if filtros.get('propietario'):
                    query = query.filter(
                        Hacienda.propietario.ilike(f"%{filtros['propietario']}%")
                    )
                
                if filtros.get('buscar'):
                    termino = filtros['buscar']
                    query = query.filter(
                        db.or_(
                            Hacienda.nombre.ilike(f'%{termino}%'),
                            Hacienda.propietario.ilike(f'%{termino}%'),
                            Hacienda.nit.ilike(f'%{termino}%'),
                            Hacienda.municipio.ilike(f'%{termino}%')
                        )
                    )
            
            # Ordenar por nombre
            query = query.order_by(Hacienda.nombre)
            
            # Paginación
            haciendas_paginadas = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'haciendas': [h.to_dict() for h in haciendas_paginadas.items],
                'total': haciendas_paginadas.total,
                'pagina_actual': pagina,
                'total_paginas': haciendas_paginadas.pages,
                'por_pagina': por_pagina,
                'tiene_siguiente': haciendas_paginadas.has_next,
                'tiene_anterior': haciendas_paginadas.has_prev,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar haciendas: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def actualizar_hacienda(hacienda_id, datos, usuario_id):
        """Actualiza una hacienda existente"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden actualizar haciendas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar la hacienda
            hacienda = Hacienda.query.get(hacienda_id)
            if not hacienda:
                return {
                    'error': 'Hacienda no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Validar datos (sin validar NIT único si no cambió)
            validar_nit_unico = datos.get('nit') and datos['nit'].strip() != hacienda.nit
            errores = HaciendaService.validar_datos_hacienda(datos, validar_nit_unico, hacienda_id)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Actualizar campos
            campos_actualizables = [
                'nit', 'nombre', 'propietario', 'telefono', 'poblacion',
                'municipio', 'departamento', 'direccion', 'localizacion',
                'hierro', 'hectareas'
            ]
            
            actualizado = False
            for campo in campos_actualizables:
                if campo in datos:
                    if campo == 'hectareas':
                        if datos[campo] is not None:
                            setattr(hacienda, campo, float(datos[campo]))
                        else:
                            setattr(hacienda, campo, None)
                    else:
                        valor = str(datos[campo]).strip() if datos[campo] else None
                        setattr(hacienda, campo, valor)
                    actualizado = True
            
            if actualizado:
                db.session.commit()
            
            return {
                'message': f'Hacienda "{hacienda.nombre}" actualizada exitosamente',
                'status': 'success',
                'hacienda': hacienda.to_dict(),
                'actualizado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al actualizar hacienda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def cambiar_estado_hacienda(hacienda_id, activo, usuario_id):
        """Activa o desactiva una hacienda"""
        try:
            # Verificar permisos del usuario (solo administradores)
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden cambiar el estado de haciendas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar la hacienda
            hacienda = Hacienda.query.get(hacienda_id)
            if not hacienda:
                return {
                    'error': 'Hacienda no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Cambiar estado
            hacienda.activo = activo
            db.session.commit()
            
            estado_texto = 'activada' if activo else 'desactivada'
            
            return {
                'message': f'Hacienda "{hacienda.nombre}" {estado_texto} exitosamente',
                'status': 'success',
                'hacienda': hacienda.to_dict(),
                'cambiado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al cambiar estado de hacienda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def eliminar_hacienda(hacienda_id, usuario_id):
        """Elimina una hacienda (solo si no tiene datos relacionados)"""
        try:
            # Verificar permisos del usuario (solo administradores)
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden eliminar haciendas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar la hacienda
            hacienda = Hacienda.query.get(hacienda_id)
            if not hacienda:
                return {
                    'error': 'Hacienda no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Verificar si tiene datos relacionados (futuras tablas)
            # if hacienda.bovinos or hacienda.raciones:
            #     return {
            #         'error': 'No se puede eliminar la hacienda porque tiene datos relacionados',
            #         'status': 'error',
            #         'code': 'HAS_RELATED_DATA'
            #     }, 409
            
            nombre_hacienda = hacienda.nombre
            db.session.delete(hacienda)
            db.session.commit()
            
            return {
                'message': f'Hacienda "{nombre_hacienda}" eliminada exitosamente',
                'status': 'success',
                'eliminado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al eliminar hacienda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_estadisticas():
        """Obtiene estadísticas de haciendas"""
        try:
            estadisticas = Hacienda.obtener_estadisticas()
            
            return {
                'estadisticas': estadisticas,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener estadísticas: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def buscar_haciendas(termino, usuario_id):
        """Búsqueda general de haciendas"""
        try:
            if not termino or len(termino.strip()) < 2:
                return {
                    'error': 'El término de búsqueda debe tener al menos 2 caracteres',
                    'status': 'error',
                    'code': 'INVALID_SEARCH_TERM'
                }, 400
            
            haciendas = Hacienda.buscar_general(termino.strip())
            
            return {
                'haciendas': [h.to_dict() for h in haciendas],
                'total': len(haciendas),
                'termino_busqueda': termino.strip(),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error en búsqueda: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500