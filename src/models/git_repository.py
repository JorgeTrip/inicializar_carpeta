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
    
    def check_git_config(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica si la configuración de usuario de Git está establecida.
        
        Returns:
            Tuple[bool, str, Dict[str, Any]]: Resultado de la verificación, mensaje y diccionario con información adicional.
        """
        config_info = {
            'user.name': None,
            'user.email': None,
            'is_configured': False
        }
        
        # Verificar user.name
        success, output = self._run_git_command(['config', '--get', 'user.name'])
        if success and output.strip() != "":
            config_info['user.name'] = output.replace("Comando: git config --get user.name\n", "").strip()
        
        # Verificar user.email
        success, output = self._run_git_command(['config', '--get', 'user.email'])
        if success and output.strip() != "":
            config_info['user.email'] = output.replace("Comando: git config --get user.email\n", "").strip()
        
        # Determinar si está configurado
        config_info['is_configured'] = config_info['user.name'] is not None and config_info['user.email'] is not None
        
        if config_info['is_configured']:
            return True, f"Configuración de Git: Usuario '{config_info['user.name']}' <{config_info['user.email']}>", config_info
        else:
            missing = []
            if config_info['user.name'] is None:
                missing.append("user.name")
            if config_info['user.email'] is None:
                missing.append("user.email")
            
            return False, f"Configuración de Git incompleta. Falta: {', '.join(missing)}", config_info
    
    def has_staged_changes(self) -> Tuple[bool, str, bool]:
        """
        Verifica si hay cambios en el área de preparación (staging) listos para commit.
        
        Returns:
            Tuple[bool, str, bool]: Resultado de la operación, mensaje y booleano que indica si hay cambios.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero.", False
        
        # Ejecutar git diff --cached para ver si hay cambios en staging
        success, output = self._run_git_command(['diff', '--cached', '--quiet'])
        
        # Si el comando falla, significa que hay cambios en staging
        has_changes = not success
        
        if has_changes:
            return True, "Hay cambios en el área de preparación listos para commit.", True
        else:
            return True, "No hay cambios en el área de preparación para hacer commit.", False
    
    def has_unstaged_changes(self) -> Tuple[bool, str, bool]:
        """
        Verifica si hay cambios sin preparar (unstaged) en el repositorio.
        
        Returns:
            Tuple[bool, str, bool]: Resultado de la operación, mensaje y booleano que indica si hay cambios.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero.", False
        
        # Ejecutar git diff para ver si hay cambios sin preparar
        success, output = self._run_git_command(['diff', '--quiet'])
        
        # Si el comando falla, significa que hay cambios sin preparar
        has_changes = not success
        
        if has_changes:
            return True, "Hay cambios sin preparar en el repositorio.", True
        else:
            return True, "No hay cambios sin preparar en el repositorio.", False
    
    def has_any_changes(self) -> Tuple[bool, str, bool]:
        """
        Verifica si hay cualquier tipo de cambio en el repositorio (staged o unstaged).
        
        Returns:
            Tuple[bool, str, bool]: Resultado de la operación, mensaje y booleano que indica si hay cambios.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero.", False
        
        # Verificar cambios preparados
        staged_success, staged_msg, has_staged = self.has_staged_changes()
        if not staged_success:
            return False, staged_msg, False
        
        # Verificar cambios sin preparar
        unstaged_success, unstaged_msg, has_unstaged = self.has_unstaged_changes()
        if not unstaged_success:
            return False, unstaged_msg, False
        
        # Verificar si hay archivos sin seguimiento
        success, output = self._run_git_command(['ls-files', '--others', '--exclude-standard', '--error-unmatch', '*'])
        has_untracked = success
        
        # Determinar si hay algún tipo de cambio
        has_any_changes = has_staged or has_unstaged or has_untracked
        
        if has_any_changes:
            message = "Hay cambios en el repositorio."
            if has_staged:
                message += " Hay cambios preparados."
            if has_unstaged:
                message += " Hay cambios sin preparar."
            if has_untracked:
                message += " Hay archivos sin seguimiento."
            return True, message, True
        else:
            return True, "No hay cambios en el repositorio.", False
    
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
        
        # Verificar si hay cambios para hacer commit
        success, status_msg, has_changes = self.has_staged_changes()
        if not success:
            return False, status_msg
        
        if not has_changes:
            # Si no hay cambios preparados, verificar si hay otros cambios sin preparar
            any_success, any_msg, has_any = self.has_any_changes()
            if any_success and has_any:
                return False, "No hay cambios preparados para hacer commit, pero hay cambios sin preparar. Usa 'git add .' para preparar todos los cambios."
            else:
                return False, "No hay cambios para hacer commit. El repositorio está sincronizado con el remoto."
        
        # Verificar si la configuración de usuario está establecida
        config_success, config_msg, config_info = self.check_git_config()
        if not config_success:
            return False, f"No se puede hacer commit: {config_msg}. Configura tu usuario de Git con 'git config --global user.name \"Tu Nombre\"' y 'git config --global user.email \"tu@email.com\"'."
        
        # Realizar el commit
        return self._run_git_command(['commit', '-m', message])
    
    def push(self, remote_name: str = 'origin', branch: str = 'main', force: bool = False) -> Tuple[bool, str]:
        """
        Envía los cambios al repositorio remoto.
        
        Args:
            remote_name (str): Nombre del remoto (por defecto 'origin').
            branch (str): Nombre de la rama (por defecto 'main').
            force (bool): Si es True, fuerza el push incluso si causa pérdida de commits remotos.
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        command = ['push', '-u']
        if force:
            command.append('--force')
        command.extend([remote_name, branch])
        
        return self._run_git_command(command)
    
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
            remote_url = remote_url_output.strip().split('\n')[-1]
            diagnosis['remote_url'] = remote_url
        
        # Intentar listar las ramas remotas
        success, ls_remote_output = self._run_git_command(['ls-remote', '--heads', remote_name])
        
        if not success:
            # Si falla, podría ser porque el repositorio remoto no existe o no es accesible
            diagnosis['possible_causes'].append('El repositorio remoto no existe o no es accesible')
            diagnosis['possible_causes'].append('Problemas de conectividad o autenticación')
            diagnosis['recommended_actions'].append('Verificar que el repositorio remoto existe y es accesible')
            diagnosis['recommended_actions'].append('Verificar credenciales de autenticación')
            return False, f"No se puede acceder al remoto '{remote_name}'. Verifica que existe y tienes acceso.", diagnosis
        
        # Si ls-remote no devuelve nada, el repositorio remoto está vacío
        if not ls_remote_output or ls_remote_output.strip() == f"Comando: git ls-remote --heads {remote_name}":
            diagnosis['is_remote_empty'] = True
            diagnosis['possible_causes'].append('El repositorio remoto está vacío')
            diagnosis['recommended_actions'].append(f'Hacer push con: git push -u {remote_name} {branch}')
            return True, f"El repositorio remoto '{remote_name}' está vacío. No hay ramas disponibles.", diagnosis
        
        # Extraer las ramas disponibles del output de ls-remote
        available_branches = []
        for line in ls_remote_output.split('\n'):
            if line.startswith('Comando:'):
                continue
            if 'refs/heads/' in line:
                branch_name = line.split('refs/heads/')[-1].strip()
                available_branches.append(branch_name)
        
        diagnosis['available_branches'] = available_branches
        
        # Si la rama especificada no está en las ramas disponibles
        if branch not in available_branches:
            diagnosis['possible_causes'].append(f"La rama '{branch}' no existe en el repositorio remoto")
            
            # Sugerir una rama alternativa si hay alguna disponible
            if available_branches:
                # Buscar 'main' o 'master' primero, luego cualquier otra
                if 'main' in available_branches:
                    diagnosis['alternative_branch'] = 'main'
                elif 'master' in available_branches:
                    diagnosis['alternative_branch'] = 'master'
                else:
                    diagnosis['alternative_branch'] = available_branches[0]
                
                diagnosis['recommended_actions'].append(f"Usar la rama '{diagnosis['alternative_branch']}' en lugar de '{branch}'")
                return False, f"La rama '{branch}' no existe en el remoto. Ramas disponibles: {', '.join(available_branches)}", diagnosis
            else:
                diagnosis['recommended_actions'].append('Crear la rama en el repositorio remoto')
                return False, f"No se encontraron ramas en el repositorio remoto '{remote_name}'.", diagnosis
        
        # Si llegamos aquí, la rama existe pero hay otro problema
        diagnosis['possible_causes'].append('Problema desconocido con la referencia remota')
        diagnosis['recommended_actions'].append('Verificar la configuración de Git y el estado del repositorio remoto')
        return False, f"La rama '{branch}' existe en el remoto, pero hay un problema al acceder a ella.", diagnosis
    
    def check_remote_content(self, remote_name: str = 'origin') -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica si el repositorio remoto tiene contenido y obtiene información sobre las ramas disponibles.
        
        Args:
            remote_name (str): Nombre del remoto a verificar.
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: Resultado de la verificación, mensaje y diccionario con información adicional.
        """
        result_info = {
            'has_content': False,
            'available_branches': [],
            'default_branch': None
        }
        
        # Verificar si el remoto existe
        success, remotes_output = self._run_git_command(['remote'])
        if not success or remote_name not in remotes_output.split():
            return False, f"El remoto '{remote_name}' no existe en este repositorio.", result_info
        
        # Intentar listar las ramas remotas
        success, ls_remote_output = self._run_git_command(['ls-remote', '--heads', remote_name])
        
        if not success:
            # Si falla, podría ser porque el repositorio remoto no existe o no es accesible
            return False, f"No se puede acceder al remoto '{remote_name}'. Verifica que existe y tienes acceso.", result_info
        
        # Si ls-remote no devuelve nada o solo devuelve el comando, el repositorio remoto está vacío
        if not ls_remote_output or ls_remote_output.strip() == f"Comando: git ls-remote --heads {remote_name}":
            return True, f"El repositorio remoto '{remote_name}' está vacío.", result_info
        
        # Extraer las ramas disponibles del output de ls-remote
        available_branches = []
        for line in ls_remote_output.split('\n'):
            if line.startswith('Comando:'):
                continue
            if 'refs/heads/' in line:
                branch_name = line.split('refs/heads/')[-1].strip()
                available_branches.append(branch_name)
        
        if available_branches:
            result_info['has_content'] = True
            result_info['available_branches'] = available_branches
            
            # Determinar la rama predeterminada (main o master)
            if 'main' in available_branches:
                result_info['default_branch'] = 'main'
            elif 'master' in available_branches:
                result_info['default_branch'] = 'master'
            else:
                result_info['default_branch'] = available_branches[0]
            
            return True, f"El repositorio remoto tiene contenido. Ramas disponibles: {', '.join(available_branches)}", result_info
        
        # Si llegamos aquí, el repositorio tiene algún contenido pero no pudimos determinar las ramas
        result_info['has_content'] = True
        return True, "El repositorio remoto tiene contenido, pero no se pudieron determinar las ramas.", result_info
    
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
            template (str): Nombre de la plantilla a utilizar (por defecto 'Python').
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        gitignore_path = os.path.join(self.local_path, '.gitignore')
        
        # Verificar si ya existe un archivo .gitignore
        if os.path.exists(gitignore_path):
            return True, "El archivo .gitignore ya existe."
        
        # Crear un archivo .gitignore básico para Python
        if template.lower() == 'python':
            gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/

# Local configuration
.idea/
.vscode/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
        else:
            # Si no se reconoce la plantilla, crear un .gitignore básico
            gitignore_content = """
# Archivos generados por el sistema operativo
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Archivos de configuración del IDE
.idea/
.vscode/
*.swp
*.swo
"""
        
        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            return True, f"Archivo .gitignore creado con plantilla '{template}'."
        except Exception as e:
            return False, f"Error al crear el archivo .gitignore: {str(e)}"
    
    def pull(self, remote_name: str = 'origin', branch: str = 'main') -> Tuple[bool, str]:
        """
        Obtiene los cambios del repositorio remoto.
        
        Args:
            remote_name (str): Nombre del remoto (por defecto 'origin').
            branch (str): Nombre de la rama (por defecto 'main').
            
        Returns:
            Tuple[bool, str]: Resultado de la operación y mensaje.
        """
        if not self.is_git_repo:
            return False, "La carpeta no es un repositorio Git. Inicialízalo primero."
        
        return self._run_git_command(['pull', remote_name, branch])