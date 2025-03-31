#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de utilidades para interactuar con GitHub CLI.
Contiene funciones para verificar la instalación, autenticación y obtener información del usuario.
"""

import subprocess
import os
from typing import Dict, Any, Tuple, Optional


def get_gh_cli_path() -> Optional[str]:
    """
    Obtiene la ruta completa del ejecutable de GitHub CLI.
    
    Returns:
        Optional[str]: Ruta completa del ejecutable o None si no se encuentra.
    """
    # Primero intentamos encontrarlo en el PATH
    try:
        # Configurar para ocultar la ventana de comandos en Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
        result = subprocess.run(
            ['where', 'gh'] if os.name == 'nt' else ['which', 'gh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            startupinfo=startupinfo
        )
        path = result.stdout.strip().split('\n')[0]
        if path and os.path.isfile(path):
            return path
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Si no está en el PATH, verificamos ubicaciones comunes de instalación
    common_locations = [
        os.path.join(os.environ.get('ProgramFiles', 'C:\Program Files'), 'GitHub CLI', 'gh.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\Program Files (x86)'), 'GitHub CLI', 'gh.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GitHub CLI', 'gh.exe')
    ]
    
    for location in common_locations:
        if os.path.isfile(location):
            return location
            
    return None


def is_gh_cli_installed() -> bool:
    """
    Verifica si GitHub CLI está instalado en el sistema.
    Comprueba tanto si el comando está disponible en el PATH como si está instalado en ubicaciones comunes.
    
    Returns:
        bool: True si GitHub CLI está instalado, False en caso contrario.
    """
    return get_gh_cli_path() is not None


def is_gh_authenticated() -> bool:
    """
    Verifica si el usuario está autenticado en GitHub CLI.
    
    Returns:
        bool: True si el usuario está autenticado, False en caso contrario.
    """
    if not is_gh_cli_installed():
        return False
    
    # Obtener la ruta del ejecutable de GitHub CLI
    gh_path = get_gh_cli_path()
    if not gh_path:
        return False
        
    try:
        # Configurar para ocultar la ventana de comandos en Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
        # Ejecutar el comando 'gh auth status' para verificar si el usuario está autenticado
        result = subprocess.run(
            [gh_path, 'auth', 'status'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo
        )
        # Si el comando se ejecuta correctamente y no hay errores, el usuario está autenticado
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def get_gh_user_info() -> Optional[Dict[str, Any]]:
    """
    Obtiene información del usuario autenticado en GitHub CLI.
    
    Returns:
        Optional[Dict[str, Any]]: Diccionario con información del usuario o None si no está autenticado.
    """
    if not is_gh_authenticated():
        return None
    
    # Obtener la ruta del ejecutable de GitHub CLI
    gh_path = get_gh_cli_path()
    if not gh_path:
        return None
        
    try:
        # Configurar para ocultar la ventana de comandos en Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
        # Ejecutar el comando 'gh api user' para obtener información del usuario
        result = subprocess.run(
            [gh_path, 'api', 'user'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            startupinfo=startupinfo
        )
        
        # Convertir la salida JSON a un diccionario
        import json
        user_info = json.loads(result.stdout)
        
        return {
            'username': user_info.get('login'),
            'name': user_info.get('name'),
            'email': user_info.get('email'),
            'avatar_url': user_info.get('avatar_url'),
            'html_url': user_info.get('html_url')
        }
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return None


def build_github_repo_url(username: str, repo_name: str) -> str:
    """
    Construye una URL de repositorio de GitHub a partir del nombre de usuario y el nombre del repositorio.
    
    Args:
        username (str): Nombre de usuario de GitHub.
        repo_name (str): Nombre del repositorio.
        
    Returns:
        str: URL del repositorio de GitHub.
    """
    return f"https://github.com/{username}/{repo_name}.git"


def extract_repo_name_from_path(folder_path: str) -> str:
    """
    Extrae el nombre del repositorio a partir de la ruta de la carpeta.
    
    Args:
        folder_path (str): Ruta de la carpeta.
        
    Returns:
        str: Nombre del repositorio.
    """
    import os
    return os.path.basename(folder_path)