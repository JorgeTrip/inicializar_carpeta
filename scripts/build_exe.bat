@echo off
echo Compilando Inicializador de Repositorios GitHub...
echo.

cd ..

:: Verificar si PyInstaller está instalado
pip show pyinstaller > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

:: Compilar la aplicación
pyinstaller --name="Inicializador de Repositorios GitHub" ^^
            --windowed ^^
            --onefile ^^
            --icon=src\views\resources\icon.ico ^^
            --add-data="src;src" ^^
            main.py

echo.
echo Compilación completada. El ejecutable se encuentra en la carpeta dist.
echo.

pause