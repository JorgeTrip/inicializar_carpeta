#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo que contiene la clase GitRepository para gestionar operaciones con repositorios Git.
"""

import os
import subprocess
from typing import Tuple, List, Optional, Dict, Any


class GitRepository:
    """
    Clase que encapsula las operaciones con repositorios Git.
    Proporciona métodos para inicializar, vincular y gestionar repositorios Git.
    """

    def __init__(self, local_path: str):
        """
        Constructor de la clase GitRepository.
        
        Args:
            local_path (str): Ruta local de la carpeta que se vinculará con GitHub.
        """
        self.local_path = local_path
        self.is_git_repo = self._check_is_git_repo()
    
    def _check_is_git_repo(self) -> bool:
        """
        Verifica si la carpeta ya es un repositorio Git.
        
        Returns:
            bool: True si la carpeta ya es un repositorio Git, False en caso contrario.
        """
        git_dir = os.path.join(self.local_path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    def _run_git_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Ejecuta un comando Git y devuelve el resultado.
        
        Args:
            command (List[str]): Lista con el comando Git y sus argumentos.
            
        Returns:
            Tuple[bool, str]: Tupla con un booleano que indica si el comando se ejecutó correctamente
                             y un string con la salida o el error.
        """
        try:
            # Preparar el comando completo con 'git' al inicio
            full_command = ['git'] + command
            
            # Crear un string con el comando completo para el log
            cmd_str = ' '.join(full_command)
            
            # Ejecutar el comando en la carpeta del repositorio sin mostrar ventana de comandos
            startupinfo = None
            if os.name == 'nt':  # Solo en Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            
            result = subprocess.run(
                full_command,
                cwd=self.local_path,
                capture_output=True,
                text=True,
                check=True,
                startupinfo=startupinfo
            )
            
            # Formatear la salida para incluir el comando ejecutado
            output = f"Comando: {cmd_str}\n{result.stdout.strip()}"
            return True, output
        except subprocess.CalledProcessError as e:
            # Formatear el error para incluir el comando ejecutado
            cmd_str = ' '.join(['git'] + command)
            error = f"Error al ejecutar: {cmd_str}\n{e.stderr.strip()}"
            return False, error
        except Exception as e:
            cmd_str = ' '.join(['git'] + command)
            error = f"Excepción al ejecutar: {cmd_str}\n{str(e)}"
            return False, error
    
    def init_repository(self) -> Tuple[bool, str]:
        """
        Inicializa un nuevo repositorio Git en la carpeta local.
        
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if self.is_git_repo:
            return True, "La carpeta ya es un repositorio Git."
        
        success, message = self._run_git_command(['init'])
        if success:
            self.is_git_repo = True
            return True, "Repositorio Git inicializado correctamente."
        return False, f"Error al inicializar el repositorio: {message}"
    
    def add_remote(self, remote_url: str, remote_name: str = 'origin') -> Tuple[bool, str]:
        """
        Añade un repositorio remoto.
        
        Args:
            remote_url (str): URL del repositorio remoto en GitHub.
            remote_name (str): Nombre del remoto (por defecto 'origin').
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        # Verificar si ya existe el remoto
        success, remotes = self._run_git_command(['remote'])
        if success and remote_name in remotes.split():
            # Si existe, actualizar la URL
            return self._run_git_command(['remote', 'set-url', remote_name, remote_url])
        else:
            # Si no existe, añadirlo
            return self._run_git_command(['remote', 'add', remote_name, remote_url])
    
    def add_all_files(self) -> Tuple[bool, str]:
        """
        Añade todos los archivos al área de preparación (staging).
        
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        return self._run_git_command(['add', '.'])
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """
        Realiza un commit con los cambios en el área de preparación.
        
        Args:
            message (str): Mensaje del commit.
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        return self._run_git_command(['commit', '-m', message])
    
    def push(self, remote_name: str = 'origin', branch: str = 'main') -> Tuple[bool, str]:
        """
        Envía los cambios al repositorio remoto.
        
        Args:
            remote_name (str): Nombre del remoto (por defecto 'origin').
            branch (str): Nombre de la rama (por defecto 'main').
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        return self._run_git_command(['push', '-u', remote_name, branch])
    
    def diagnose_remote_ref_error(self, remote_name: str = 'origin', branch: str = 'main') -> Tuple[bool, str, Dict[str, Any]]:
        """
        Diagnostica el error "couldn't find remote ref" y proporciona información sobre posibles causas.
        
        Args:
            remote_name (str): Nombre del remoto a verificar.
            branch (str): Nombre de la rama a verificar.
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: Resultado del diagnóstico, mensaje y diccionario con información adicional.
        """
        diagnosis = {
            'possible_causes': [],
            'recommended_actions': [],
            'alternative_branch': None,
            'is_remote_empty': False,
            'remote_exists': False,
            'remote_url': None,
            'available_branches': []
        }
        
        # Verificar si el remoto existe
        success, remotes_output = self._run_git_command(['remote'])
        if not success or remote_name not in remotes_output.split():
            diagnosis['possible_causes'].append('El remoto especificado no existe')
            diagnosis['recommended_actions'].append(f'Añadir el remoto con: git remote add {remote_name} <url>')
            return False, f"El remoto '{remote_name}' no existe en este repositorio.", diagnosis
        
        diagnosis['remote_exists'] = True
        
        # Obtener la URL del remoto
        success, remote_url_output = self._run_git_command(['remote', 'get-url', remote_name])
        if success:
            diagnosis['remote_url'] = remote_url_output.strip().split('\n')[-1]
        
        # Verificar si hay conexión con el remoto
        success, ls_remote_output = self._run_git_command(['ls-remote', remote_name])
        if not success:
            diagnosis['possible_causes'].append('Problemas de conexión o autenticación con el repositorio remoto')
            diagnosis['recommended_actions'].append('Verificar credenciales de Git y conexión a internet')
            return False, "No se puede conectar al repositorio remoto. Verifica tus credenciales y conexión.", diagnosis
        
        # Verificar si el repositorio remoto está vacío
        if not ls_remote_output or ls_remote_output.strip() == "":
            diagnosis['is_remote_empty'] = True
            diagnosis['possible_causes'].append('El repositorio remoto está vacío')
            diagnosis['recommended_actions'].append(f'Inicializar el repositorio remoto o usar git push -u {remote_name} {branch}')
            return False, "El repositorio remoto parece estar vacío. No hay ramas para obtener.", diagnosis
        
        # Obtener las ramas disponibles en el remoto
        success, branches_output = self._run_git_command(['ls-remote', '--heads', remote_name])
        if success:
            # Extraer nombres de ramas del output (formato: hash refs/heads/nombre_rama)
            import re
            branches = re.findall(r'refs/heads/([^\s]+)', branches_output)
            diagnosis['available_branches'] = branches
            
            # Verificar si existe una rama alternativa (main/master)
            alternative_branch = 'master' if branch == 'main' else 'main'
            if alternative_branch in branches:
                diagnosis['alternative_branch'] = alternative_branch
                diagnosis['possible_causes'].append(f'La rama "{branch}" no existe, pero "{alternative_branch}" sí')
                diagnosis['recommended_actions'].append(f'Usar git pull {remote_name} {alternative_branch}')
            
            # Si la rama solicitada no está en la lista pero hay otras ramas disponibles
            if branch not in branches and branches:
                diagnosis['possible_causes'].append(f'La rama "{branch}" no existe en el remoto')
                branch_suggestions = ', '.join(branches[:3]) + (', ...' if len(branches) > 3 else '')
                diagnosis['recommended_actions'].append(f'Usar una de las ramas disponibles: {branch_suggestions}')
        
        # Si no se encontró ninguna causa específica
        if not diagnosis['possible_causes']:
            diagnosis['possible_causes'].append('Causa desconocida')
            diagnosis['recommended_actions'].append('Verificar la configuración de Git y el estado del repositorio remoto')
        
        return True, "Diagnóstico completado.", diagnosis
    
    def pull(self, remote_name: str = 'origin', branch: str = 'main') -> Tuple[bool, str]:
        """
        Obtiene los cambios del repositorio remoto.
        Implementa un diagnóstico avanzado cuando se encuentra el error "couldn't find remote ref".
        
        Args:
            remote_name (str): Nombre del remoto (por defecto 'origin').
            branch (str): Nombre de la rama (por defecto 'main').
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        # Intentar con la rama especificada
        success, message = self._run_git_command(['pull', remote_name, branch])
        
        # Si falla con un error de referencia no encontrada, realizar diagnóstico
        if not success and "couldn't find remote ref" in message:
            # Ejecutar diagnóstico para identificar el problema
            _, diagnosis_msg, diagnosis_info = self.diagnose_remote_ref_error(remote_name, branch)
            
            # Intentar estrategias de recuperación automática
            
            # 1. Si hay una rama alternativa disponible (main/master), intentar con ella
            if diagnosis_info['alternative_branch']:
                alternative_branch = diagnosis_info['alternative_branch']
                alt_success, alt_message = self._run_git_command(['pull', remote_name, alternative_branch])
                if alt_success:
                    return True, f"Se utilizó la rama alternativa '{alternative_branch}' en lugar de '{branch}'."
            
            # 2. Si el repositorio remoto está vacío, sugerir hacer push primero
            if diagnosis_info['is_remote_empty']:
                return False, "El repositorio remoto está vacío. Considera hacer un push inicial con tus cambios locales."
            
            # 3. Si hay otras ramas disponibles, sugerir usar una de ellas
            if diagnosis_info['available_branches'] and branch not in diagnosis_info['available_branches']:
                branches_str = ', '.join(diagnosis_info['available_branches'][:3])
                if len(diagnosis_info['available_branches']) > 3:
                    branches_str += ', ...'
                return False, f"La rama '{branch}' no existe en el remoto. Ramas disponibles: {branches_str}"
            
            # Si no se pudo recuperar automáticamente, devolver un mensaje detallado con el diagnóstico
            detailed_message = f"Error: No se pudo encontrar la referencia remota '{branch}'\n\n"
            detailed_message += "Diagnóstico:\n"
            for i, cause in enumerate(diagnosis_info['possible_causes'], 1):
                detailed_message += f"  {i}. {cause}\n"
            
            detailed_message += "\nAcciones recomendadas:\n"
            for i, action in enumerate(diagnosis_info['recommended_actions'], 1):
                detailed_message += f"  {i}. {action}\n"
            
            return False, detailed_message
        
        return success, message
    
    def get_status(self) -> Tuple[bool, str]:
        """
        Obtiene el estado actual del repositorio.
        
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje con el estado.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        return self._run_git_command(['status'])
    
    def create_gitignore(self, template: str = 'Python') -> Tuple[bool, str]:
        """
        Crea un archivo .gitignore basado en una plantilla.
        
        Args:
            template (str): Nombre de la plantilla (por defecto 'Python').
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        gitignore_path = os.path.join(self.local_path, '.gitignore')
        
        # Plantillas básicas de .gitignore
        templates = {
            'Python': """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Virtual environments
venv/
env/
.env/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log

# Local configuration
.env
""",
            'Node': """# Dependencies
node_modules/
npm-debug.log
yarn-error.log
yarn-debug.log

# Build
dist/
build/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
"""
        }
        
        if template not in templates:
            return False, f"Plantilla '{template}' no disponible. Opciones: {', '.join(templates.keys())}"
        
        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(templates[template])
            return True, f"Archivo .gitignore creado con plantilla '{template}'."
        except Exception as e:
            return False, f"Error al crear .gitignore: {str(e)}"