#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo que contiene la pantalla de carga inicial de la aplicación.
Implementa una interfaz gráfica que muestra el progreso de las verificaciones iniciales.
"""

import sys
from typing import List, Dict, Any, Optional, Callable

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QApplication, QCheckBox,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon


class CheckItem(QFrame):
    """
    Componente que representa un elemento del checklist.
    Muestra un checkbox y una etiqueta con la descripción del elemento.
    """
    def __init__(self, text: str, parent=None):
        """
        Constructor del componente CheckItem.
        
        Args:
            text (str): Texto descriptivo del elemento.
            parent: Widget padre.
        """
        super().__init__(parent)
        
        # Configurar el layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear el checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setEnabled(False)  # Deshabilitado para que el usuario no pueda modificarlo
        layout.addWidget(self.checkbox)
        
        # Crear la etiqueta
        self.label = QLabel(text)
        layout.addWidget(self.label)
        
        # Agregar espacio expansible al final
        layout.addStretch()
    
    def set_checked(self, checked: bool, success: bool = True):
        """
        Establece el estado del checkbox.
        
        Args:
            checked (bool): True para marcar como completado, False en caso contrario.
            success (bool): True si la verificación fue exitosa, False si falló.
        """
        self.checkbox.setChecked(checked)
        
        if checked:
            if success:
                self.label.setStyleSheet("color: green; font-weight: bold;")
                self.label.setText(f"{self.label.text()} ✓")
            else:
                self.label.setStyleSheet("color: red; font-weight: bold;")
                self.label.setText(f"{self.label.text()} ✗")


class LoadingWorker(QThread):
    """
    Clase para ejecutar las verificaciones iniciales en segundo plano.
    Evita que la interfaz se bloquee durante las verificaciones.
    """
    progress_signal = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(bool, dict)
    
    def __init__(self, checks: List[Dict[str, Any]]):
        """
        Constructor de la clase LoadingWorker.
        
        Args:
            checks (List[Dict[str, Any]]): Lista de verificaciones a realizar.
        """
        super().__init__()
        self.checks = checks
    
    def run(self):
        """
        Método que se ejecuta en segundo plano.
        Realiza las verificaciones y emite señales de progreso y finalización.
        """
        all_success = True
        results = {}
        
        for check in self.checks:
            try:
                # Ejecutar la verificación
                result = check['function'](*check.get('args', []), **check.get('kwargs', {}))
                success = True if result else False
                
                # Si la verificación requiere un resultado específico y no coincide, marcar como fallida
                if 'expected_result' in check and result != check['expected_result']:
                    success = False
                
                # Almacenar el resultado
                results[check['id']] = result
                
                # Emitir señal de progreso
                self.progress_signal.emit(check['id'], success)
                
                # Si la verificación es crítica y falló, marcar todo como fallido
                if check.get('critical', False) and not success:
                    all_success = False
                    
                    # Si la verificación tiene una función de recuperación, ejecutarla
                    if 'recovery_function' in check and callable(check['recovery_function']):
                        recovery_result = check['recovery_function'](*check.get('recovery_args', []), **check.get('recovery_kwargs', {}))
                        results[f"{check['id']}_recovery"] = recovery_result
                        
                        # Si la recuperación fue exitosa, continuar con las verificaciones
                        if recovery_result:
                            all_success = True
                            continue
                    
                    # Si no hay función de recuperación o falló, terminar las verificaciones
                    break
            except Exception as e:
                # Si ocurre un error, marcar la verificación como fallida
                self.progress_signal.emit(check['id'], False)
                results[check['id']] = str(e)
                
                # Si la verificación es crítica, marcar todo como fallido
                if check.get('critical', False):
                    all_success = False
                    break
        
        # Emitir señal de finalización
        self.finished_signal.emit(all_success, results)


class LoadingScreen(QDialog):
    """
    Pantalla de carga inicial de la aplicación.
    Muestra un checklist con el progreso de las verificaciones iniciales.
    """
    def __init__(self, checks: List[Dict[str, Any]], parent=None):
        """
        Constructor de la pantalla de carga.
        
        Args:
            checks (List[Dict[str, Any]]): Lista de verificaciones a realizar.
            parent: Widget padre.
        """
        super().__init__(parent)
        
        # Configurar la ventana
        self.setWindowTitle("Inicializando aplicación")
        self.setMinimumSize(500, 300)
        # Configurar banderas para que la ventana permanezca siempre visible
        self.setWindowFlags((self.windowFlags() & ~Qt.WindowContextHelpButtonHint) | Qt.WindowStaysOnTopHint)
        
        # Almacenar las verificaciones
        self.checks = checks
        self.check_items = {}
        self.results = {}
        
        # Inicializar la interfaz
        self._init_ui()
        
        # Iniciar las verificaciones
        self._start_checks()
    
    def _init_ui(self):
        """
        Inicializa los componentes de la interfaz gráfica.
        """
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Inicializando aplicación")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Descripción
        description_label = QLabel(
            "Por favor, espera mientras se realizan las verificaciones iniciales necesarias para el funcionamiento de la aplicación."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(description_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Checklist
        checklist_layout = QVBoxLayout()
        checklist_layout.setSpacing(10)
        
        # Crear los elementos del checklist
        for check in self.checks:
            check_item = CheckItem(check['description'])
            self.check_items[check['id']] = check_item
            checklist_layout.addWidget(check_item)
        
        layout.addLayout(checklist_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Botón de continuar (inicialmente deshabilitado)
        self.continue_button = QPushButton("Continuar")
        self.continue_button.setEnabled(False)
        self.continue_button.setMinimumHeight(40)
        self.continue_button.clicked.connect(self.accept)
        layout.addWidget(self.continue_button)
    
    def _start_checks(self):
        """
        Inicia las verificaciones en segundo plano.
        """
        # Crear el worker
        self.worker = LoadingWorker(self.checks)
        
        # Conectar señales
        self.worker.progress_signal.connect(self._update_progress)
        self.worker.finished_signal.connect(self._checks_finished)
        
        # Iniciar el worker
        self.worker.start()
    
    @pyqtSlot(str, bool)
    def _update_progress(self, check_id: str, success: bool):
        """
        Actualiza el progreso de las verificaciones.
        
        Args:
            check_id (str): Identificador de la verificación.
            success (bool): True si la verificación fue exitosa, False si falló.
        """
        # Actualizar el elemento del checklist
        if check_id in self.check_items:
            self.check_items[check_id].set_checked(True, success)
            
            # Asegurar que la ventana permanezca visible y con foco
            self.activateWindow()
            self.raise_()
        
        # Actualizar la barra de progreso
        completed = sum(1 for item in self.check_items.values() if item.checkbox.isChecked())
        progress = int((completed / len(self.check_items)) * 100)
        self.progress_bar.setValue(progress)
        
        # Procesar eventos para mantener la interfaz responsiva
        QApplication.processEvents()
    
    @pyqtSlot(bool, dict)
    def _checks_finished(self, all_success: bool, results: dict):
        """
        Método llamado cuando se completan todas las verificaciones.
        
        Args:
            all_success (bool): True si todas las verificaciones fueron exitosas, False si alguna falló.
            results (dict): Resultados de las verificaciones.
        """
        # Almacenar los resultados
        self.results = results
        
        # Actualizar la barra de progreso
        self.progress_bar.setValue(100)
        
        # Habilitar el botón de continuar si todas las verificaciones fueron exitosas
        self.continue_button.setEnabled(all_success)
        
        # Asegurar que la ventana permanezca visible y con foco
        self.activateWindow()
        self.raise_()
        
        # Si alguna verificación falló, mostrar mensaje
        if not all_success:
            # Buscar la primera verificación crítica que falló
            failed_check = None
            for check in self.checks:
                if check.get('critical', False) and not results.get(check['id'], False):
                    failed_check = check
                    break
            
            # Actualizar el botón de continuar
            self.continue_button.setText("Salir")
            self.continue_button.setStyleSheet("background-color: #FF5252; color: white;")
            
            # Mostrar mensaje de error
            if failed_check and 'error_message' in failed_check:
                error_label = QLabel(failed_check['error_message'])
                error_label.setStyleSheet("color: red; font-weight: bold;")
                error_label.setWordWrap(True)
                error_label.setAlignment(Qt.AlignCenter)
                self.layout().insertWidget(self.layout().count() - 1, error_label)