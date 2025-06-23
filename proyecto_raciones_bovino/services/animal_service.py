from models import db, Animal, EstadoAnimal, Hacienda, Usuario
from datetime import datetime, date
import re

class AnimalService:
    """
    Servicio para gestión de animales
    Contiene toda la lógica de negocio relacionada con animales
    """
    
    @staticmethod
    def validar_datos_animal(datos, validar_hierro_unico=True, hacienda_id=None, animal_id=None):
        """Valida los datos de un animal"""
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = ['hierro', 'sexo']
        for campo in campos_requeridos:
            if not datos.get(campo) or not str(datos[campo]).strip():
                errores.append(f'{campo.capitalize()} es requerido')
        
        # Validar hierro
        if datos.get('hierro') and hacienda_id:
            hierro = str(datos['hierro']).strip()
            es_valido, mensaje = Animal.validar_hierro(hierro, hacienda_id, animal_id)
            if not es_valido:
                errores.append(mensaje)
        
        # Validar sexo
        if datos.get('sexo'):
            sexo = datos['sexo']
            if sexo not in ['Macho', 'Hembra']:
                errores.append('Sexo debe ser Macho o Hembra')
        
        # Validar peso
        if datos.get('peso_actual') is not None:
            es_valido, mensaje = Animal.validar_peso(datos['peso_actual'])
            if not es_valido:
                errores.append(mensaje)
        
        # Validar número de partos
        if datos.get('numero_partos') is not None:
            try:
                partos = int(datos['numero_partos'])
                if partos < 0:
                    errores.append('El número de partos no puede ser negativo')
            except (ValueError, TypeError):
                errores.append('Número de partos debe ser un entero válido')
        
        # Validar fechas
        fecha_nacimiento = None
        if datos.get('fecha_nacimiento'):
            try:
                if isinstance(datos['fecha_nacimiento'], str):
                    fecha_nacimiento = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
                else:
                    fecha_nacimiento = datos['fecha_nacimiento']
            except (ValueError, TypeError):
                errores.append('Formato de fecha de nacimiento inválido (YYYY-MM-DD)')
        
        ultimo_parto = None
        if datos.get('ultimo_parto'):
            try:
                if isinstance(datos['ultimo_parto'], str):
                    ultimo_parto = datetime.strptime(datos['ultimo_parto'], '%Y-%m-%d').date()
                else:
                    ultimo_parto = datos['ultimo_parto']
            except (ValueError, TypeError):
                errores.append('Formato de fecha de último parto inválido (YYYY-MM-DD)')
        
        ultimo_aborto = None
        if datos.get('ultimo_aborto'):
            try:
                if isinstance(datos['ultimo_aborto'], str):
                    ultimo_aborto = datetime.strptime(datos['ultimo_aborto'], '%Y-%m-%d').date()
                else:
                    ultimo_aborto = datos['ultimo_aborto']
            except (ValueError, TypeError):
                errores.append('Formato de fecha de último aborto inválido (YYYY-MM-DD)')
        
        fecha_preñez = None
        if datos.get('fecha_preñez'):
            try:
                if isinstance(datos['fecha_preñez'], str):
                    fecha_preñez = datetime.strptime(datos['fecha_preñez'], '%Y-%m-%d').date()
                else:
                    fecha_preñez = datos['fecha_preñez']
            except (ValueError, TypeError):
                errores.append('Formato de fecha de preñez inválido (YYYY-MM-DD)')
        
        # Validar fechas en conjunto
        if not errores:  # Solo si no hay errores de formato
            es_valido, mensaje = Animal.validar_fechas(fecha_nacimiento, ultimo_parto, ultimo_aborto, fecha_preñez)
            if not es_valido:
                errores.append(mensaje)
        
        # Validar lógica de preñez
        if datos.get('sexo') == 'Macho':
            if datos.get('preñada') or datos.get('fecha_preñez') or datos.get('numero_partos') or datos.get('ultimo_parto'):
                errores.append('Los machos no pueden tener datos reproductivos')
        
        # Validar campos de texto
        campos_texto = ['raza', 'preñada_por']
        for campo in campos_texto:
            if datos.get(campo):
                valor = str(datos[campo]).strip()
                if len(valor) > 50:
                    errores.append(f'{campo.replace("_", " ").capitalize()} no puede exceder 50 caracteres')
        
        return errores
    
    @staticmethod
    def crear_animal(datos, usuario_id):
        """Crea un nuevo animal"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden crear animales',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Validar que la hacienda existe
            hacienda_id = datos.get('idhacienda')
            if not hacienda_id:
                return {
                    'error': 'ID de hacienda es requerido',
                    'status': 'error',
                    'code': 'MISSING_HACIENDA'
                }, 400
            
            hacienda = Hacienda.query.get(hacienda_id)
            if not hacienda:
                return {
                    'error': 'Hacienda no encontrada',
                    'status': 'error',
                    'code': 'HACIENDA_NOT_FOUND'
                }, 404
            
            # Validar que el estado existe
            estado_id = datos.get('idestado', 1)  # Por defecto 'Activo'
            estado = EstadoAnimal.query.get(estado_id)
            if not estado:
                return {
                    'error': 'Estado de animal no válido',
                    'status': 'error',
                    'code': 'INVALID_STATE'
                }, 400
            
            # Validar datos
            errores = AnimalService.validar_datos_animal(datos, True, hacienda_id)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Crear el animal
            animal = Animal(
                idhacienda=hacienda_id,
                idestado=estado_id,
                hierro=str(datos['hierro']).strip(),
                sexo=datos['sexo'],
                raza=str(datos.get('raza', '')).strip() or None,
                peso_actual=float(datos['peso_actual']) if datos.get('peso_actual') else None,
                numero_partos=int(datos.get('numero_partos', 0)),
                preñada=bool(datos.get('preñada', False)) if datos['sexo'] == 'Hembra' else False,
                preñada_por=str(datos.get('preñada_por', '')).strip() or None,
                observaciones=str(datos.get('observaciones', '')).strip() or None
            )
            
            # Manejar fechas
            if datos.get('fecha_nacimiento'):
                if isinstance(datos['fecha_nacimiento'], str):
                    animal.fecha_nacimiento = datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d').date()
                else:
                    animal.fecha_nacimiento = datos['fecha_nacimiento']
            
            if datos.get('ultimo_parto') and datos['sexo'] == 'Hembra':
                if isinstance(datos['ultimo_parto'], str):
                    animal.ultimo_parto = datetime.strptime(datos['ultimo_parto'], '%Y-%m-%d').date()
                else:
                    animal.ultimo_parto = datos['ultimo_parto']
            
            if datos.get('ultimo_aborto') and datos['sexo'] == 'Hembra':
                if isinstance(datos['ultimo_aborto'], str):
                    animal.ultimo_aborto = datetime.strptime(datos['ultimo_aborto'], '%Y-%m-%d').date()
                else:
                    animal.ultimo_aborto = datos['ultimo_aborto']
            
            if datos.get('fecha_preñez') and datos['sexo'] == 'Hembra':
                if isinstance(datos['fecha_preñez'], str):
                    animal.fecha_preñez = datetime.strptime(datos['fecha_preñez'], '%Y-%m-%d').date()
                else:
                    animal.fecha_preñez = datos['fecha_preñez']
            
            db.session.add(animal)
            db.session.commit()
            
            return {
                'message': f'Animal "{animal.hierro}" creado exitosamente',
                'status': 'success',
                'animal': animal.to_dict(),
                'creado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al crear animal: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_animal(animal_id):
        """Obtiene un animal por ID"""
        try:
            animal = Animal.query.get(animal_id)
            
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            return {
                'animal': animal.to_dict(),
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener animal: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def listar_animales(filtros=None, pagina=1, por_pagina=50):
        """Lista animales con filtros y paginación"""
        try:
            query = Animal.query.join(Hacienda).join(EstadoAnimal)
            
            # Aplicar filtros
            if filtros:
                if filtros.get('hacienda_id'):
                    query = query.filter(Animal.idhacienda == filtros['hacienda_id'])
                
                if filtros.get('estado_id'):
                    query = query.filter(Animal.idestado == filtros['estado_id'])
                
                if filtros.get('sexo'):
                    query = query.filter(Animal.sexo == filtros['sexo'])
                
                if filtros.get('raza'):
                    query = query.filter(Animal.raza.ilike(f"%{filtros['raza']}%"))
                
                if filtros.get('preñada') is not None:
                    query = query.filter(Animal.preñada == filtros['preñada'])
                
                if filtros.get('buscar'):
                    termino = filtros['buscar']
                    query = query.filter(
                        db.or_(
                            Animal.hierro.ilike(f'%{termino}%'),
                            Animal.raza.ilike(f'%{termino}%'),
                            Hacienda.nombre.ilike(f'%{termino}%')
                        )
                    )
            
            # Ordenar por hacienda y hierro
            query = query.order_by(Hacienda.nombre, Animal.hierro)
            
            # Paginación
            animales_paginados = query.paginate(
                page=pagina,
                per_page=por_pagina,
                error_out=False
            )
            
            return {
                'animales': [a.to_dict() for a in animales_paginados.items],
                'total': animales_paginados.total,
                'pagina_actual': pagina,
                'total_paginas': animales_paginados.pages,
                'por_pagina': por_pagina,
                'tiene_siguiente': animales_paginados.has_next,
                'tiene_anterior': animales_paginados.has_prev,
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al listar animales: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def actualizar_animal(animal_id, datos, usuario_id):
        """Actualiza un animal existente"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden actualizar animales',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar el animal
            animal = Animal.query.get(animal_id)
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Validar datos
            validar_hierro_unico = datos.get('hierro') and datos['hierro'].strip() != animal.hierro
            errores = AnimalService.validar_datos_animal(datos, validar_hierro_unico, animal.idhacienda, animal_id)
            if errores:
                return {
                    'error': 'Errores de validación',
                    'status': 'error',
                    'code': 'VALIDATION_ERROR',
                    'details': errores
                }, 400
            
            # Actualizar campos
            campos_actualizables = [
                'hierro', 'sexo', 'raza', 'peso_actual', 'numero_partos',
                'preñada', 'preñada_por', 'observaciones', 'idestado'
            ]
            
            actualizado = False
            for campo in campos_actualizables:
                if campo in datos:
                    if campo == 'peso_actual':
                        if datos[campo] is not None:
                            setattr(animal, campo, float(datos[campo]))
                        else:
                            setattr(animal, campo, None)
                    elif campo == 'numero_partos':
                        if datos[campo] is not None:
                            setattr(animal, campo, int(datos[campo]))
                        else:
                            setattr(animal, campo, 0)
                    elif campo == 'preñada':
                        # Solo permitir si es hembra
                        if animal.sexo == 'Hembra':
                            setattr(animal, campo, bool(datos[campo]))
                        else:
                            setattr(animal, campo, False)
                    else:
                        valor = str(datos[campo]).strip() if datos[campo] else None
                        setattr(animal, campo, valor)
                    actualizado = True
            
            # Manejar fechas
            fechas = ['fecha_nacimiento', 'ultimo_parto', 'ultimo_aborto', 'fecha_preñez']
            for fecha_campo in fechas:
                if fecha_campo in datos:
                    if datos[fecha_campo]:
                        try:
                            if isinstance(datos[fecha_campo], str):
                                fecha = datetime.strptime(datos[fecha_campo], '%Y-%m-%d').date()
                            else:
                                fecha = datos[fecha_campo]
                            setattr(animal, fecha_campo, fecha)
                        except (ValueError, TypeError):
                            continue
                    else:
                        setattr(animal, fecha_campo, None)
                    actualizado = True
            
            if actualizado:
                db.session.commit()
            
            return {
                'message': f'Animal "{animal.hierro}" actualizado exitosamente',
                'status': 'success',
                'animal': animal.to_dict(),
                'actualizado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al actualizar animal: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def cambiar_estado_animal(animal_id, estado_id, usuario_id):
        """Cambia el estado de un animal"""
        try:
            # Verificar permisos del usuario
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not (usuario.es_administrador() or usuario.es_instructor()):
                return {
                    'error': 'Solo administradores e instructores pueden cambiar estado de animales',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar el animal
            animal = Animal.query.get(animal_id)
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            # Verificar que el estado existe
            estado = EstadoAnimal.query.get(estado_id)
            if not estado:
                return {
                    'error': 'Estado no válido',
                    'status': 'error',
                    'code': 'INVALID_STATE'
                }, 400
            
            # Cambiar estado
            animal.idestado = estado_id
            db.session.commit()
            
            return {
                'message': f'Estado del animal "{animal.hierro}" cambiado a "{estado.nombre_estado}"',
                'status': 'success',
                'animal': animal.to_dict(),
                'cambiado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al cambiar estado del animal: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def eliminar_animal(animal_id, usuario_id):
        """Elimina un animal"""
        try:
            # Verificar permisos del usuario (solo administradores)
            usuario = Usuario.query.get(usuario_id)
            if not usuario or not usuario.es_administrador():
                return {
                    'error': 'Solo administradores pueden eliminar animales',
                    'status': 'error',
                    'code': 'ACCESS_DENIED'
                }, 403
            
            # Buscar el animal
            animal = Animal.query.get(animal_id)
            if not animal:
                return {
                    'error': 'Animal no encontrado',
                    'status': 'error',
                    'code': 'NOT_FOUND'
                }, 404
            
            hierro_animal = animal.hierro
            db.session.delete(animal)
            db.session.commit()
            
            return {
                'message': f'Animal "{hierro_animal}" eliminado exitosamente',
                'status': 'success',
                'eliminado_por': f'{usuario.nombres} {usuario.apellidos}'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {
                'error': f'Error al eliminar animal: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500
    
    @staticmethod
    def obtener_estadisticas_animales(hacienda_id=None):
        """Obtiene estadísticas de animales"""
        try:
            if hacienda_id:
                # Estadísticas de una hacienda específica
                estadisticas = Animal.obtener_estadisticas_hacienda(hacienda_id)
            else:
                # Estadísticas globales
                total = Animal.query.count()
                
                # Por sexo
                machos = Animal.query.filter_by(sexo='Macho').count()
                hembras = Animal.query.filter_by(sexo='Hembra').count()
                
                # Por estado
                por_estado = db.session.query(
                    EstadoAnimal.nombre_estado,
                    db.func.count(Animal.idanimal).label('cantidad')
                ).join(Animal).group_by(EstadoAnimal.nombre_estado).all()
                
                # Hembras preñadas
                preñadas = Animal.query.filter_by(sexo='Hembra', preñada=True).count()
                
                # Por hacienda
                por_hacienda = db.session.query(
                    Hacienda.nombre,
                    db.func.count(Animal.idanimal).label('cantidad')
                ).join(Animal).group_by(Hacienda.nombre).all()
                
                estadisticas = {
                    'total_animales': total,
                    'machos': machos,
                    'hembras': hembras,
                    'preñadas': preñadas,
                    'por_estado': [
                        {'estado': estado, 'cantidad': cantidad}
                        for estado, cantidad in por_estado
                    ],
                    'por_hacienda': [
                        {'hacienda': hacienda, 'cantidad': cantidad}
                        for hacienda, cantidad in por_hacienda
                    ]
                }
            
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
    def buscar_animales(termino, hacienda_id=None):
        """Búsqueda general de animales"""
        try:
            if not termino or len(termino.strip()) < 2:
                return {
                    'error': 'El término de búsqueda debe tener al menos 2 caracteres',
                    'status': 'error',
                    'code': 'INVALID_SEARCH_TERM'
                }, 400
            
            animales = Animal.buscar_general(termino.strip(), hacienda_id)
            
            return {
                'animales': [a.to_dict() for a in animales],
                'total': len(animales),
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
    def obtener_estados_animal():
        """Obtiene todos los estados de animal disponibles"""
        try:
            estados = EstadoAnimal.query.all()
            
            return {
                'estados': [estado.to_dict() for estado in estados],
                'status': 'success'
            }, 200
            
        except Exception as e:
            return {
                'error': f'Error al obtener estados: {str(e)}',
                'status': 'error',
                'code': 'INTERNAL_ERROR'
            }, 500