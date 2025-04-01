#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo que contiene el controlador para operaciones Git.
Implementa la lógica de negocio para interactuar con repositorios Git.
"""

import os
from typing import List, Dict, Any, Optional, Callable, Tuple

from src.models.git_repository import GitRepository
from src.utils.common import format_git_url, validate_folder_path, get_default_branch_name


class GitController:
    """
    Controlador para operaciones Git.
    Implementa la lógica de negocio para interactuar con repositorios Git.
    """

    def __init__(self):
        """
        Constructor del controlador Git.
        Inicializa las propiedades del controlador.
        """
        self.repository = None
        self.folder_path = None
    
    def set_folder_path(self, folder_path: str) -> Tuple[bool, str]:
        """
        Establece la ruta de la carpeta local y crea el repositorio.
        
        Args:
            folder_path (str): Ruta de la carpeta local.
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not validate_folder_path(folder_path):
            return False, f"La carpeta '{folder_path}' no existe o no es accesible."
        
        self.folder_path = folder_path
        self.repository = GitRepository(folder_path)
        
        if self.repository.is_git_repo:
            return True, f"La carpeta '{folder_path}' ya es un repositorio Git."
        else:
            return True, f"Carpeta '{folder_path}' seleccionada correctamente."
    
    def get_new_repository_workflow(self, repo_url: str, commit_message: str) -> List[Dict[str, Any]]:
        """
        Obtiene el flujo de trabajo para un nuevo repositorio.
        
        Args:
            repo_url (str): URL del repositorio remoto.
            commit_message (str): Mensaje para el commit inicial.
            
        Returns:
            List[Dict[str, Any]]: Lista de pasos del flujo de trabajo.
        """
        # Formatear la URL del repositorio
        formatted_url = format_git_url(repo_url)
        
        # Obtener el nombre de la rama predeterminada
        branch_name = get_default_branch_name()
        
        # Definir el flujo de trabajo
        workflow = [
            {
                'name': 'Inicializar repositorio Git',
                'function': self.repository.init_repository,
                'args': [],
                'kwargs': {}
            },
            {
                'name': 'Crear archivo .gitignore',
                'function': self.repository.create_gitignore,
                'args': [],
                'kwargs': {'template': 'Python'}
            },
            {
                'name': 'Añadir archivos al área de preparación',
                'function': self.repository.add_all_files,
                'args': [],
                'kwargs': {}
            },
            {
                'name': 'Realizar commit inicial',
                'function': self.repository.commit,
                'args': [commit_message],
                'kwargs': {}
            },
            {
                'name': 'Añadir repositorio remoto',
                'function': self.repository.add_remote,
                'args': [formatted_url],
                'kwargs': {'remote_name': 'origin'}
            },
            {
                'name': 'Enviar cambios al repositorio remoto',
                'function': self.repository.push,
                'args': [],
                'kwargs': {'remote_name': 'origin', 'branch': branch_name}
            }
        ]
        
        return workflow
    
    def get_existing_repository_workflow(self, repo_url: str, overwrite_remote: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene el flujo de trabajo para un repositorio existente.
        
        Args:
            repo_url (str): URL del repositorio remoto.
            overwrite_remote (bool): Si es True, sobrescribe el contenido remoto con el local.
            
        Returns:
            List[Dict[str, Any]]: Lista de pasos del flujo de trabajo.
        """
        # Formatear la URL del repositorio
        formatted_url = format_git_url(repo_url)
        
        # Obtener el nombre de la rama predeterminada
        branch_name = get_default_branch_name()
        
        # Definir el flujo de trabajo básico (inicialización y configuración remota)
        workflow = [
            {
                'name': 'Inicializar repositorio Git',
                'function': self.repository.init_repository,
                'args': [],
                'kwargs': {}
            },
            {
                'name': 'Añadir repositorio remoto',
                'function': self.repository.add_remote,
                'args': [formatted_url],
                'kwargs': {'remote_name': 'origin'}
            },
            {
                'name': 'Verificar contenido del repositorio remoto',
                'function': self.repository.check_remote_content,
                'args': [],
                'kwargs': {'remote_name': 'origin'}
            }
        ]
        
        # Si el usuario eligió sobrescribir el contenido remoto, añadir pasos para push
        if overwrite_remote:
            # Verificar si hay cambios en el repositorio antes de intentar hacer commit
            workflow.append({
                'name': 'Verificar cambios en el repositorio',
                'function': self.repository.has_any_changes,
                'args': [],
                'kwargs': {}
            })
            
            # Añadir pasos para sobrescribir el contenido remoto
            workflow.extend([
                {
                    'name': 'Añadir archivos al área de preparación',
                    'function': self.repository.add_all_files,
                    'args': [],
                    'kwargs': {}
                },
                {
                    'name': 'Realizar commit inicial',
                    'function': self.repository.commit,
                    'args': ['Commit inicial para sobrescribir contenido remoto'],
                    'kwargs': {}
                },
                {
                    'name': 'Enviar cambios al repositorio remoto (forzado)',
                    'function': self.repository.push,
                    'args': [],
                    'kwargs': {'remote_name': 'origin', 'branch': branch_name, 'force': True}
                }
            ])
        else:
            # Añadir paso para obtener cambios del repositorio remoto
            workflow.append({
                'name': 'Obtener cambios del repositorio remoto',
                'function': self.repository.pull,
                'args': [],
                'kwargs': {'remote_name': 'origin', 'branch': branch_name}
            })
        
        return workflow
    
    def execute_workflow(self, workflow: List[Dict[str, Any]], progress_callback: Optional[Callable[[int, str], None]] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta un flujo de trabajo.
        
        Args:
            workflow (List[Dict[str, Any]]): Lista de pasos del flujo de trabajo.
            progress_callback (Optional[Callable[[int, str], None]]): Función de callback para informar del progreso.
            
        Returns:
            List[Dict[str, Any]]: Resultados de la ejecución del flujo de trabajo.
        """
        if not self.repository:
            raise ValueError("No se ha seleccionado una carpeta válida.")
        
        results = []
        total_steps = len(workflow)
        
        for i, step in enumerate(workflow):
            # Calcular el progreso
            progress = int((i / total_steps) * 100)
            
            # Informar del progreso
            if progress_callback:
                progress_callback(progress, f"Ejecutando: {step['name']}...")
            
            # Ejecutar la función
            try:
                # Informar del inicio de la operación con más detalle
                if progress_callback:
                    progress_callback(progress, f"📋 Iniciando: {step['name']}...")
                
                # Manejar específicamente funciones que devuelven 3 valores
                if step['name'] == 'Verificar contenido del repositorio remoto':
                    success, message, remote_info = step['function'](*step['args'], **step['kwargs'])
                    # Guardar el resultado con la información adicional
                    results.append({
                        'name': step['name'],
                        'success': success,
                        'message': message,
                        'remote_info': remote_info
                    })
                elif step['name'] == 'Verificar cambios en el repositorio':
                    success, message, has_changes = step['function'](*step['args'], **step['kwargs'])
                    # Guardar el resultado con la información de cambios
                    results.append({
                        'name': step['name'],
                        'success': True,  # Siempre marcamos como éxito, ya que es solo informativo
                        'message': message,
                        'has_changes': has_changes
                    })
                    
                    # Si no hay cambios, mostrar un mensaje informativo y ajustar el flujo de trabajo
                    if not has_changes:
                        if progress_callback:
                            progress_callback(progress, f"ℹ️ {message} El repositorio está sincronizado con el remoto.")
                            
                        # Buscar y saltar los pasos de commit y push si no hay cambios
                        next_steps_to_skip = []
                        for j in range(i + 1, len(workflow)):
                            if workflow[j]['name'] in ['Realizar commit inicial', 'Añadir archivos al área de preparación']:
                                next_steps_to_skip.append(j)
                                # Añadir un resultado informativo para estos pasos saltados
                                results.append({
                                    'name': workflow[j]['name'],
                                    'success': True,  # Marcamos como éxito para no interrumpir el flujo
                                    'message': "Paso omitido: No hay cambios para procesar.",
                                    'skipped': True
                                })
                                
                                if progress_callback:
                                    progress_callback(progress, f"ℹ️ {workflow[j]['name']} omitido: No hay cambios para procesar.")
                        
                        # Si hay pasos para saltar, ajustar el índice para continuar con el siguiente paso relevante
                        if next_steps_to_skip:
                            i = max(next_steps_to_skip)  # Saltar al último paso que debemos omitir
                            continue  # Continuar con el siguiente paso después del salto
                else:
                    success, message = step['function'](*step['args'], **step['kwargs'])
                    # Guardar el resultado estándar
                    results.append({
                        'name': step['name'],
                        'success': success,
                        'message': message
                    })
                
                # Informar del resultado con formato mejorado
                if progress_callback:
                    if success:
                        status = "✅ completado"
                        # Mostrar detalles del mensaje en líneas separadas para mejor legibilidad
                        progress_callback(progress, f"{step['name']} {status}")
                        if message:
                            for line in message.split('\n'):
                                if line.strip():
                                    progress_callback(progress, f"  └─ {line.strip()}")
                    else:
                        status = "❌ fallido"
                        progress_callback(progress, f"{step['name']} {status}: {message}")
                        # Si hay un mensaje de error detallado, mostrarlo línea por línea
                        if '\n' in message:
                            for line in message.split('\n'):
                                if line.strip():
                                    progress_callback(progress, f"  ❌ {line.strip()}")
                
                # Si hay un error, detener el flujo de trabajo
                if not success:
                    break
            except Exception as e:
                # Guardar el error
                results.append({
                    'name': step['name'],
                    'success': False,
                    'message': f"Error: {str(e)}"
                })
                
                # Informar del error
                if progress_callback:
                    progress_callback(progress, f"{step['name']} fallido: {str(e)}")
                
                # Detener el flujo de trabajo
                break
        
        # Informar de la finalización
        if progress_callback:
            progress_callback(100, "Proceso completado.")
        
        return results