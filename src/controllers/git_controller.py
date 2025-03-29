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
    
    def get_existing_repository_workflow(self, repo_url: str) -> List[Dict[str, Any]]:
        """
        Obtiene el flujo de trabajo para un repositorio existente.
        
        Args:
            repo_url (str): URL del repositorio remoto.
            
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
                'name': 'Añadir repositorio remoto',
                'function': self.repository.add_remote,
                'args': [formatted_url],
                'kwargs': {'remote_name': 'origin'}
            },
            {
                'name': 'Obtener cambios del repositorio remoto',
                'function': self.repository.pull,
                'args': [],
                'kwargs': {'remote_name': 'origin', 'branch': branch_name}
            }
        ]
        
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
                success, message = step['function'](*step['args'], **step['kwargs'])
                
                # Guardar el resultado
                results.append({
                    'name': step['name'],
                    'success': success,
                    'message': message
                })
                
                # Informar del resultado
                if progress_callback:
                    status = "completado" if success else "fallido"
                    progress_callback(progress, f"{step['name']} {status}: {message}")
                
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