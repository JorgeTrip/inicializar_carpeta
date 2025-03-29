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
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
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

    def __init__(self):
        """
        Constructor de la ventana principal.
        Inicializa la interfaz gráfica.
        """
        super().__init__()
        
        # Configurar la ventana principal
        self.setWindowTitle("Inicializador de Repositorios GitHub")
        self.setMinimumSize(800, 600)
        
        # Crear el controlador de Git
        self.git_controller = GitController()
        
        # Inicializar la interfaz
        self._init_ui()
        
        # Verificar si Git está instalado
        if not is_git_installed():
            QMessageBox.warning(
                self,
                "Git no encontrado",
                "No se ha detectado Git en el sistema. Por favor, instálalo para poder usar esta aplicación."
            )
    
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
        
        url_description = QLabel(
            "Introduce la URL del repositorio de GitHub:"
        )
        url_description.setWordWrap(True)
        url_layout.addWidget(url_description)
        
        # Checkbox para usar el nombre de la carpeta como nombre del repositorio
        self.use_folder_name_checkbox = QCheckBox("Mi carpeta se llama igual que el repositorio")
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
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
        )
        
        if folder_path:
            self.folder_path_input.setText(folder_path)
            success, message = self.git_controller.set_folder_path(folder_path)
            self._log_message(message)
            
            # Actualizar la URL del repositorio si está marcada la opción
            if self.use_folder_name_checkbox.isChecked():
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
        
        # Validar que se haya introducido una URL
        repo_url = self.repo_url_input.text()
        if not repo_url:
            QMessageBox.warning(
                self,
                "URL no especificada",
                "Por favor, introduce la URL del repositorio de GitHub."
            )
            return
        
        # Obtener el mensaje de commit
        commit_message = self.commit_message_input.text()
        if not commit_message:
            commit_message = "Commit inicial"
        
        # Determinar el tipo de flujo de trabajo
        if self.new_repo_radio.isChecked():
            # Mostrar instrucciones para crear un nuevo repositorio
            self._show_new_repo_instructions()
            workflow = self.git_controller.get_new_repository_workflow(repo_url, commit_message)
        else:
            # Mostrar instrucciones para vincular con un repositorio existente
            self._show_existing_repo_instructions()
            workflow = self.git_controller.get_existing_repository_workflow(repo_url)
        
        # Preguntar al usuario si desea continuar
        reply = QMessageBox.question(
            self,
            "Confirmar operación",
            "¿Deseas continuar con el proceso de vinculación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
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
    
    def _show_new_repo_instructions(self):
        """
        Muestra instrucciones para crear un nuevo repositorio en GitHub.
        """
        instructions = (
            "<h3>Instrucciones para crear un nuevo repositorio en GitHub:</h3>"
            "<ol>"
            "<li>Inicia sesión en tu cuenta de GitHub.</li>"
            "<li>Haz clic en el botón '+' en la esquina superior derecha y selecciona 'New repository'.</li>"
            "<li>Introduce un nombre para tu repositorio.</li>"
            "<li>Opcionalmente, añade una descripción.</li>"
            "<li>Selecciona si el repositorio será público o privado.</li>"
            "<li>NO inicialices el repositorio con README, .gitignore o licencia.</li>"
            "<li>Haz clic en 'Create repository'.</li>"
            "<li>Copia la URL del repositorio (termina en .git) y pégala en el campo 'URL del Repositorio'.</li>"
            "</ol>"
            "<p>Una vez creado el repositorio, haz clic en 'Iniciar Proceso' para continuar.</p>"
        )
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Crear Nuevo Repositorio")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(instructions)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def _show_existing_repo_instructions(self):
        """
        Muestra instrucciones para vincular con un repositorio existente en GitHub.
        """
        instructions = (
            "<h3>Instrucciones para vincular con un repositorio existente:</h3>"
            "<ol>"
            "<li>Asegúrate de que el repositorio ya existe en GitHub.</li>"
            "<li>Copia la URL del repositorio (termina en .git) desde la página del repositorio.</li>"
            "<li>Pega la URL en el campo 'URL del Repositorio'.</li>"
            "</ol>"
            "<p>Ten en cuenta que si el repositorio no está vacío, es posible que necesites resolver conflictos manualmente.</p>"
            "<p>Haz clic en 'Iniciar Proceso' para continuar.</p>"
        )
        
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
        for result in results:
            status = "✅ Éxito" if result['success'] else "❌ Error"
            self._log_message(f"{status}: {result['name']} - {result['message']}")
            if result['success']:
                success_count += 1
        
        # Mostrar mensaje final
        if success_count == len(results):
            self._log_message("\n✅ Proceso completado con éxito.")
            QMessageBox.information(
                self,
                "Proceso Completado",
                "La carpeta ha sido vinculada con GitHub correctamente."
            )
        else:
            self._log_message(f"\n⚠️ Proceso completado con {len(results) - success_count} errores.")
            QMessageBox.warning(
                self,
                "Proceso Completado con Errores",
                f"El proceso ha finalizado con {len(results) - success_count} errores. Revisa el registro para más detalles."
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
        
        # Mostrar error en el log
        self._log_message(f"\n❌ Error: {error_message}")
        
        # Mostrar mensaje de error
        QMessageBox.critical(
            self,
            "Error en el Proceso",
            f"Se ha producido un error durante el proceso: {error_message}"
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
        
    def _update_repo_url(self):
        """
        Actualiza la URL del repositorio basándose en el nombre de la carpeta seleccionada.
        """
        from src.utils.common import get_git_username, build_github_url
        
        folder_path = self.folder_path_input.text()
        if not folder_path:
            return
            
        if self.use_folder_name_checkbox.isChecked():
            # Obtener el nombre de usuario de Git
            username = get_git_username()
            
            # Construir la URL del repositorio
            repo_url = build_github_url(folder_path, username)
            
            # Actualizar el campo de URL
            self.repo_url_input.setText(repo_url)
        else:
            # Si se desmarca la casilla, no hacer nada con la URL actual
            pass
    
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