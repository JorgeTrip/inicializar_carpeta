#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo principal de la aplicación Inicializador de Repositorios GitHub.
Este archivo sirve como punto de entrada para la aplicación.
"""

import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton, QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QEventLoop
from src.views.main_window import MainWindow
from src.views.loading_screen import LoadingScreen
from src.utils.common import is_git_installed
from src.utils.github_cli import is_gh_cli_installed, is_gh_authenticated, get_gh_user_info, get_gh_cli_path


class AuthDialog(QDialog):
    """
    Diálogo para autenticación de GitHub CLI.
    Muestra instrucciones y opciones para iniciar el proceso de autenticación.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autenticación de GitHub CLI")
        self.setMinimumWidth(500)
        # Permitir que el diálogo permanezca visible mientras se trabaja con otras ventanas
        self.setWindowFlags((self.windowFlags() & ~Qt.WindowContextHelpButtonHint) | Qt.WindowStaysOnTopHint)
        # Asegurar que la ventana permanezca siempre visible, incluso cuando se abren otras ventanas
        self.setWindowModality(Qt.NonModal)
        
        layout = QVBoxLayout()
        
        # Mensaje de instrucciones
        info_label = QLabel(
            "<html><body>"
            "<p>Para utilizar esta aplicación, es necesario autenticarse en GitHub.</p>"
            "<p>Al hacer clic en 'Iniciar autenticación', se abrirá el navegador web para que puedas iniciar sesión con tus credenciales de GitHub.</p>"
            "<p>Sigue las instrucciones en el navegador y en la terminal para completar el proceso.</p>"
            "</body></html>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Botones
        button_layout = QVBoxLayout()
        
        self.auth_button = QPushButton("Iniciar autenticación")
        self.auth_button.setMinimumHeight(40)
        self.auth_button.clicked.connect(self.start_auth)
        button_layout.addWidget(self.auth_button)
        
        self.retry_button = QPushButton("Verificar autenticación")
        self.retry_button.setMinimumHeight(40)
        self.retry_button.clicked.connect(self.accept)
        button_layout.addWidget(self.retry_button)
        
        self.cancel_button = QPushButton("Salir")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def start_auth(self):
        """
        Inicia el proceso de autenticación de GitHub CLI.
        Ejecuta el comando gh auth login de forma interactiva para que el usuario pueda completar el proceso.
        """
        try:
            gh_path = get_gh_cli_path()
            if gh_path:
                import os
                
                # Actualizamos la interfaz para indicar que el proceso está en curso
                self.auth_button.setEnabled(False)
                self.auth_button.setText("Autenticación en curso...")
                self.retry_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
                
                # Mostramos las instrucciones directamente en el diálogo en lugar de un mensaje emergente
                # para que permanezcan visibles durante todo el proceso
                info_label = QLabel(
                    "<html><body>"
                    "<h3>Instrucciones para la autenticación:</h3>"
                    "<p><b>1.</b> En la ventana de terminal que se abrirá:</p>"
                    "<ul>"
                    "<li>Selecciona <b>'HTTPS'</b> cuando te pregunte por el protocolo preferido.</li>"
                    "<li>Responde <b>'Y'</b> cuando te pregunte si deseas autenticar Git con tus credenciales de GitHub.</li>"
                    "<li>Copia el código de un solo uso que aparecerá y presiona Enter para abrir el navegador.</li>"
                    "<li>En el navegador, pega el código y autoriza la aplicación.</li>"
                    "</ul>"
                    "<p><b>2.</b> Una vez completado el proceso en la terminal y el navegador:</p>"
                    "<ul>"
                    "<li>Vuelve a esta ventana y haz clic en <b>'Verificar autenticación'</b>.</li>"
                    "</ul>"
                    "<p style='color: #FF5722; font-weight: bold;'>Esta ventana permanecerá visible para que puedas consultar estas instrucciones en cualquier momento.</p>"
                    "</body></html>"
                )
                info_label.setWordWrap(True)
                info_label.setStyleSheet("background-color: #F5F5F5; padding: 10px; border-radius: 5px;")
                
                # Reemplazamos el contenido del layout con las nuevas instrucciones
                # Primero, limpiamos el layout existente
                for i in reversed(range(self.layout().count())):
                    item = self.layout().itemAt(i)
                    if item.layout() != self.layout().itemAt(self.layout().count()-1).layout():  # Preservamos el layout de botones
                        widget = item.widget()
                        if widget:
                            widget.deleteLater()
                
                # Añadimos las nuevas instrucciones al principio del layout
                self.layout().insertWidget(0, info_label)
                
                # Ejecutamos el comando gh auth login de forma interactiva
                try:
                    if os.name == 'nt':
                        # En Windows, usamos start cmd.exe para abrir una nueva ventana de terminal
                        # y ejecutar el comando de forma interactiva
                        cmd = f'start cmd.exe /k \"{gh_path}\" auth login --web'
                        subprocess.Popen(cmd, shell=True)
                    else:
                        # En otros sistemas operativos, abrimos una terminal
                        import tempfile
                        script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sh')
                        script_file.write(f'{gh_path} auth login --web\necho "Presiona Enter para cerrar..."\nread'.encode())
                        script_file.close()
                        os.chmod(script_file.name, 0o755)
                        subprocess.Popen(['x-terminal-emulator', '-e', script_file.name])
                except Exception as cmd_error:
                    # Si falla el comando, mostramos el error
                    print(f"Error al ejecutar gh auth login: {cmd_error}")
                    QMessageBox.critical(
                        self,
                        "Error de autenticación",
                        f"No se pudo iniciar el proceso de autenticación: {str(cmd_error)}"
                    )
                    # Restauramos el estado del botón
                    self.auth_button.setEnabled(True)
                    self.auth_button.setText("Iniciar autenticación")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de autenticación",
                f"No se pudo iniciar el proceso de autenticación: {str(e)}"
            )
            # Restauramos el estado del botón
            self.auth_button.setEnabled(True)
            self.auth_button.setText("Iniciar autenticación")


