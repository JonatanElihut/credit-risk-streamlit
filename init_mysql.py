"""
Script de inicialización para MySQL
"""
import sys
import os

# Agregar el directorio padre al path para importar utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st


def initialize_database():
    """Inicializar la base de datos MySQL"""

    st.set_page_config(
        page_title="Inicialización BD",
        page_icon="🔧",
        layout="wide"
    )

    st.title("🔧 Inicialización de Base de Datos MySQL")
    st.markdown("---")

    st.info("""
    ### ¿Qué hace este script?
    1. Verifica la conexión a MySQL
    2. Crea la base de datos si no existe
    3. Crea todas las tablas necesarias
    4. Inserta datos de configuración inicial

    **Requisitos previos:**
    - MySQL Server 8.0+ instalado y ejecutándose
    - Archivo `.env` configurado con credenciales
    - Archivo `database/mysql_schema.sql` en su lugar
    """)

    # Verificar que existe el archivo SQL
    sql_file = 'database/mysql_schema.sql'
    if not os.path.exists(sql_file):
        st.error(f"❌ No se encuentra el archivo: {sql_file}")
        st.info("""
        Crea el archivo `database/mysql_schema.sql` con el siguiente contenido:

        1. Crea la carpeta 'database' si no existe
        2. Guarda allí el script SQL que te proporcioné
        3. Vuelve a ejecutar este script
        """)
        return False

    # Importar db_manager después de configurar el path
    try:
        from utils.database import db_manager
        from sqlalchemy import text
    except ImportError as e:
        st.error(f"❌ Error de importación: {str(e)}")
        return False

    # 1. Probar conexión básica
    with st.spinner("🔌 Probando conexión a MySQL..."):
        if db_manager.test_connection():
            st.success("✅ Conexión establecida")
        else:
            st.error("❌ No se pudo conectar a MySQL")
            st.info("""
            **Solución:**
            1. Verifica que MySQL esté ejecutándose
            2. Revisa las credenciales en `.env`
            3. Asegúrate de que el usuario tenga permisos
            """)
            return False

    # 2. Crear base de datos si no existe
    with st.spinner("🗄️ Verificando/Creando base de datos..."):
        try:
            # Conectar sin especificar base de datos
            from sqlalchemy import create_engine

            # Obtener parámetros de conexión
            import os
            from dotenv import load_dotenv
            load_dotenv()

            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '3306')
            user = os.getenv('DB_USER', 'root')
            password = os.getenv('DB_PASSWORD', '')
            database = os.getenv('DB_NAME', 'CreditRiskDB')

            # Crear engine temporal
            temp_engine = create_engine(
                f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/",
                echo=False
            )

            with temp_engine.connect() as conn:
                # Crear base de datos si no existe
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))
                conn.execute(text(f"USE {database}"))
                conn.commit()

            st.success(f"✅ Base de datos '{database}' verificada/creada")

        except Exception as e:
            st.error(f"❌ Error al crear base de datos: {str(e)}")
            return False

    # 3. Crear tablas
    with st.spinner("📊 Creando tablas..."):
        try:
            # Leer script SQL
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # Dividir por sentencias SQL
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]

            # Ejecutar cada sentencia
            success_count = 0
            error_count = 0

            with db_manager.get_connection() as conn:
                for i, statement in enumerate(statements):
                    try:
                        if statement:  # Asegurar que no sea cadena vacía
                            conn.execute(text(statement))
                            success_count += 1
                    except Exception as e:
                        st.warning(f"⚠️ Sentencia {i + 1} tuvo advertencia: {str(e)}")
                        error_count += 1
                        # Continuar con las siguientes sentencias

                conn.commit()

            st.success(f"✅ Tablas creadas: {success_count} sentencias ejecutadas")
            if error_count > 0:
                st.warning(f"⚠️ {error_count} sentencias con advertencias (puede ser normal)")

            return True

        except Exception as e:
            st.error(f"❌ Error al crear tablas: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return False


# Función principal de Streamlit
def main():
    """Función principal"""

    st.sidebar.title("Configuración")

    st.sidebar.info("""
    **Credenciales necesarias en `.env`:**
    ```
    DB_HOST=localhost
    DB_PORT=3306
    DB_NAME=CreditRiskDB
    DB_USER=root
    DB_PASSWORD=tu_contraseña
    ```
    """)

    # Botón para iniciar
    if st.sidebar.button("🚀 Iniciar Inicialización", type="primary", use_container_width=True):
        if initialize_database():
            st.balloons()
            st.success("✨ Base de datos MySQL inicializada correctamente!")

            st.markdown("---")
            st.subheader("🎉 ¡Listo para usar!")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### Siguientes pasos:
                1. ✅ Base de datos creada
                2. ✅ Tablas configuradas
                3. ✅ Datos iniciales insertados
                """)

            with col2:
                if st.button("📱 Ejecutar Aplicación Principal", use_container_width=True):
                    st.info("Ejecuta en otra terminal: streamlit run app.py")

            st.markdown("---")
            st.info("""
            ### Comandos para verificar:
            ```bash
            # Conectar a MySQL
            mysql -u root -p

            # Ver bases de datos
            SHOW DATABASES;

            # Usar tu base de datos
            USE CreditRiskDB;

            # Ver tablas
            SHOW TABLES;
            ```
            """)
        else:
            st.error("❌ La inicialización falló. Revisa los mensajes arriba.")

    # Mostrar estado actual
    st.sidebar.markdown("---")
    st.sidebar.subheader("Estado del sistema")

    # Verificar archivos
    files_to_check = {
        '.env': 'Configuración',
        'database/mysql_schema.sql': 'Esquema SQL',
        'utils/database.py': 'Módulo DB',
    }

    for file, description in files_to_check.items():
        if os.path.exists(file):
            st.sidebar.success(f"✅ {description}")
        else:
            st.sidebar.error(f"❌ {description}")


if __name__ == "__main__":
    main()