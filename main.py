#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo principal de la aplicación Inicializador de Repositorios GitHub.
Este archivo sirve como punto de entrada para la aplicación.
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.views.main_window import MainWindow


def main():
    """
    Función principal que inicia la aplicación.
    Crea la ventana principal y muestra la interfaz gráfica.
    """
    # Inicializar la aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Inicializador de Repositorios GitHub")
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar el bucle principal de la aplicación
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()