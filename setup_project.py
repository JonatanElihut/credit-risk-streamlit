# setup_project.py
import os
import sys


def create_project_structure():
    """Crear estructura de carpetas del proyecto"""

    # Directorios principales
    directories = [
        'models',
        'utils',
        'pages',
        'config',
        'database'
    ]

    # Archivos principales
    main_files = [
        'app.py',
        'init_mysql.py',
        'requirements.txt',
        '.env.example',
        '.gitignore'
    ]

    # Archivos en utils
    utils_files = [
        'utils/__init__.py',
        'utils/database.py',
        'utils/auth.py',
        'utils/translation_helper.py',
        'utils/prediction.py',
        'utils/visualization.py'
    ]

    # Archivos en config
    config_files = [
        'config/mysql_config.py',
        'config/feature_translations.py'

    ]

    # Archivos en databas
    database_files = [
        'database/mysql_schema.sql'

    ]

    # Archivos en pages
    pages_files = [
        'pages/1_📊_Predicción.py',
        'pages/2_📈_Análisis.py',
        'pages/3_📋_Historial.py',
        'pages/4_⚙️_Configuración.py'
    ]

    print("🚀 Creando estructura del proyecto...")

    # Crear directorios
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

    # Crear archivos principales
    for file in main_files:
        open(file, 'w', encoding='utf-8').close()
        print(f"✅ Archivo creado: {file}")

    # Crear archivos en utils
    for file in utils_files:
        with open(file, 'w', encoding='utf-8') as f:
            f.write("# " + os.path.basename(file) + "\n")
        print(f"✅ Archivo creado: {file}")

    # Crear archivos en config
    for file in config_files:
        with open(file, 'w', encoding='utf-8') as f:
            f.write("# " + os.path.basename(file) + "\n")
        print(f"✅ Archivo creado: {file}")

    # Crear archivos en database
    for file in database_files:
        with open(file, 'w', encoding='utf-8') as f:
            f.write("# " + os.path.basename(file) + "\n")
        print(f"✅ Archivo creado: {file}")

    # Crear archivos en pages
    for file in pages_files:
        with open(file, 'w', encoding='utf-8') as f:
            f.write("# " + os.path.basename(file) + "\nimport streamlit as st\n\n")
        print(f"✅ Archivo creado: {file}")

    print("\n🎉 Estructura del proyecto creada exitosamente!")
    print("\n📦 Siguientes pasos:")
    print("1. Copia tus archivos de modelo a la carpeta 'models/'")
    print("2. Configura las variables de entorno en .env")
    print("3. Ejecuta 'pip install -r requirements.txt'")
    print("4. Ejecuta 'streamlit run app.py'")


if __name__ == "__main__":
    create_project_structure()