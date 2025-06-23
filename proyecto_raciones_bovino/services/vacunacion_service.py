from models import db, Animal, CatalogoVacuna, VacunacionAnimal, Usuario
from datetime import datetime, date
import re

class VacunacionService:
    """
    Servicio para gestión de vacunación
    Contiene toda la lógica de negocio relacionada con vacunas y vacunaciones
    """
    
    # ===============================
    # GESTIÓN DEL CATÁLOGO DE VACUNAS
    # ===============================
    
    @staticmethod
    def crear_vacuna(datos, usuario_id):
        """Crea una nueva vacuna en el catálogo"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear vacunas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = VacunacionService.validar_datos_vacuna(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Verificar que no exista una vacuna con el mismo nombre
            vacuna_existente = CatalogoVacuna.query.filter_by(
                nombre_vacuna=datos['nombre_vacuna'].strip()
            ).first()
            if vacuna_existente:
                return {
                    'error': 'Ya existe una vacuna con ese nombre',
                    'status': 'error',
                    'code': 'DUPLICATE_NAME'
                }, 409
            
            # Crear la vacuna
            vacuna = CatalogoVacuna(
                nombre_vacuna=str(datos['nombre_vacuna']).strip(),
                descripcion=str(datos.get('descripcion', '')).strip() or None,
                frecuencia_dias=int(datos['frecuencia_dias']) if datos.get('frecuencia_dias') else None,
                activo=bool(datos.get('activo', True))
            )
            
            db.session.add(vacuna)
            db.session.commit()
            
            return {
                'message': f'Vacuna "{vacuna.nombre_vacuna}" creada exitosamente',
                'status': 'success',
                'vacuna': vacuna.to_dict(),
                'creado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear vacuna: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def listar_vacunas(filtros=None, pagina=1, por_pagina=50):
        """Lista vacunas del catálogo con filtros y paginación"""
        try:
            query = CatalogoVacuna.query
            
            # Aplicar filtros
            if filtros:
                if filtros.get('activo') is not None:
                    query = query.filter(CatalogoVacuna.activo == filtros['activo'])
                
                if filtros.get('buscar'):
                    termino = filtros['buscar']
                    query = query.filter(
                        db.or_(
                            CatalogoVacuna.nombre_vacuna.ilike(f'%{termino}%'),
                            CatalogoVacuna.descripcion.ilike(f'%{termino}%')
                        )
                    )
            
            # Ordenar por nombre
            query = query.order_by(CatalogoVacuna.nombre_vacuna)
            
            # Paginación
            vacunas_paginadas = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'vacunas': [v.to_dict() for v in vacunas_paginadas.items],
                'total': vacunas_paginadas.total,
                'pagina_actual': pagina,
                'total_paginas': vacunas_paginadas.pages,
                'por_pagina': por_pagina,
                'tiene_siguiente': vacunas_paginadas.has_next,
                'tiene_anterior': vacunas_paginadas.has_prev,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar vacunas: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def actualizar_vacuna(vacuna_id, datos, usuario_id):
        """Actualiza una vacuna del catálogo"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden actualizar vacunas',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar la vacuna
            vacuna = CatalogoVacuna.query.get(vacuna_id)
            if not vacuna:
                return {
                    'error': 'Vacuna no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Validar datos
            errores = VacunacionService.validar_datos_vacuna(datos, vacuna_id)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Actualizar
            actualizado = vacuna.actualizar_datos(datos)
            
            return {
                'message': f'Vacuna "{vacuna.nombre_vacuna}" actualizada exitosamente',
                'status': 'success',
                'vacuna': vacuna.to_dict(),
                'actualizado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al actualizar vacuna: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    # ===============================
    # GESTIÓN DE VACUNACIONES
    # ===============================
    
    @staticmethod
    def registrar_vacunacion(datos, usuario_id):
        """Registra una nueva vacunación"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden registrar vacunaciones',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar datos
            errores = VacunacionAnimal.validar_datos_vacunacion(datos)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
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
            
            # Verificar que la vacuna existe y está activa
            vacuna = CatalogoVacuna.query.get(datos['idvacuna'])
            if not vacuna:
                return {
                    'error': 'Vacuna no encontrada',
                    'status': 'error',
                    'code': 'VACCINE_NOT_FOUND'
                }, 404
            
            if not vacuna.activo:
                return {
                    'error': 'La vacuna no está activa',
                    'status': 'error',
                    'code': 'VACCINE_INACTIVE'
                }, 400
            
            # Convertir fechas
            fecha_aplicacion = datos['fecha_aplicacion']
            if isinstance(fecha_aplicacion, str):
                fecha_aplicacion = datetime.strptime(fecha_aplicacion, '%Y-%m-%d').date()
            
            # Verificar duplicados
            if VacunacionAnimal.verificar_duplicado(datos['idanimal'], datos['idvacuna'], fecha_aplicacion):
                return {
                    'error': 'Ya existe una vacunación similar en las últimas 4 semanas',
                    'status': 'error',
                    'code': 'DUPLICATE_VACCINATION'
                }, 409
            
            # Crear la vacunación
            vacunacion = VacunacionAnimal(
                idanimal=datos['idanimal'],
                idvacuna=datos['idvacuna'],
                fecha_aplicacion=fecha_aplicacion,
                dosis=str(datos.get('dosis', '')).strip() or None,
                lote_vacuna=str(datos.get('lote_vacuna', '')).strip() or None,
                veterinario=str(datos.get('veterinario', '')).strip() or None,
                observaciones=str(datos.get('observaciones', '')).strip() or None
            )
            
            # Calcular próxima dosis
            if datos.get('proxima_dosis'):
                if isinstance(datos['proxima_dosis'], str):
                    vacunacion.proxima_dosis = datetime.strptime(datos['proxima_dosis'], '%Y-%m-%d').date()
                else:
                    vacunacion.proxima_dosis = datos['proxima_dosis']
            else:
                # Calcular automáticamente basado en la frecuencia
                vacunacion.proxima_dosis = vacunacion.calcular_proxima_dosis_automatica()
            
            db.session.add(vacunacion)
            db.session.commit()
            
            return {
                'message': f'Vacunación de {animal.hierro} con {vacuna.nombre_vacuna} registrada exitosamente',
                'status': 'success',
                'vacunacion': vacunacion.to_dict(),
                'registrado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al registrar vacunación: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def listar_vacunaciones(filtros=None, pagina=1, por_pagina=50):
        """Lista vacunaciones con filtros y paginación"""
        try:
            query = VacunacionAnimal.query.join(Animal).join(CatalogoVacuna)
            
            # Aplicar filtros
            if filtros:
                if filtros.get('hacienda_id'):
                    query = query.filter(Animal.idhacienda == filtros['hacienda_id'])
                
                if filtros.get('animal_id'):
                    query = query.filter(VacunacionAnimal.idanimal == filtros['animal_id'])
                
                if filtros.get('vacuna_id'):
                    query = query.filter(VacunacionAnimal.idvacuna == filtros['vacuna_id'])
                
                if filtros.get('fecha_desde'):
                    fecha_desde = datetime.strptime(filtros['fecha_desde'], '%Y-%m-%d').date()
                    query = query.filter(VacunacionAnimal.fecha_aplicacion >= fecha_desde)
                
                if filtros.get('fecha_hasta'):
                    fecha_hasta = datetime.strptime(filtros['fecha_hasta'], '%Y-%m-%d').date()
                    query = query.filter(VacunacionAnimal.fecha_aplicacion <= fecha_hasta)
                
                if filtros.get('veterinario'):
                    query = query.filter(VacunacionAnimal.veterinario.ilike(f"%{filtros['veterinario']}%"))
                
                if filtros.get('buscar'):
                    termino = filtros['buscar']
                    query = query.filter(
                        db.or_(
                            Animal.hierro.ilike(f'%{termino}%'),
                            CatalogoVacuna.nombre_vacuna.ilike(f'%{termino}%'),
                            VacunacionAnimal.veterinario.ilike(f'%{termino}%'),
                            VacunacionAnimal.lote_vacuna.ilike(f'%{termino}%')
                        )
                    )
            
            # Ordenar por fecha de aplicación descendente
            query = query.order_by(VacunacionAnimal.fecha_aplicacion.desc())
            
            # Paginación
            vacunaciones_paginadas = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'vacunaciones': [v.to_dict() for v in vacunaciones_paginadas.items],
                'total': vacunaciones_paginadas.total,
                'pagina_actual': pagina,
                'total_paginas': vacunaciones_paginadas.pages,
                'por_pagina': por_pagina,
                'tiene_siguiente': vacunaciones_paginadas.has_next,
                'tiene_anterior': vacunaciones_paginadas.has_prev,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar vacunaciones: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_vacunaciones_animal(animal_id):
        """Obtiene el historial de vacunaciones de un animal"""
        try:
            # Verificar que el animal existe
            animal = Animal.query.get(animal_id)
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            vacunaciones = VacunacionAnimal.obtener_por_animal(animal_id)
            
            return {
                'animal': {
                    'idanimal': animal.idanimal,
                    'hierro': animal.hierro,
                    'sexo': animal.sexo,
                    'raza': animal.raza,
                    'hacienda': animal.hacienda.nombre if animal.hacienda else None
                },
                'vacunaciones': [v.to_dict() for v in vacunaciones],
                'total': len(vacunaciones),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener vacunaciones del animal: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_proximas_dosis(dias_adelante=30, hacienda_id=None):
        """Obtiene animales que necesitan próximas dosis"""
        try:
            proximas = VacunacionAnimal.obtener_proximas_dosis(dias_adelante, hacienda_id)
            
            return {
                'proximas_dosis': [v.to_dict() for v in proximas],
                'total': len(proximas),
                'dias_adelante': dias_adelante,
                'hacienda_id': hacienda_id,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener próximas dosis: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_vencidas(hacienda_id=None):
        """Obtiene vacunaciones con dosis vencidas"""
        try:
            vencidas = VacunacionAnimal.obtener_vencidas(hacienda_id)
            
            return {
                'dosis_vencidas': [v.to_dict() for v in vencidas],
                'total': len(vencidas),
                'hacienda_id': hacienda_id,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener dosis vencidas: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_estadisticas_vacunacion(hacienda_id=None):
        """Obtiene estadísticas de vacunación"""
        try:
            estadisticas = VacunacionAnimal.obtener_estadisticas_generales(hacienda_id)
            
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
    def eliminar_vacunacion(vacunacion_id, usuario_id):
        """Elimina una vacunación (solo administradores)"""
        try:
            # Verificar permisos del usuario (solo administradores)
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden eliminar vacunaciones',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar la vacunación
            vacunacion = VacunacionAnimal.query.get(vacunacion_id)
            if not vacunacion:
                return {
                    'error': 'Vacunación no encontrada',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            animal_hierro = vacunacion.animal.hierro if vacunacion.animal else "N/A"
            vacuna_nombre = vacunacion.vacuna.nombre_vacuna if vacunacion.vacuna else "N/A"
            
            db.session.delete(vacunacion)
            db.session.commit()
            
            return {
                'message': f'Vacunación de {animal_hierro} con {vacuna_nombre} eliminada exitosamente',
                'status': 'success',
                'eliminado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al eliminar vacunación: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    # ===============================
    # MÉTODOS DE VALIDACIÓN
    # ===============================
    
    @staticmethod
    def validar_datos_vacuna(datos, vacuna_id=None):
        """Valida los datos de una vacuna"""
        errores = []
        
        # Validar nombre de vacuna
        if datos.get('nombre_vacuna'):
            es_valido, mensaje = CatalogoVacuna.validar_nombre_vacuna(datos['nombre_vacuna'])
            if not es_valido:
                errores.append(mensaje)
            else:
                # Verificar unicidad del nombre
                vacuna_existente = CatalogoVacuna.query.filter_by(
                    nombre_vacuna=datos['nombre_vacuna'].strip()
                ).first()
                if vacuna_existente and (not vacuna_id or vacuna_existente.idvacuna != vacuna_id):
                    errores.append('Ya existe una vacuna con ese nombre')
        else:
            errores.append('Nombre de vacuna es requerido')
        
        # Validar frecuencia
        if datos.get('frecuencia_dias') is not None:
            es_valido, mensaje = CatalogoVacuna.validar_frecuencia(datos['frecuencia_dias'])
            if not es_valido:
                errores.append(mensaje)
        
        # Validar descripción
        if datos.get('descripcion'):
            descripcion = str(datos['descripcion']).strip()
            if len(descripcion) > 1000:
                errores.append('La descripción no puede exceder 1000 caracteres')
        
        return errores
    
    @staticmethod
    def obtener_vacunas_activas():
        """Obtiene todas las vacunas activas para formularios"""
        try:
            vacunas = CatalogoVacuna.obtener_activas()
            return {
                'vacunas': [v.to_dict() for v in vacunas],
                'status': 'success'
            }, 200
        except Exception as e:
            return {
                'error': f'Error al obtener vacunas activas: {str(e)}',
                'status': 'error'
            }, 500