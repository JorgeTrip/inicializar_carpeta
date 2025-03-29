# Scripts de Inicializador de Repositorios GitHub

Esta carpeta contiene scripts útiles para el desarrollo y distribución de la aplicación.

## Contenido

### run_dev.bat

Script para ejecutar la aplicación en modo desarrollo. Útil durante el proceso de desarrollo y pruebas.

**Uso:**
```
run_dev.bat
```

### build_exe.bat

Script para compilar la aplicación en un ejecutable (.exe) utilizando PyInstaller. Genera un archivo ejecutable independiente que puede distribuirse a usuarios finales.

**Uso:**
```
build_exe.bat
```

**Requisitos:**
- PyInstaller (se instalará automáticamente si no está presente)

**Nota:** El ejecutable compilado se encontrará en la carpeta `dist` después de la compilación.