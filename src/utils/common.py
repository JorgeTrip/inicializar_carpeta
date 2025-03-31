#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de utilidades comunes para la aplicación.
Contiene funciones y clases de utilidad que pueden ser usadas en diferentes partes del proyecto.
"""

import os
import sys
import platform
import subprocess
from typing import Optional, List, Dict, Any


def is_git_installed() -> bool:
    """
    Verifica si Git está instalado en el sistema.
    
    Returns:
        bool: True si Git está instalado, False en caso contrario.
    """
    try:
        # Configurar para ocultar la ventana de comandos en Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
        # Ejecutar el comando 'git --version' para verificar si Git está instalado
        subprocess.run(
            ['git', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            startupinfo=startupinfo
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_system_info() -> Dict[str, str]:
    """
    Obtiene información del sistema operativo.
    
    Returns:
        Dict[str, str]: Diccionario con información del sistema.
    """
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor()
    }


def validate_folder_path(folder_path: str) -> bool:
    """
    Valida si una ruta de carpeta existe y es accesible.
    
    Args:
        folder_path (str): Ruta de la carpeta a validar.
        
    Returns:
        bool: True si la carpeta existe y es accesible, False en caso contrario.
    """
    return os.path.exists(folder_path) and os.path.isdir(folder_path)


def format_git_url(url: str) -> str:
    """
    Formatea una URL de GitHub para asegurar que sea válida.
    
    Args:
        url (str): URL del repositorio de GitHub.
        
    Returns:
        str: URL formateada.
    """
    # Eliminar espacios en blanco
    url = url.strip()
    
    # Asegurar que la URL termina con .git
    if not url.endswith('.git') and not url.endswith('/'):
        url += '.git'
    elif url.endswith('/') and not url.endswith('.git'):
        url = url[:-1] + '.git'
    
    # Asegurar que la URL comienza con https:// o git@
    if not (url.startswith('https://') or url.startswith('git@')):
        if '@' in url and ':' in url:
            # Parece ser una URL SSH sin el prefijo git@
            url = 'git@' + url
        else:
            # Asumir que es una URL HTTPS sin el prefijo
            url = 'https://' + url
    
    return url


def get_default_branch_name() -> str:
    """
    Obtiene el nombre de la rama predeterminada configurada en Git.
    
    Returns:
        str: Nombre de la rama predeterminada (por defecto 'main').
    """
    try:
        # Configurar para ocultar la ventana de comandos en Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
        # Intentar obtener la rama predeterminada configurada en Git
        result = subprocess.run(
            ['git', 'config', '--get', 'init.defaultBranch'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            startupinfo=startupinfo
        )
        branch = result.stdout.strip()
        return branch if branch else 'main'
    except (subprocess.SubprocessError, FileNotFoundError):
        # Si no se puede obtener, devolver 'main' como valor predeterminado
        return 'main'


def get_git_username() -> str:
    """
    Obtiene el nombre de usuario configurado en Git.
    
    Returns:
        str: Nombre de usuario de Git o cadena vacía si no se encuentra.
    """
    try:
        # Configurar para ocultar la ventana de comandos en Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
        # Intentar obtener el nombre de usuario configurado en Git
        result = subprocess.run(
            ['git', 'config', '--get', 'user.name'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            startupinfo=startupinfo
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def build_github_url(folder_name: str, username: str = "") -> str:
    """
    Construye una URL de GitHub basada en el nombre de la carpeta y el nombre de usuario.
    
    Args:
        folder_name (str): Nombre de la carpeta/repositorio.
        username (str): Nombre de usuario de GitHub (opcional).
        
    Returns:
        str: URL del repositorio de GitHub.
    """
    # Obtener solo el nombre de la carpeta sin la ruta completa
    repo_name = os.path.basename(folder_name)
    
    # Construir la URL
    if username:
        return f"https://github.com/{username}/{repo_name}.git"
    else:
        return f"https://github.com/usuario/{repo_name}.git"