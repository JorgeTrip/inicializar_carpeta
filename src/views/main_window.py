#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo que contiene la ventana principal de la aplicación.
Implementa la interfaz gráfica para seleccionar carpetas y vincularlas con GitHub.
"""

import os
from typing import List, Dict, Any, Optional, Callable

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFileDialog, QRadioButton, QButtonGroup, 
    QGroupBox, QTextEdit, QProgressBar, QMessageBox, QApplication,
    QFrame, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QDir
from PyQt5.QtGui import QFont, QIcon

from src.controllers.git_controller import GitController
from src.utils.common import is_git_installed


class WorkerThread(QThread):
    """
    Clase para ejecutar operaciones en segundo plano.
    Evita que la interfaz se bloquee durante operaciones largas.
    """
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    
    def __init__(self, controller: GitController, workflow: List[Dict[str, Any]]):
        """
        Constructor de la clase WorkerThread.
        
        Args:
            controller (GitController): Controlador de Git.
            workflow (List[Dict[str, Any]]): Flujo de trabajo a ejecutar.
        """
        super().__init__()
        self.controller = controller
        self.workflow = workflow
    
    def run(self):
        """
        Método que se ejecuta en segundo plano.
        Ejecuta el flujo de trabajo y emite señales de progreso y finalización.
        """
        try:
            results = self.controller.execute_workflow(
                self.workflow, 
                progress_callback=lambda percent, message: self.progress_signal.emit(percent, message)
            )
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación.
    Proporciona una interfaz para seleccionar carpetas y vincularlas con GitHub.
    """

    def __init__(self, gh_cli_installed=False, gh_user_info=None):
        """
        Constructor de la ventana principal.
        Inicializa la interfaz gráfica.
        
        Args:
            gh_cli_installed (bool): Indica si GitHub CLI está instalado.
            gh_user_info (Optional[Dict[str, Any]]): Información del usuario de GitHub.
        """
        super().__init__()
        
        # Configurar la ventana principal
        self.setWindowTitle("Inicializador de Repositorios GitHub")
        self.setMinimumSize(800, 600)
        
        # Almacenar información de GitHub CLI
        self.gh_cli_installed = gh_cli_installed
        self.gh_user_info = gh_user_info
        
        # Crear el controlador de Git
        self.git_controller = GitController()
        
        # Inicializar la interfaz
        self._init_ui()
    
    def _init_ui(self):
        """
        Inicializa los componentes de la interfaz gráfica.
        """
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Título de la aplicación
        title_label = QLabel("Inicializador de Repositorios GitHub")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Descripción
        description_label = QLabel(
            "Esta aplicación te permite seleccionar una carpeta local y vincularla con un repositorio de GitHub."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Sección de selección de carpeta
        folder_group = QGroupBox("Selección de Carpeta")
        folder_layout = QVBoxLayout(folder_group)
        
        folder_description = QLabel(
            "Selecciona la carpeta local que deseas vincular con GitHub:"
        )
        folder_description.setWordWrap(True)
        folder_layout.addWidget(folder_description)
        
        folder_input_layout = QHBoxLayout()
        self.folder_path_input = QLineEdit()
        self.folder_path_input.setReadOnly(True)
        self.folder_path_input.setPlaceholderText("Ruta de la carpeta...")
        folder_input_layout.addWidget(self.folder_path_input)
        
        browse_button = QPushButton("Examinar...")
        browse_button.clicked.connect(self._browse_folder)
        folder_input_layout.addWidget(browse_button)
        folder_layout.addLayout(folder_input_layout)
        
        main_layout.addWidget(folder_group)
        
        # Sección de tipo de repositorio
        repo_type_group = QGroupBox("Tipo de Repositorio")
        repo_type_layout = QVBoxLayout(repo_type_group)
        
        repo_type_description = QLabel(
            "Selecciona si ya tienes un repositorio creado en GitHub o si deseas crear uno nuevo:"
        )
        repo_type_description.setWordWrap(True)
        repo_type_layout.addWidget(repo_type_description)
        
        self.repo_type_group = QButtonGroup(self)
        
        self.new_repo_radio = QRadioButton("Crear nuevo repositorio")
        self.new_repo_radio.setChecked(True)
        self.repo_type_group.addButton(self.new_repo_radio)
        repo_type_layout.addWidget(self.new_repo_radio)
        
        self.existing_repo_radio = QRadioButton("Vincular con repositorio existente")
        self.repo_type_group.addButton(self.existing_repo_radio)
        repo_type_layout.addWidget(self.existing_repo_radio)
        
        main_layout.addWidget(repo_type_group)
        
        # Sección de URL del repositorio
        url_group = QGroupBox("URL del Repositorio")
        url_layout = QVBoxLayout(url_group)
        
        # Mostrar información de GitHub CLI si está disponible
        if self.gh_cli_installed and self.gh_user_info and self.gh_user_info.get('username'):
            gh_info_layout = QHBoxLayout()
            
            gh_status_label = QLabel(f"✅ GitHub CLI: Autenticado como {self.gh_user_info.get('username')}")
            gh_status_label.setStyleSheet("color: green;")
            gh_info_layout.addWidget(gh_status_label)
            
            url_layout.addLayout(gh_info_layout)
        elif self.gh_cli_installed:
            gh_status_label = QLabel("⚠️ GitHub CLI: Instalado pero no autenticado")
            gh_status_label.setStyleSheet("color: orange;")
            url_layout.addWidget(gh_status_label)
        else:
            gh_status_label = QLabel("❌ GitHub CLI: No instalado")
            gh_status_label.setStyleSheet("color: red;")
            url_layout.addWidget(gh_status_label)
        
        url_description = QLabel(
            "Introduce la URL del repositorio de GitHub:"
        )
        url_description.setWordWrap(True)
        url_layout.addWidget(url_description)
        
        # Checkbox para permitir la edición manual de la URL del repositorio
        self.use_folder_name_checkbox = QCheckBox("Modificar manualmente (si el link es correcto, no cambiar nada)")
        self.use_folder_name_checkbox.setChecked(False)
        self.use_folder_name_checkbox.stateChanged.connect(self._update_repo_url)
        url_layout.addWidget(self.use_folder_name_checkbox)
        
        self.repo_url_input = QLineEdit()
        self.repo_url_input.setPlaceholderText("https://github.com/usuario/repositorio.git")
        url_layout.addWidget(self.repo_url_input)
        
        main_layout.addWidget(url_group)
        
        # Sección de mensaje de commit
        commit_group = QGroupBox("Mensaje de Commit")
        commit_layout = QVBoxLayout(commit_group)
        
        commit_description = QLabel(
            "Introduce un mensaje para el commit inicial:"
        )
        commit_description.setWordWrap(True)
        commit_layout.addWidget(commit_description)
        
        self.commit_message_input = QLineEdit("Commit inicial")
        commit_layout.addWidget(self.commit_message_input)
        
        main_layout.addWidget(commit_group)
        
        # Botón de iniciar proceso
        self.start_button = QPushButton("Iniciar Proceso")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self._start_process)
        main_layout.addWidget(self.start_button)
        
        # Botón de salir
        self.exit_button = QPushButton("Salir")
        self.exit_button.setMinimumHeight(40)
        self.exit_button.clicked.connect(self._exit_application)
        main_layout.addWidget(self.exit_button)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Área de log
        log_group = QGroupBox("Registro de Operaciones")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # Ajustar el tamaño de los widgets
        main_layout.setStretch(main_layout.indexOf(log_group), 1)
    
    def _browse_folder(self):
        """
        Abre un diálogo para seleccionar una carpeta.
        """
        # Asegurar que la aplicación procese eventos pendientes antes de mostrar el diálogo
        QApplication.processEvents()
        
        # Usar el diálogo nativo del sistema operativo para mejor compatibilidad
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
        
        dialog = QFileDialog(self)
        dialog.setOptions(options)
        dialog.setWindowTitle("Seleccionar Carpeta")
        dialog.setFileMode(QFileDialog.Directory)
        
        # Establecer directorio inicial para Windows (Este Equipo)
        if os.name == 'nt':
            dialog.setDirectory("::{20D04FE0-3AEA-1069-A2D8-08002B30309D}")
        else:
            dialog.setDirectory(QDir.homePath())
        
        if dialog.exec_():
            folder = dialog.selectedFiles()[0]
            if folder:
                self.folder_path_input.setText(folder)
                success, message = self.git_controller.set_folder_path(folder)
                self._log_message(message)
                self._update_repo_url()

    def _start_process(self):
        """
        Inicia el proceso de vinculación con GitHub.
        """
        # Validar que se haya seleccionado una carpeta
        folder_path = self.folder_path_input.text()
        if not folder_path:
            QMessageBox.warning(
                self,
                "Carpeta no seleccionada",
                "Por favor, selecciona una carpeta para continuar."
            )
            return
        
        # Obtener el mensaje de commit
        commit_message = self.commit_message_input.text()
        if not commit_message:
            commit_message = "Commit inicial"
        
        # Determinar el tipo de flujo de trabajo
        if self.new_repo_radio.isChecked():
            # Verificar si GitHub CLI está instalado y autenticado
            if not self.gh_cli_installed:
                QMessageBox.warning(
                    self,
                    "GitHub CLI no instalado",
                    "Para crear automáticamente un repositorio, necesitas instalar GitHub CLI. "
                    "Puedes descargarlo desde https://cli.github.com/"
                )
                return
            
            if not self.gh_user_info or not self.gh_user_info.get('username'):
                QMessageBox.warning(
                    self,
                    "No autenticado en GitHub",
                    "Para crear automáticamente un repositorio, necesitas autenticarte en GitHub CLI. "
                    "Reinicia la aplicación y sigue las instrucciones de autenticación."
                )
                return
            
            # Crear el repositorio automáticamente con GitHub CLI
            # Nota: El método _create_github_repository ahora inicializa el repositorio Git si es necesario
            repo_name = os.path.basename(folder_path)
            repo_url = self._create_github_repository(repo_name)
            
            if not repo_url:
                return  # Si hubo un error al crear el repositorio, detener el proceso
            
            # Actualizar el campo de URL con la URL del repositorio creado
            self.repo_url_input.setText(repo_url)
            
            # Obtener el flujo de trabajo para un nuevo repositorio
            # Como ya hemos inicializado el repositorio Git en _create_github_repository,
            # podemos ajustar el flujo de trabajo para evitar duplicar la inicialización
            workflow = self.git_controller.get_new_repository_workflow(repo_url, commit_message)
        else:
            # Validar que se haya introducido una URL para repositorios existentes
            repo_url = self.repo_url_input.text()
            if not repo_url:
                QMessageBox.warning(
                    self,
                    "URL no especificada",
                    "Por favor, introduce la URL del repositorio de GitHub."
                )
                return
            
            # Mostrar instrucciones para vincular con un repositorio existente
            self._show_existing_repo_instructions()
            
            # Verificar si el repositorio remoto tiene contenido antes de continuar
            # Primero inicializamos el repositorio y configuramos el remoto para poder verificar
            self._log_message("🔍 Verificando el contenido del repositorio remoto...")
            
            # Inicializar el repositorio Git si no está inicializado
            if not os.path.exists(os.path.join(folder_path, '.git')):
                self._log_message("🔄 Inicializando repositorio Git local...")
                success, message = self.git_controller.repository.init_repository()
                if not success:
                    self._log_message(f"❌ Error al inicializar el repositorio Git: {message}")
                    QMessageBox.critical(
                        self,
                        "Error al inicializar el repositorio",
                        f"No se pudo inicializar el repositorio Git. Error: {message}"
                    )
                    return
                self._log_message("✅ Repositorio Git local inicializado correctamente.")
            
            # Configurar el remoto
            self._log_message(f"🔄 Configurando remoto 'origin' con URL: {repo_url}")
            success, message = self.git_controller.repository.add_remote(repo_url)
            if not success:
                self._log_message(f"❌ Error al configurar el remoto: {message}")
                QMessageBox.critical(
                    self,
                    "Error al configurar el remoto",
                    f"No se pudo configurar el remoto. Error: {message}"
                )
                return
            self._log_message("✅ Remoto configurado correctamente.")
            
            # Verificar el contenido del repositorio remoto
            success, message, remote_info = self.git_controller.repository.check_remote_content()
            
            # Variable para controlar si debemos sobrescribir el contenido remoto
            overwrite_remote = False
            
            if success and remote_info['has_content']:
                # El repositorio remoto tiene contenido, preguntar al usuario qué hacer
                branches_str = ", ".join(remote_info['available_branches'][:3])
                if len(remote_info['available_branches']) > 3:
                    branches_str += ", ..."
                
                self._log_message(f"⚠️ El repositorio remoto tiene contenido. Ramas disponibles: {branches_str}")
                
                reply = QMessageBox.question(
                    self,
                    "Repositorio Remoto con Contenido",
                    f"El repositorio remoto ya tiene contenido. Ramas disponibles: {branches_str}\n\n"
                    "¿Deseas sobrescribir el contenido remoto con el contenido local?\n\n"
                    "- Si eliges 'Sí', se sobrescribirá el contenido remoto con el local.\n"
                    "- Si eliges 'No', se obtendrán los cambios del remoto y se mezclarán con el local.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                overwrite_remote = (reply == QMessageBox.Yes)
                
                if overwrite_remote:
                    self._log_message("⚠️ Se sobrescribirá el contenido remoto con el local.")
                else:
                    self._log_message("ℹ️ Se obtendrán los cambios del remoto y se mezclarán con el local.")
            elif success and remote_info['is_empty']:
                self._log_message("ℹ️ El repositorio remoto está vacío.")
                # Si el repositorio está vacío, podemos tratarlo como un nuevo repositorio
                overwrite_remote = True
            
            # Obtener el flujo de trabajo adecuado según la decisión del usuario
            workflow = self.git_controller.get_existing_repository_workflow(repo_url, overwrite_remote)
        
        # Determinar si debemos mostrar confirmación o proceder directamente
        # Si estamos creando un nuevo repositorio y ya se ha creado exitosamente, no necesitamos confirmación
        if self.new_repo_radio.isChecked() and repo_url:
            # Mostrar mensaje de éxito en lugar de confirmación
            QMessageBox.information(
                self,
                "Repositorio Creado",
                f"El repositorio '{os.path.basename(folder_path)}' ha sido creado exitosamente en GitHub.\n\nSe procederá a completar el proceso de vinculación."
            )
            proceed = True
        else:
            # Para vinculación manual, mostrar confirmación
            reply = QMessageBox.question(
                self,
                "Confirmar operación",
                "¿Deseas continuar con el proceso de vinculación?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            proceed = (reply == QMessageBox.Yes)
        
        if proceed:
            # Limpiar el log
            self.log_text.clear()
            self.progress_bar.setValue(0)
            
            # Deshabilitar controles durante el proceso
            self._set_controls_enabled(False)
            
            # Crear y ejecutar el hilo de trabajo
            self.worker_thread = WorkerThread(self.git_controller, workflow)
            self.worker_thread.progress_signal.connect(self._update_progress)
            self.worker_thread.finished_signal.connect(self._process_finished)
            self.worker_thread.error_signal.connect(self._process_error)
            self.worker_thread.start()
    
    def _create_github_repository(self, repo_name: str) -> str:
        """
        Crea un nuevo repositorio en GitHub usando GitHub CLI.
        Primero inicializa el repositorio Git local si es necesario.
        
        Args:
            repo_name (str): Nombre del repositorio a crear.
            
        Returns:
            str: URL del repositorio creado o cadena vacía si hubo un error.
        """
        from src.utils.github_cli import get_gh_cli_path
        import subprocess
        import json
        
        # Obtener la ruta del ejecutable de GitHub CLI
        gh_path = get_gh_cli_path()
        if not gh_path:
            self._log_message("❌ Error: No se pudo encontrar GitHub CLI.")
            return ""
        
        # Limpiar el nombre del repositorio (eliminar caracteres no válidos)
        import re
        clean_repo_name = re.sub(r'[^\w.-]', '-', repo_name)
        
        # Verificar si la carpeta ya es un repositorio Git
        folder_path = self.folder_path_input.text()
        if not os.path.exists(os.path.join(folder_path, '.git')):
            # Inicializar el repositorio Git local primero
            self._log_message("🔄 Inicializando repositorio Git local...")
            try:
                # Configurar para ocultar la ventana de comandos en Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                # Ejecutar el comando git init y capturar la salida en tiempo real
                self._log_message("📋 Ejecutando: git init")
                init_result = subprocess.run(
                    ['git', 'init'],
                    cwd=folder_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo
                )
                
                # Mostrar la salida del comando en el log
                if init_result.stdout:
                    for line in init_result.stdout.strip().split('\n'):
                        if line.strip():
                            self._log_message(f"  └─ {line.strip()}")
                
                if init_result.returncode != 0:
                    # Mostrar el error en el log
                    if init_result.stderr:
                        for line in init_result.stderr.strip().split('\n'):
                            if line.strip():
                                self._log_message(f"  ❌ {line.strip()}")
                    
                    self._log_message(f"❌ Error al inicializar el repositorio Git: {init_result.stderr}")
                    QMessageBox.critical(
                        self,
                        "Error al inicializar el repositorio",
                        f"No se pudo inicializar el repositorio Git. Error: {init_result.stderr}"
                    )
                    return ""
                self._log_message("✅ Repositorio Git local inicializado correctamente.")
            except Exception as e:
                self._log_message(f"❌ Error inesperado al inicializar el repositorio Git: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Error al inicializar el repositorio",
                    f"Se produjo un error inesperado al inicializar el repositorio Git: {str(e)}"
                )
                return ""
        
        # Mostrar mensaje en el log
        self._log_message(f"🔄 Creando repositorio '{clean_repo_name}' en GitHub...")
        
        try:
            # Configurar para ocultar la ventana de comandos en Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
            # Crear el repositorio con GitHub CLI
            # Usamos --private por defecto, pero se podría añadir una opción en la interfaz
            command = [gh_path, 'repo', 'create', clean_repo_name, '--private', '--source=.']
            self._log_message(f"📋 Ejecutando: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=folder_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo
            )
            
            # Mostrar la salida del comando en el log
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        self._log_message(f"  └─ {line.strip()}")
            
            # Verificar si el comando se ejecutó correctamente
            if result.returncode == 0:
                # Extraer la URL del repositorio de la salida de texto
                # La salida típica contiene algo como "Created repository username/repo-name on GitHub"
                # y posiblemente una URL en otra línea
                output_lines = result.stdout.strip().split('\n')
                repo_url = ""
                
                # Buscar una URL en la salida
                for line in output_lines:
                    # Buscar URLs de GitHub en la salida
                    if "github.com" in line:
                        # Extraer la URL usando expresiones regulares
                        import re
                        urls = re.findall(r'https?://github\.com/[\w.-]+/[\w.-]+', line)
                        if urls:
                            repo_url = urls[0]
                            break
                
                # Si no se encontró una URL, intentar construirla a partir del nombre del repositorio
                if not repo_url and self.gh_user_info and self.gh_user_info.get('username'):
                    username = self.gh_user_info.get('username')
                    repo_url = f"https://github.com/{username}/{clean_repo_name}"
                
                # Asegurar que la URL termina en .git
                if repo_url and not repo_url.endswith('.git'):
                    repo_url = repo_url + '.git'
                
                if repo_url:
                    self._log_message(f"✅ Repositorio creado correctamente: {repo_url}")
                    return repo_url
                else:
                    self._log_message(f"⚠️ No se pudo obtener la URL del repositorio. Salida: {result.stdout}")
                    return ""
            else:
                # Mostrar el error en el log de forma detallada
                self._log_message(f"❌ Error al crear el repositorio:")
                
                # Mostrar cada línea del error en el log
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            self._log_message(f"  ❌ {line.strip()}")
                
                # Mostrar un mensaje de error al usuario
                QMessageBox.critical(
                    self,
                    "Error al crear el repositorio",
                    f"No se pudo crear el repositorio en GitHub. Error: {result.stderr}"
                )
                return ""
        except Exception as e:
            # Capturar cualquier excepción
            error_msg = str(e)
            self._log_message(f"❌ Error inesperado al crear el repositorio: {error_msg}")
            
            # Mostrar un mensaje de error al usuario
            QMessageBox.critical(
                self,
                "Error al crear el repositorio",
                f"Se produjo un error inesperado al crear el repositorio: {error_msg}"
            )
            return ""
    
    def _show_existing_repo_instructions(self):
        """
        Muestra instrucciones para vincular con un repositorio existente en GitHub.
        """
        instructions = (
            "<h3>Instrucciones para vincular con un repositorio existente:</h3>"
            "<ol>"
            "<li>Asegúrate de que el repositorio ya existe en GitHub.</li>"
            "<li>Verifica que la URL del repositorio en el campo sea correcta (debe terminar en .git).</li>"
            "<li>Si necesitas modificar la URL, activa la casilla 'Modificar manualmente'.</li>"
            "</ol>"
            "<p>Ten en cuenta que si el repositorio no está vacío, es posible que necesites resolver conflictos manualmente.</p>"
            "<p>Al hacer clic en 'Iniciar Proceso', se vinculará la carpeta local con el repositorio existente.</p>"
        )
        
        # Registrar la acción en el log
        self._log_message("ℹ️ Vinculando con repositorio existente: " + self.repo_url_input.text())
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Vincular con Repositorio Existente")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(instructions)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    @pyqtSlot(int, str)
    def _update_progress(self, percent: int, message: str):
        """
        Actualiza la barra de progreso y el log.
        
        Args:
            percent (int): Porcentaje de progreso.
            message (str): Mensaje de progreso.
        """
        self.progress_bar.setValue(percent)
        self._log_message(message)
        QApplication.processEvents()  # Actualizar la interfaz
    
    @pyqtSlot(list)
    def _process_finished(self, results: List[Dict[str, Any]]):
        """
        Maneja la finalización del proceso.
        
        Args:
            results (List[Dict[str, Any]]): Resultados del proceso.
        """
        # Habilitar controles
        self._set_controls_enabled(True)
        
        # Mostrar resultados en el log
        self._log_message("\n--- Resultados del proceso ---")
        success_count = 0
        error_details = []
        
        for result in results:
            status = "✅ Éxito" if result['success'] else "❌ Error"
            self._log_message(f"{status}: {result['name']} - {result['message']}")
            
            if result['success']:
                success_count += 1
            else:
                error_details.append(result)
        
        # Mostrar mensaje final
        if success_count == len(results):
            self._log_message("\n✅ Proceso completado con éxito.")
            self._log_message("\n📋 Resumen:")
            self._log_message("  - Repositorio inicializado correctamente")
            self._log_message(f"  - URL del repositorio: {self.repo_url_input.text()}")
            self._log_message("  - Archivos añadidos y sincronizados con GitHub")
            
            QMessageBox.information(
                self,
                "Proceso Completado",
                "La carpeta ha sido vinculada con GitHub correctamente."
            )
        else:
            self._log_message(f"\n⚠️ Proceso completado con {len(results) - success_count} errores.")
            
            # Mostrar detalles de los errores y posibles soluciones
            self._log_message("\n🔍 Detalles de los errores:")
            for i, error in enumerate(error_details, 1):
                self._log_message(f"  {i}. Error en: {error['name']}")
                self._log_message(f"     Mensaje: {error['message']}")
                
                # Sugerir soluciones según el tipo de error
                if "remote" in error['name'].lower():
                    self._log_message("     Posible solución: Verifica que la URL del repositorio sea correcta y que tengas permisos de acceso.")
                elif "push" in error['name'].lower():
                    self._log_message("     Posible solución: Puede haber conflictos entre los archivos locales y remotos. Considera hacer un pull antes de push.")
                elif "commit" in error['name'].lower():
                    self._log_message("     Posible solución: Asegúrate de que hay cambios para hacer commit y que tu usuario de Git está configurado.")
                else:
                    self._log_message("     Posible solución: Revisa los mensajes de error y asegúrate de que Git está correctamente configurado.")
            
            self._log_message("\n💡 Recomendación: Si los errores persisten, considera ejecutar los comandos Git manualmente para obtener más detalles.")
            
            QMessageBox.warning(
                self,
                "Proceso Completado con Errores",
                f"El proceso ha finalizado con {len(results) - success_count} errores. Revisa el registro para más detalles y recomendaciones."
            )
    
    @pyqtSlot(str)
    def _process_error(self, error_message: str):
        """
        Maneja los errores durante el proceso.
        
        Args:
            error_message (str): Mensaje de error.
        """
        # Habilitar controles
        self._set_controls_enabled(True)
        
        # Mostrar error en el log con formato destacado
        self._log_message(f"\n❌ ERROR CRÍTICO: {error_message}")
        
        # Analizar el error y proporcionar sugerencias
        self._log_message("\n🔍 Análisis del error:")
        
        if "permission" in error_message.lower() or "acceso" in error_message.lower():
            self._log_message("  - Parece ser un problema de permisos.")
            self._log_message("  - Sugerencia: Verifica que tienes permisos de escritura en la carpeta seleccionada.")
            self._log_message("  - Sugerencia: Asegúrate de que tienes permisos en el repositorio de GitHub.")
        
        elif "network" in error_message.lower() or "red" in error_message.lower() or "conexión" in error_message.lower():
            self._log_message("  - Parece ser un problema de conexión a internet.")
            self._log_message("  - Sugerencia: Verifica tu conexión a internet.")
            self._log_message("  - Sugerencia: Comprueba si puedes acceder a GitHub desde tu navegador.")
        
        elif "authentication" in error_message.lower() or "autenticación" in error_message.lower():
            self._log_message("  - Parece ser un problema de autenticación con GitHub.")
            self._log_message("  - Sugerencia: Verifica tus credenciales de GitHub.")
            self._log_message("  - Sugerencia: Ejecuta 'gh auth login' en una terminal para reautenticarte.")
        
        elif "not found" in error_message.lower() or "no encontrado" in error_message.lower():
            self._log_message("  - Parece que no se encontró un recurso necesario.")
            self._log_message("  - Sugerencia: Verifica que la URL del repositorio sea correcta.")
            self._log_message("  - Sugerencia: Asegúrate de que el repositorio existe en GitHub.")
        
        else:
            self._log_message("  - Error no categorizado.")
            self._log_message("  - Sugerencia: Revisa la configuración de Git y GitHub CLI.")
            self._log_message("  - Sugerencia: Intenta ejecutar los comandos manualmente para obtener más detalles.")
        
        self._log_message("\n💡 Recomendación general: Si el problema persiste, considera reiniciar la aplicación o tu sistema.")
        
        # Mostrar mensaje de error
        QMessageBox.critical(
            self,
            "Error en el Proceso",
            f"Se ha producido un error durante el proceso: {error_message}\n\nRevisa el registro para ver sugerencias de solución."
        )
    
    def _set_controls_enabled(self, enabled: bool):
        """
        Habilita o deshabilita los controles de la interfaz.
        
        Args:
            enabled (bool): True para habilitar, False para deshabilitar.
        """
        self.folder_path_input.setEnabled(enabled)
        self.repo_url_input.setEnabled(enabled)
        self.commit_message_input.setEnabled(enabled)
        self.new_repo_radio.setEnabled(enabled)
        self.existing_repo_radio.setEnabled(enabled)
        self.use_folder_name_checkbox.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.exit_button.setEnabled(enabled)
        
    def _update_repo_url(self):
        """
        Actualiza la URL del repositorio basándose en el nombre de la carpeta seleccionada.
        Utiliza la información del usuario de GitHub CLI si está disponible.
        Controla la edición del campo de URL según el estado del checkbox.
        """
        from src.utils.common import get_git_username, build_github_url
        from src.utils.github_cli import extract_repo_name_from_path, build_github_repo_url
        
        folder_path = self.folder_path_input.text()
        if not folder_path:
            return
        
        # Determinar si el campo de URL debe ser editable
        is_manual_edit = self.use_folder_name_checkbox.isChecked()
        self.repo_url_input.setReadOnly(not is_manual_edit)
        
        # Establecer el estilo del campo según si es editable o no
        if is_manual_edit:
            self.repo_url_input.setStyleSheet("")
        else:
            self.repo_url_input.setStyleSheet("background-color: #F0F0F0;")
            
            # Generar la URL automáticamente cuando no es editable
            username = ""
            
            # Usar el nombre de usuario de GitHub CLI si está disponible
            if self.gh_cli_installed and self.gh_user_info and self.gh_user_info.get('username'):
                username = self.gh_user_info.get('username')
            else:
                # Si no hay información de GitHub CLI, usar el nombre de usuario de Git
                username = get_git_username()
            
            # Extraer el nombre del repositorio de la ruta de la carpeta
            repo_name = extract_repo_name_from_path(folder_path)
            
            # Construir la URL del repositorio
            if username:
                repo_url = build_github_repo_url(username, repo_name)
            else:
                # Si no se puede obtener el nombre de usuario, usar la función existente
                repo_url = build_github_url(folder_path)
            
            # Actualizar el campo de URL
            self.repo_url_input.setText(repo_url)
    
    def _log_message(self, message: str):
        """
        Añade un mensaje al área de log.
        
        Args:
            message (str): Mensaje a añadir.
        """
        self.log_text.append(message)
        # Desplazar al final del texto
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def _exit_application(self):
        """
        Cierra la aplicación.
        """
        QApplication.quit()