def authenticate_github_cli():
    """
    Inicia el proceso de autenticación de GitHub CLI.
    Muestra un diálogo con instrucciones y opciones para autenticarse.
    El diálogo permanece visible mientras se realiza la autenticación en la terminal.
    
    Returns:
        bool: True si el usuario está autenticado, False en caso contrario.
    """
    # Verificar si el usuario ya está autenticado
    if is_gh_authenticated():
        return True
    
    # Crear y mostrar diálogo de autenticación no modal
    auth_dialog = AuthDialog()
    auth_dialog.setModal(False)  # Hacemos que el diálogo no sea modal
    auth_dialog.show()  # Mostramos el diálogo sin bloquear
    auth_dialog.activateWindow()  # Aseguramos que tenga el foco
    auth_dialog.raise_()  # Lo colocamos encima de otras ventanas
    
    # Creamos un bucle de eventos personalizado para esperar a que el diálogo se cierre
    from PyQt5.QtCore import QEventLoop
    loop = QEventLoop()
    auth_dialog.accepted.connect(lambda: loop.exit(QDialog.Accepted))
    auth_dialog.rejected.connect(lambda: loop.exit(QDialog.Rejected))
    
    # Esperamos a que el usuario complete la autenticación o cancele
    result = loop.exec_()
    
    # Si el usuario cancela, salir
    if result == QDialog.Rejected:
        return False
    
    # Verificamos si la autenticación fue exitosa
    return is_gh_authenticated()


def main():
    """
    Función principal que inicia la aplicación.
    Crea la ventana principal y muestra la interfaz gráfica.
    """
    # Inicializar la aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Inicializador de Repositorios GitHub")
    
    # Definir las verificaciones iniciales
    checks = [
        {
            'id': 'git_installed',
            'description': 'Verificando instalación de Git',
            'function': is_git_installed,
            'critical': True,
            'error_message': "No se ha detectado Git en el sistema. Por favor, instálalo para poder usar esta aplicación."
        },
        {
            'id': 'gh_cli_installed',
            'description': 'Verificando instalación de GitHub CLI',
            'function': is_gh_cli_installed,
            'critical': True,
            'error_message': "No se ha detectado GitHub CLI en el sistema. Esta aplicación requiere GitHub CLI para funcionar correctamente. "
                            "Por favor, instálalo desde https://cli.github.com/ e inténtalo de nuevo."
        },
        {
            'id': 'gh_authenticated',
            'description': 'Verificando autenticación en GitHub',
            'function': is_gh_authenticated,
            'critical': True,
            'recovery_function': authenticate_github_cli,
            'error_message': "No se ha podido autenticar en GitHub. Esta aplicación requiere autenticación en GitHub para funcionar correctamente."
        }
    ]
    
    # Mostrar la pantalla de carga
    loading_screen = LoadingScreen(checks)
    result = loading_screen.exec_()
    
    # Si el usuario cancela o alguna verificación falla, salir
    if result != QDialog.Accepted:
        return
    
    # Obtener información del usuario autenticado
    gh_user_info = get_gh_user_info()
    
    # Verificar si se obtuvo la información del usuario
    if not gh_user_info:
        QMessageBox.critical(
            None,
            "Error al obtener información de usuario",
            "No se ha podido obtener la información del usuario de GitHub. Por favor, intenta nuevamente."
        )
        return
    
    # Crear y mostrar la ventana principal
    window = MainWindow(True, gh_user_info)
    window.show()
    
    # Ejecutar el bucle principal de la aplicación
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()