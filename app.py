"""
Aplicación principal de Streamlit - Sistema de Predicción de Riesgo Crediticio
VERSIÓN CORREGIDA PARA DAR MISMOS RESULTADOS QUE TKINTER
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import json

# Configuración de la página
st.set_page_config(
    page_title="🏦 Sistema de Riesgo Crediticio",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos
from utils.auth import auth_manager
from utils.database import db_manager
from utils.prediction import prediction_manager
from utils.visualization import viz_manager
from utils.translation_helper import TranslationHelper

def initialize_session_state():
    """Inicializar variables del session_state"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'form_initialized' not in st.session_state:
        st.session_state.form_initialized = False
    if 'password_changed' not in st.session_state:
        st.session_state.password_changed = False

def show_login_page():
    """Mostrar página de inicio de sesión/registro"""
    st.title("🏦 Sistema de Predicción de Riesgo Crediticio")
    st.markdown("---")

    # Verificar conexión a base de datos
    with st.spinner("Verificando conexión a base de datos..."):
        if db_manager.test_connection():
            st.success("✅ Conexión a base de datos establecida")
        else:
            st.error("❌ No se pudo conectar a la base de datos")
            st.stop()

    # Pestañas para Login/Registro
    tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])

    with tab1:
        st.header("Iniciar Sesión")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")

            submit = st.form_submit_button("Ingresar")

            if submit:
                if not email or not password:
                    st.error("❌ Por favor, complete todos los campos")
                else:
                    success, message = auth_manager.login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab2:
        st.header("Registrarse")

        with st.form("register_form"):
            full_name = st.text_input("Nombre Completo")
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Contraseña", type="password")

            submit = st.form_submit_button("Crear Cuenta")

            if submit:
                if not all([full_name, email, password, confirm_password]):
                    st.error("❌ Por favor, complete todos los campos")
                else:
                    success, message = auth_manager.register_user(
                        email, full_name, password, confirm_password
                    )
                    if success:
                        st.success(message)
                        st.info("✅ Ahora puede iniciar sesión con sus credenciales")
                    else:
                        st.error(message)


def show_main_page():
    """Mostrar página principal después del login"""
    user = auth_manager.get_current_user()

    # Barra lateral
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2721/2721264.png", width=100)
        st.markdown(f"### 👋 Bienvenido, {user['full_name']}")
        st.markdown(f"📧 {user['email']}")
        st.markdown("---")

        # Menú de navegación
        st.markdown("### 📋 Navegación")
        page = st.selectbox(
            "Seleccione una página",
            ["📊 Predicción", "📈 Análisis", "📋 Historial", "⚙️ Configuración", "🚪 Salir"]
        )

        st.markdown("---")

        # Información del modelo
        if st.checkbox("ℹ️ Mostrar info del modelo"):
            model_info = prediction_manager.get_model_info()
            st.json(model_info.get('hyperparameters', {}))

        # Botón de salir
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            auth_manager.logout()
            st.rerun()

    # Redirigir a la página seleccionada
    if page == "📊 Predicción":
        show_prediction_page()
    elif page == "📈 Análisis":
        show_analysis_page()
    elif page == "📋 Historial":
        show_history_page()
    elif page == "⚙️ Configuración":
        show_configuration_page()
    elif page == "🚪 Salir":
        auth_manager.logout()
        st.rerun()


def show_prediction_page():
    """Mostrar página de predicción - VERSIÓN MEXICANA COMPLETA"""
    st.title("📊 Predicción de Riesgo Crediticio")
    st.markdown("---")

    # Importar el helper de traducciones
    from utils.translation_helper import TranslationHelper

    # Información del modelo
    model_info = prediction_manager.get_model_info()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Modelo", model_info.get('type', 'Random Forest'))
    with col2:
        st.metric("Características", model_info.get('n_features', 'N/A'))
    with col3:
        st.metric("Umbral Actual", f"{prediction_manager.threshold:.1%}")

    st.markdown("---")

    # Control de umbral ajustable (igual que Tkinter: 0.1 a 0.9)
    st.subheader("⚙️ Configuración de Umbral")

    col1, col2 = st.columns([3, 1])

    with col1:
        current_threshold = prediction_manager.threshold
        new_threshold = st.slider(
            "Umbral de decisión (probabilidad mínima para RECHAZAR)",
            min_value=0.1,
            max_value=0.9,
            value=float(current_threshold),
            step=0.05,
            format="%.2f",
            key="threshold_slider",
            help="""Probabilidad mínima de riesgo para clasificar como RECHAZADO:
            • Valores más bajos = Más aprobaciones (pero más riesgo)
            • Valores más altos = Menos aprobaciones (pero menos riesgo)"""
        )

        if new_threshold != current_threshold:
            prediction_manager.set_threshold(new_threshold)
            st.success(f"✅ Umbral actualizado a {new_threshold:.1%}")

    with col2:
        st.metric("Umbral Actual", f"{current_threshold:.1%}")

        # Botón para restablecer umbral
        if st.button("🔄 Restablecer", key="reset_threshold", use_container_width=True):
            prediction_manager.set_threshold(0.4)  # Valor por defecto de Tkinter
            st.success("✅ Umbral restablecido a 40%")
            st.rerun()

    st.markdown("---")

    # Primero definimos las claves comunes que todos los perfiles tendrán
    FEATURE_KEYS = [
        'out_prncp', 'out_prncp_inv', 'last_pymnt_amnt', 'total_rec_prncp',
        'recoveries', 'collection_recovery_fee', 'total_pymnt', 'installment',
        'funded_amnt_inv', 'total_pymnt_inv', 'total_rec_int',
        'hardship_payoff_balance_amount', 'orig_projected_additional_accrued_interest',
        'int_rate', 'hardship_amount', 'total_rec_late_fee',
        'hardship_last_payment_amount', 'dti', 'annual_inc', 'bc_util'
    ]

    # Valores por defecto (igual que Tkinter)
    default_values = {
        'out_prncp': 0.0,
        'out_prncp_inv': 0.0,
        'last_pymnt_amnt': 500.0,
        'total_rec_prncp': 1000.0,
        'recoveries': 0.0,
        'collection_recovery_fee': 0.0,
        'total_pymnt': 2000.0,
        'installment': 250.0,
        'funded_amnt_inv': 8000.0,
        'total_pymnt_inv': 2000.0,
        'total_rec_int': 500.0,
        'hardship_payoff_balance_amount': 0.0,
        'orig_projected_additional_accrued_interest': 0.0,
        'int_rate': 6.5,
        'hardship_amount': 0.0,
        'total_rec_late_fee': 0.0,
        'hardship_last_payment_amount': 0.0,
        'dti': 10.0,
        'annual_inc': 95000.0,
        'bc_util': 15.0
    }

    # Inicializar session state para los valores del formulario
    if 'form_initialized' not in st.session_state:
        # Inicializar cada campo individualmente en session_state
        for key, value in default_values.items():
            st.session_state[key] = value

        st.session_state.form_initialized = True
        st.session_state.current_profile = "default"

    # Definir perfiles - VERSIÓN IDÉNTICA A TKINTER
    PROFILES = {
        "minimal": {
            'name': "🟢 RIESGO MÍNIMO (0-20%)",
            'values': {
                'out_prncp': 0.0,
                'out_prncp_inv': 0.0,
                'last_pymnt_amnt': 450.0,
                'total_rec_prncp': 9800.0,
                'recoveries': 0.0,
                'collection_recovery_fee': 0.0,
                'total_pymnt': 10500.0,
                'installment': 300.0,
                'funded_amnt_inv': 10000.0,
                'total_pymnt_inv': 10500.0,
                'total_rec_int': 700.0,
                'hardship_payoff_balance_amount': 0.0,
                'orig_projected_additional_accrued_interest': 0.0,
                'int_rate': 6.5,
                'hardship_amount': 0.0,
                'total_rec_late_fee': 0.0,
                'hardship_last_payment_amount': 0.0,
                'dti': 8.5,
                'annual_inc': 120000.0,
                'bc_util': 15.5
            },
            'expected_result': "APROBADO",
            'expected_probability': "0-20%",
            'description': "Cliente premium, historial crediticio impecable"
        },
        "low": {
            'name': "🟡 RIESGO BAJO (20-40%)",
            'values': {
                'out_prncp': 500.0,
                'out_prncp_inv': 400.0,
                'last_pymnt_amnt': 350.0,
                'total_rec_prncp': 4500.0,
                'recoveries': 0.0,
                'collection_recovery_fee': 0.0,
                'total_pymnt': 5000.0,
                'installment': 250.0,
                'funded_amnt_inv': 8000.0,
                'total_pymnt_inv': 5000.0,
                'total_rec_int': 500.0,
                'hardship_payoff_balance_amount': 0.0,
                'orig_projected_additional_accrued_interest': 0.0,
                'int_rate': 8.5,
                'hardship_amount': 0.0,
                'total_rec_late_fee': 0.0,
                'hardship_last_payment_amount': 0.0,
                'dti': 12.5,
                'annual_inc': 85000.0,
                'bc_util': 25.5
            },
            'expected_result': "APROBADO",
            'expected_probability': "20-40%",
            'description': "Cliente sólido, aprobación estándar"
        },
        "high": {
            'name': "🔴 RIESGO ALTO (40-60%)",
            'values': {
                'out_prncp': 6000.0,
                'out_prncp_inv': 5500.0,
                'last_pymnt_amnt': 100.0,
                'total_rec_prncp': 800.0,
                'recoveries': 500.0,
                'collection_recovery_fee': 75.0,
                'total_pymnt': 1200.0,
                'installment': 450.0,
                'funded_amnt_inv': 15000.0,
                'total_pymnt_inv': 1200.0,
                'total_rec_int': 100.0,
                'hardship_payoff_balance_amount': 2500.0,
                'orig_projected_additional_accrued_interest': 300.0,
                'int_rate': 18.5,
                'hardship_amount': 3000.0,
                'total_rec_late_fee': 50.0,
                'hardship_last_payment_amount': 100.0,
                'dti': 38.5,
                'annual_inc': 45000.0,
                'bc_util': 75.5
            },
            'expected_result': "RECHAZADO",
            'expected_probability': "40-60%",
            'description': "Cliente de alto riesgo, rechazo recomendado"
        },
        "default": {
            'name': "⚙️ VALORES PREDETERMINADOS",
            'values': default_values.copy(),
            'expected_result': "APROBADO",
            'expected_probability': "0-20%",
            'description': "Valores iniciales del sistema"
        }
    }

    # Mostrar perfil actual
    if 'current_profile' in st.session_state:
        profile_name = PROFILES.get(st.session_state.current_profile, {}).get('name', 'Personalizado')
        profile_desc = PROFILES.get(st.session_state.current_profile, {}).get('description', '')
        st.info(f"📋 **Perfil actual:** {profile_name}\n\n{profile_desc}")

    # Botones de acción
    st.markdown("### 🎯 Cargar Perfiles Predefinidos")

    # Primera fila de botones
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🟢 RIESGO MÍNIMO", use_container_width=True, key="btn_minimal"):
            for key, value in PROFILES["minimal"]['values'].items():
                st.session_state[key] = value
            st.session_state.current_profile = "minimal"
            st.success(PROFILES["minimal"]['name'])
            st.info("Cliente premium - Aprobación automática")

    with col2:
        if st.button("🟡 RIESGO BAJO", use_container_width=True, key="btn_low"):
            for key, value in PROFILES["low"]['values'].items():
                st.session_state[key] = value
            st.session_state.current_profile = "low"
            st.success(PROFILES["low"]['name'])
            st.info("Cliente sólido - Aprobación estándar")

    with col3:
        if st.button("🔴 RIESGO ALTO", use_container_width=True, key="btn_high"):
            for key, value in PROFILES["high"]['values'].items():
                st.session_state[key] = value
            st.session_state.current_profile = "high"
            st.success(PROFILES["high"]['name'])
            st.info("Cliente de alto riesgo - Rechazo recomendado")

    # Tercera fila - botones adicionales
    col7, col8 = st.columns(2)

    with col7:
        if st.button("⚙️ PREDETERMINADOS", use_container_width=True, key="btn_default"):
            for key, value in PROFILES["default"]['values'].items():
                st.session_state[key] = value
            st.session_state.current_profile = "default"
            st.success(PROFILES["default"]['name'])
            st.info("Valores por defecto del sistema")

    with col8:
        if st.button("🎲 VALORES ALEATORIOS", use_container_width=True, key="btn_random"):
            import random
            random_values = {}
            for key in FEATURE_KEYS:
                if 'rate' in key or 'util' in key or 'dti' in key:
                    random_values[key] = round(random.uniform(0, 30), 1)
                elif 'inc' in key:
                    random_values[key] = round(random.uniform(30000, 120000), 0)
                elif 'amnt' in key or 'prncp' in key or 'pymnt' in key:
                    random_values[key] = round(random.uniform(0, 10000), 2)
                else:
                    random_values[key] = round(random.uniform(0, 1000), 2)

            for key, value in random_values.items():
                st.session_state[key] = value
            st.session_state.current_profile = "random"
            st.success("🎲 Valores aleatorios generados")

    # Sección de contexto mexicano
    st.markdown("---")

    # Agregar información contextual mexicana
    with st.expander("🇲🇽 Contexto Mexicano - Información de Referencia", expanded=False):
        context_info = TranslationHelper.create_mexican_context_info()

        # Crear pestañas para cada sección de contexto
        dti_tab, income_tab, interest_tab, credit_tab = st.tabs([
            "📊 DTI",
            "💰 Ingresos",
            "📈 Tasas",
            "💳 Crédito"
        ])

        with dti_tab:
            st.markdown(context_info['dti_info']['content'])
            st.progress(0.35, text="DTI Recomendado: <35%")

        with income_tab:
            st.markdown(context_info['income_info']['content'])

            # Tabla de referencia de ingresos
            income_data = {
                "Nivel": ["Salario Mínimo", "Ingreso Promedio", "Clase Media Baja", "Clase Media Alta"],
                "Mensual (MXN)": ["$7,468", "$12,000 - $25,000", "$25,000 - $45,000", "$45,000 - $80,000"],
                "Anual (MXN)": ["$89,616", "$144,000 - $300,000", "$300,000 - $540,000", "$540,000 - $960,000"]
            }
            st.dataframe(income_data, use_container_width=True)

        with interest_tab:
            st.markdown(context_info['interest_info']['content'])

            # Gráfico de tasas
            import plotly.graph_objects as go

            rates_data = {
                "Producto": ["Tarjetas Crédito", "Crédito Personal", "Nómina", "Automotriz"],
                "Tasa Mínima (%)": [35, 15, 12, 8],
                "Tasa Máxima (%)": [65, 40, 25, 15],
                "CAT Promedio (%)": [55, 28, 18, 11]
            }

            fig = go.Figure(data=[
                go.Bar(name='Tasa Mínima', x=rates_data["Producto"], y=rates_data["Tasa Mínima (%)"]),
                go.Bar(name='CAT Promedio', x=rates_data["Producto"], y=rates_data["CAT Promedio (%)"]),
                go.Bar(name='Tasa Máxima', x=rates_data["Producto"], y=rates_data["Tasa Máxima (%)"])
            ])

            fig.update_layout(
                title="Tasas de Interés en México 2024",
                barmode='group',
                yaxis_title="Tasa Anual (%)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with credit_tab:
            st.markdown("""
            **📋 Utilización de Crédito (Buró de Crédito):**
            - **Excelente (<30%):** Buen manejo del crédito
            - **Adecuado (30-50%):** Uso moderado
            - **Alto (50-75%):** Riesgo de sobreendeudamiento
            - **Muy Alto (>75%):** Capacidad comprometida

            **🏛️ Instituciones regulatorias:**
            • **Banxico:** Banco de México (tasa de referencia)
            • **CNBV:** Comisión Nacional Bancaria y de Valores
            • **Condusef:** Protección a usuarios financieros
            • **Buró de Crédito:** Historial crediticio

            **📄 Documentación común requerida:**
            1. Identificación oficial (INE)
            2. Comprobante de domicilio
            3. Comprobantes de ingresos (3 meses)
            4. Estados de cuenta bancarios
            """)

    st.markdown("---")

    # Formulario de entrada CON NOMBRES MEXICANOS
    st.header("📝 Datos del Solicitante - Contexto Mexicano")

    # Crear columnas para el formulario
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Información del Crédito")

        # Saldo Capital Pendiente
        out_prncp = TranslationHelper.create_input_field_with_context(
            'out_prncp',
            st.session_state.get('out_prncp', 0.0),
            min_value=0.0,
            max_value=1000000.0,
            step=1000.0,
            key="out_prncp"
        )

        # Saldo Inversionistas Pendiente
        out_prncp_inv = TranslationHelper.create_input_field_with_context(
            'out_prncp_inv',
            st.session_state.get('out_prncp_inv', 0.0),
            min_value=0.0,
            max_value=1000000.0,
            step=1000.0,
            key="out_prncp_inv"
        )

        # Monto Último Pago
        last_pymnt_amnt = TranslationHelper.create_input_field_with_context(
            'last_pymnt_amnt',
            st.session_state.get('last_pymnt_amnt', 500.0),
            min_value=0.0,
            max_value=50000.0,
            step=100.0,
            key="last_pymnt_amnt"
        )

        # Total Capital Recibido
        total_rec_prncp = TranslationHelper.create_input_field_with_context(
            'total_rec_prncp',
            st.session_state.get('total_rec_prncp', 1000.0),
            min_value=0.0,
            max_value=1000000.0,
            step=1000.0,
            key="total_rec_prncp"
        )

        # Cobranza Recuperada
        recoveries = TranslationHelper.create_input_field_with_context(
            'recoveries',
            st.session_state.get('recoveries', 0.0),
            min_value=0.0,
            max_value=100000.0,
            step=1000.0,
            key="recoveries"
        )

        # Comisión de Cobranza
        collection_recovery_fee = TranslationHelper.create_input_field_with_context(
            'collection_recovery_fee',
            st.session_state.get('collection_recovery_fee', 0.0),
            min_value=0.0,
            max_value=50000.0,
            step=100.0,
            key="collection_recovery_fee"
        )

        # Total Pagado
        total_pymnt = TranslationHelper.create_input_field_with_context(
            'total_pymnt',
            st.session_state.get('total_pymnt', 2000.0),
            min_value=0.0,
            max_value=1000000.0,
            step=1000.0,
            key="total_pymnt"
        )

        # Pago Mensual (Mensualidad)
        installment = TranslationHelper.create_input_field_with_context(
            'installment',
            st.session_state.get('installment', 250.0),
            min_value=0.0,
            max_value=50000.0,
            step=100.0,
            key="installment"
        )

        # Monto Financiado por Inversionistas
        funded_amnt_inv = TranslationHelper.create_input_field_with_context(
            'funded_amnt_inv',
            st.session_state.get('funded_amnt_inv', 8000.0),
            min_value=0.0,
            max_value=500000.0,
            step=1000.0,
            key="funded_amnt_inv"
        )

        # Total Pagado a Inversionistas
        total_pymnt_inv = TranslationHelper.create_input_field_with_context(
            'total_pymnt_inv',
            st.session_state.get('total_pymnt_inv', 2000.0),
            min_value=0.0,
            max_value=1000000.0,
            step=1000.0,
            key="total_pymnt_inv"
        )

    with col2:
        st.subheader("📈 Otras Características")

        # Total Intereses Recibidos
        total_rec_int = TranslationHelper.create_input_field_with_context(
            'total_rec_int',
            st.session_state.get('total_rec_int', 500.0),
            min_value=0.0,
            max_value=500000.0,
            step=1000.0,
            key="total_rec_int"
        )

        # Saldo Liquidación por Dificultad
        hardship_payoff_balance_amount = TranslationHelper.create_input_field_with_context(
            'hardship_payoff_balance_amount',
            st.session_state.get('hardship_payoff_balance_amount', 0.0),
            min_value=0.0,
            max_value=500000.0,
            step=1000.0,
            key="hardship_payoff_balance_amount"
        )

        # Interés Devengado Proyectado
        orig_projected_additional_accrued_interest = TranslationHelper.create_input_field_with_context(
            'orig_projected_additional_accrued_interest',
            st.session_state.get('orig_projected_additional_accrued_interest', 0.0),
            min_value=0.0,
            max_value=100000.0,
            step=1000.0,
            key="orig_projected_additional_accrued_interest"
        )

        # Tasa de Interés Anual
        int_rate = TranslationHelper.create_input_field_with_context(
            'int_rate',
            st.session_state.get('int_rate', 6.5),
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key="int_rate"
        )

        # Monto por Dificultad Financiera
        hardship_amount = TranslationHelper.create_input_field_with_context(
            'hardship_amount',
            st.session_state.get('hardship_amount', 0.0),
            min_value=0.0,
            max_value=500000.0,
            step=1000.0,
            key="hardship_amount"
        )

        # Total Recargos por Mora
        total_rec_late_fee = TranslationHelper.create_input_field_with_context(
            'total_rec_late_fee',
            st.session_state.get('total_rec_late_fee', 0.0),
            min_value=0.0,
            max_value=100000.0,
            step=100.0,
            key="total_rec_late_fee"
        )

        # Último Pago por Dificultad
        hardship_last_payment_amount = TranslationHelper.create_input_field_with_context(
            'hardship_last_payment_amount',
            st.session_state.get('hardship_last_payment_amount', 0.0),
            min_value=0.0,
            max_value=100000.0,
            step=1000.0,
            key="hardship_last_payment_amount"
        )

        # Relación Deuda/Ingreso (DTI)
        dti = TranslationHelper.create_input_field_with_context(
            'dti',
            st.session_state.get('dti', 10.0),
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key="dti"
        )

        # Ingreso Anual Bruto
        annual_inc = TranslationHelper.create_input_field_with_context(
            'annual_inc',
            st.session_state.get('annual_inc', 95000.0),
            min_value=0.0,
            max_value=10000000.0,
            step=1000.0,
            key="annual_inc"
        )

        # Utilización de Crédito (Buró)
        bc_util = TranslationHelper.create_input_field_with_context(
            'bc_util',
            st.session_state.get('bc_util', 15.0),
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key="bc_util"
        )

    # Sección de resumen con contexto mexicano
    st.markdown("---")
    st.subheader("📋 Resumen del Perfil - Análisis Mexicano")

    # Crear columnas para resumen
    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        # Evaluación DTI
        dti_value = st.session_state.get('dti', 0)
        if dti_value <= 30:
            dti_status = "🟢 Excelente"
            dti_color = "green"
        elif dti_value <= 40:
            dti_status = "🟡 Adecuado"
            dti_color = "orange"
        elif dti_value <= 50:
            dti_status = "🟠 Limitado"
            dti_color = "darkorange"
        else:
            dti_status = "🔴 Alto Riesgo"
            dti_color = "red"

        st.metric(
            "📊 Relación DTI",
            f"{dti_value:.1f}%",
            delta=dti_status,
            delta_color="off"
        )

        # Barra de progreso DTI
        st.progress(
            min(dti_value / 100, 1.0),
            text=f"Límite recomendado en México: 40%"
        )

    with summary_col2:
        # Evaluación Ingreso
        annual_inc_value = st.session_state.get('annual_inc', 0)
        monthly_inc = annual_inc_value / 12

        if monthly_inc >= 45000:
            inc_status = "🟢 Alto"
        elif monthly_inc >= 25000:
            inc_status = "🟡 Medio-Alto"
        elif monthly_inc >= 12000:
            inc_status = "🟠 Medio"
        else:
            inc_status = "🔴 Bajo"

        st.metric(
            "💰 Ingreso Mensual",
            f"${monthly_inc:,.0f} MXN",
            delta=inc_status,
            delta_color="off"
        )

        # Comparación con salario mínimo
        min_wage = 7486  # Salario mínimo mensual 2024
        if monthly_inc > 0:
            times_min_wage = monthly_inc / min_wage
            st.caption(f"Equivale a {times_min_wage:.1f} veces el salario mínimo")

    with summary_col3:
        # Evaluación Utilización Crédito
        bc_util_value = st.session_state.get('bc_util', 0)

        if bc_util_value <= 30:
            util_status = "🟢 Excelente"
        elif bc_util_value <= 50:
            util_status = "🟡 Adecuado"
        elif bc_util_value <= 75:
            util_status = "🟠 Alto"
        else:
            util_status = "🔴 Muy Alto"

        st.metric(
            "💳 Utilización Crédito",
            f"{bc_util_value:.1f}%",
            delta=util_status,
            delta_color="off"
        )

        # Recomendación Buró de Crédito
        if bc_util_value > 50:
            st.warning("⚠️ Alta utilización puede afectar score Buró")
        else:
            st.success("✅ Nivel saludable según Buró de Crédito")

    # Información sobre perfiles con contexto mexicano
    with st.expander("📋 Guía de Perfiles - Contexto Mexicano", expanded=False):
        st.markdown("""
        ### 🎯 Perfiles de Ejemplo Adaptados a México

        **🟢 RIESGO MÍNIMO (0-20%):**
        - **Perfil:** Cliente premium (ejecutivo, profesionista)
        - **Ingreso:** >$100,000 mensuales
        - **DTI:** <30% (excelente capacidad de pago)
        - **Buró:** Utilización <30%, historial impecable
        - **Contexto mexicano:** Ingresos formales, declaración fiscal al día

        **🟡 RIESGO BAJO (20-40%):**
        - **Perfil:** Cliente sólido (empleado formal, pequeño empresario)
        - **Ingreso:** $25,000 - $100,000 mensuales
        - **DTI:** 30-40% (capacidad adecuada)
        - **Buró:** Utilización 30-50%, historial bueno
        - **Contexto mexicano:** Contrato indefinido, antigüedad laboral >2 años

        **🔴 RIESGO ALTO (40-60%):**
        - **Perfil:** Cliente de alto riesgo (ingresos variables, sector informal)
        - **Ingreso:** <$25,000 mensuales
        - **DTI:** >40% (sobreendeudamiento)
        - **Buró:** Utilización >75%, morosidades
        - **Contexto mexicano:** Ingresos informales, sin comprobantes fiscales

        **⚠️ CONSIDERACIONES ESPECÍFICAS MÉXICO:**
        - **Sector informal:** Representa ~55% de la economía
        - **Ingresos variables:** Comisiones, ventas, trabajos por proyecto
        - **Compensación:** Garantías, avales, seguros de crédito
        - **Regulación:** Límites de usura (CAT máximo no regulado explícitamente)
        """)

        # Tabla comparativa con contexto mexicano
        comparison_data = {
            "Indicador": ["DTI Recomendado", "Utilización Buró Ideal", "Antigüedad Laboral Mínima",
                          "Ingreso Mínimo Formal"],
            "Valor": ["< 40%", "< 50%", "6 meses - 1 año", "3x Salario Mínimo"],
            "Observaciones MX": ["Límite prudencial bancario", "Impacta score Buró", "Estabilidad laboral valorada",
                                 "~$22,400 mensuales"]
        }

        import pandas as pd
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)

    st.markdown("---")

    # Botón de predicción
    if st.button("🎯 Realizar Predicción de Riesgo", type="primary", use_container_width=True, key="predict_button"):
        with st.spinner("Analizando perfil crediticio..."):
            # Recopilar datos actuales del formulario
            input_data = {
                'out_prncp': out_prncp,
                'out_prncp_inv': out_prncp_inv,
                'last_pymnt_amnt': last_pymnt_amnt,
                'total_rec_prncp': total_rec_prncp,
                'recoveries': recoveries,
                'collection_recovery_fee': collection_recovery_fee,
                'total_pymnt': total_pymnt,
                'installment': installment,
                'funded_amnt_inv': funded_amnt_inv,
                'total_pymnt_inv': total_pymnt_inv,
                'total_rec_int': total_rec_int,
                'hardship_payoff_balance_amount': hardship_payoff_balance_amount,
                'orig_projected_additional_accrued_interest': orig_projected_additional_accrued_interest,
                'int_rate': int_rate,
                'hardship_amount': hardship_amount,
                'total_rec_late_fee': total_rec_late_fee,
                'hardship_last_payment_amount': hardship_last_payment_amount,
                'dti': dti,
                'annual_inc': annual_inc,
                'bc_util': bc_util
            }

            # Validar y hacer predicción
            input_data, errors = prediction_manager.validate_input(input_data)

            if errors:
                for error in errors:
                    st.error(error)
            else:
                results = prediction_manager.predict(input_data)

                if results:
                    # Mostrar resultados
                    st.markdown("## 🎯 Resultado del Análisis Crediticio")

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Gráfico de resultados
                        fig = viz_manager.plot_prediction_result(
                            results['probability'],
                            results['decision'],
                            results['risk_level']
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Añadir gráfico de comparación mexicana
                        fig_mx = viz_manager.plot_profile_comparison_mx(input_data)
                        if fig_mx:
                            st.plotly_chart(fig_mx, use_container_width=True)

                    with col2:
                        # Información detallada con contexto mexicano
                        decision_color = "green" if results['decision'] == "APROBADO" else "red"

                        st.markdown(
                            f"### <span style='color:{decision_color}; font-size: 24px;'>{results['decision']}</span>",
                            unsafe_allow_html=True)

                        st.metric(
                            "Probabilidad de Riesgo",
                            f"{results['probability']:.1%}",
                            delta=f"Umbral: {results['threshold']:.1%}",
                            delta_color="off"
                        )

                        st.metric(
                            "Nivel de Riesgo",
                            results['risk_level']
                        )

                        st.metric(
                            "Score de Perfil",
                            f"{results['profile_score']:.0f}/100"
                        )

                        # Interpretación mexicana
                        st.markdown("---")
                        st.subheader("🇲🇽 Interpretación Local")

                        if results['decision'] == "APROBADO":
                            st.success("""
                            **✅ Aprobación Recomendada:**
                            - Perfil alineado con estándares mexicanos
                            - Capacidad de pago verificable
                            - Riesgo dentro de parámetros aceptables
                            """)
                        else:
                            st.error("""
                            **❌ Rechazo Recomendado:**
                            - Perfil fuera de parámetros prudenciales
                            - Riesgo crediticio elevado
                            - Considerar garantías adicionales
                            """)

                    # Guardar en base de datos
                    user = auth_manager.get_current_user()
                    prediction_id = db_manager.save_prediction(
                        user['id'],
                        input_data,
                        results
                    )

                    if prediction_id:
                        st.success(f"✅ Análisis guardado con ID: {prediction_id}")

                    # Información de diagnóstico con contexto mexicano
                    st.markdown("---")
                    st.subheader("🔍 Diagnóstico Detallado - Perspectiva Mexicana")

                    # Mostrar información del modelo
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.info(f"**Modelo:** {model_info.get('type', 'N/A')}")

                    with col2:
                        st.info(f"**Umbral usado:** {results['threshold']:.1%}")

                    with col3:
                        st.info(f"**Predicción raw:** {results.get('prediction_raw', 'N/A')}")

                    # Verificar coherencia con perfil esperado
                    if st.session_state.get('current_profile') in PROFILES:
                        profile = PROFILES[st.session_state.current_profile]
                        expected_result = profile.get('expected_result', 'N/A')
                        expected_prob = profile.get('expected_probability', 'N/A')

                        if expected_result != 'N/A':
                            st.markdown(f"**Resultado esperado para este perfil:** {expected_result} ({expected_prob})")

                            if results['decision'] == expected_result:
                                st.success("✅ Resultado coherente con el perfil")
                            else:
                                st.warning("⚠️ Resultado diferente al esperado para este perfil")

                                # Sugerir ajuste de umbral con contexto mexicano
                                if results['decision'] == "RECHAZADO" and expected_result == "APROBADO":
                                    suggested_threshold = max(0.1, results['probability'] - 0.05)
                                    st.markdown(
                                        f"**Sugerencia:** Para aprobar este perfil en contexto mexicano, reduce el umbral a **{suggested_threshold:.1%}** o menos")
                                elif results['decision'] == "APROBADO" and expected_result == "RECHAZADO":
                                    suggested_threshold = min(0.9, results['probability'] + 0.05)
                                    st.markdown(
                                        f"**Sugerencia:** Para rechazar este perfil considerando estándares mexicanos, aumenta el umbral a **{suggested_threshold:.1%}** o más")

                    # Mostrar análisis de factores con perspectiva mexicana
                    st.markdown("---")
                    st.subheader("📊 Análisis de Factores Clave - Contexto Mexicano")

                    # Función para evaluar factores en contexto mexicano
                    def evaluate_factor_mx(factor, value):
                        """Evaluar un factor individual en contexto mexicano"""
                        if factor == 'out_prncp':
                            if value == 0:
                                return {'status': 'good', 'text': 'Excelente - Sin deuda', 'icon': '✅'}
                            elif value < 10000:
                                return {'status': 'good', 'text': 'Bajo - Buen manejo', 'icon': '👍'}
                            elif value < 50000:
                                return {'status': 'medium', 'text': 'Moderado - Vigilar', 'icon': '⚠️'}
                            else:
                                return {'status': 'bad', 'text': 'Alto - Sobreendeudamiento', 'icon': '❌'}

                        elif factor == 'dti':
                            if value < 30:
                                return {'status': 'good', 'text': 'Excelente - Capacidad sobrada', 'icon': '✅'}
                            elif value < 40:
                                return {'status': 'good', 'text': 'Adecuado - Límite prudencial', 'icon': '👍'}
                            elif value < 50:
                                return {'status': 'medium', 'text': 'Alto - Riesgo moderado', 'icon': '⚠️'}
                            else:
                                return {'status': 'bad', 'text': 'Muy Alto - Sobreendeudamiento', 'icon': '❌'}

                        elif factor == 'int_rate':
                            if value < 15:
                                return {'status': 'good', 'text': 'Muy Baja - Excelente', 'icon': '✅'}
                            elif value < 25:
                                return {'status': 'good', 'text': 'Baja - Competitiva', 'icon': '👍'}
                            elif value < 40:
                                return {'status': 'medium', 'text': 'Media - Estándar mercado', 'icon': '⚠️'}
                            else:
                                return {'status': 'bad', 'text': 'Muy Alta - Riesgo usura', 'icon': '❌'}

                        elif factor == 'bc_util':
                            if value < 30:
                                return {'status': 'good', 'text': 'Excelente - Buró saludable', 'icon': '✅'}
                            elif value < 50:
                                return {'status': 'good', 'text': 'Adecuado - Buen manejo', 'icon': '👍'}
                            elif value < 75:
                                return {'status': 'medium', 'text': 'Alto - Vigilar uso', 'icon': '⚠️'}
                            else:
                                return {'status': 'bad', 'text': 'Muy Alto - Capacidad comprometida', 'icon': '❌'}

                        elif factor == 'annual_inc':
                            monthly = value / 12
                            if monthly >= 45000:
                                return {'status': 'good', 'text': 'Alto - Clase media alta', 'icon': '✅'}
                            elif monthly >= 25000:
                                return {'status': 'good', 'text': 'Medio - Clase media', 'icon': '👍'}
                            elif monthly >= 12000:
                                return {'status': 'medium', 'text': 'Básico - Salario promedio', 'icon': '⚠️'}
                            else:
                                return {'status': 'bad', 'text': 'Bajo - Subsistencia', 'icon': '❌'}

                        elif factor == 'last_pymnt_amnt':
                            if value == 0:
                                return {'status': 'bad', 'text': 'Crítico - Sin pago reciente', 'icon': '❌'}
                            elif value < 500:
                                return {'status': 'medium', 'text': 'Bajo - Pago mínimo', 'icon': '⚠️'}
                            elif value < 2000:
                                return {'status': 'good', 'text': 'Adecuado - Pago regular', 'icon': '👍'}
                            else:
                                return {'status': 'good', 'text': 'Alto - Excelente pago', 'icon': '✅'}

                        else:
                            return {'status': 'neutral', 'text': 'Normal - Sin observaciones', 'icon': '📝'}

                    # Factores clave con valores y evaluación mexicana
                    key_factors = [
                        ('out_prncp', 'Saldo Capital Pendiente', True, '💰'),
                        ('dti', 'Relación DTI', False, '📊'),
                        ('int_rate', 'Tasa de Interés', False, '📈'),
                        ('bc_util', 'Utilización Crédito', False, '💳'),
                        ('annual_inc', 'Ingreso Anual', True, '🏦'),
                        ('last_pymnt_amnt', 'Último Pago', True, '📅')
                    ]

                    cols = st.columns(3)
                    for i, (factor, label, is_money, icon) in enumerate(key_factors):
                        if factor in input_data:
                            with cols[i % 3]:
                                value = input_data[factor]
                                formatted_value = TranslationHelper.format_currency_mx(value, factor)

                                # Evaluación mexicana
                                evaluation = evaluate_factor_mx(factor, value)
                                color_map = {
                                    'good': "normal",
                                    'medium': "off",
                                    'bad': "inverse",
                                    'neutral': "normal"
                                }

                                st.metric(
                                    f"{icon} {label}",
                                    formatted_value,
                                    delta=f"{evaluation['icon']} {evaluation['text']}",
                                    delta_color=color_map[evaluation['status']]
                                )

                    # Mostrar detalles completos
                    with st.expander("📋 Ver detalles completos del análisis"):
                        st.json(results)

                        # Tabla de todos los valores con nombres mexicanos
                        st.subheader("Valores ingresados - Contexto Mexicano")
                        import pandas as pd

                        df_values = pd.DataFrame([
                            {
                                'Característica': TranslationHelper.translate_feature(k),
                                'Variable Original': k,
                                'Valor': TranslationHelper.format_currency_mx(v, k),
                                'Evaluación MX': evaluate_factor_mx(k, v)['text'],
                                'Estado': evaluate_factor_mx(k, v)['icon']
                            }
                            for k, v in input_data.items()
                        ])
                        st.dataframe(df_values, use_container_width=True, hide_index=True)

                        # Explicación del resultado en contexto mexicano
                        st.subheader("💡 Interpretación del Resultado - Perspectiva Mexicana")

                        if results['probability'] < 0.2:
                            st.markdown("""
                            **🟢 RIESGO MÍNIMO (0-20%):**
                            - **Perfil mexicano:** Cliente premium, ingresos formales altos
                            - **Documentación:** Comprobantes fiscales completos, historial Buró impecable
                            - **Recomendación:** Aprobación automática, condiciones preferenciales
                            - **Consideraciones MX:** Ideal para tarjetas platinum, créditos hipotecarios
                            """)
                        elif results['probability'] < 0.4:
                            st.markdown("""
                            **🟡 RIESGO BAJO (20-40%):**
                            - **Perfil mexicano:** Cliente formal estable, empleado o pequeño empresario
                            - **Documentación:** Nóminas, contratos, declaraciones al día
                            - **Recomendación:** Aprobación estándar, revisión de capacidad
                            - **Consideraciones MX:** Mercado objetivo principal de la banca comercial
                            """)
                        else:  # probability >= 0.4
                            st.markdown("""
                            **🔴 RIESGO ALTO (40-100%):**
                            - **Perfil mexicano:** Sector informal, ingresos variables, historial problemático
                            - **Documentación:** Limitada o irregular, posiblemente sin comprobantes fiscales
                            - **Recomendación:** Rechazo o condiciones especiales (garantías, avales, tasas más altas)
                            - **Consideraciones MX:** Mercado de microcrédito, fintechs, créditos con garantía
                            - **Alternativas MX:** Considerar Sofomes, Uniones de Crédito, programas gubernamentales
                            """)

                        # Recomendaciones específicas para México
                        st.subheader("🤝 Recomendaciones - Estrategia Mexicana")

                        if results['decision'] == "APROBADO":
                            st.success("""
                            **Estrategia de Aprobación:**
                            1. **Oferta estándar:** Tasas competitivas del mercado
                            2. **Cross-selling:** Seguros, tarjetas adicionales
                            3. **Límites prudentes:** Basados en capacidad comprobada
                            4. **Seguimiento:** Monitoreo periódico del Buró
                            """)
                        else:
                            st.warning("""
                            **Estrategia Alternativa (si desea proceder):**
                            1. **Garantías adicionales:** Avales con buen historial, garantías prendarias
                            2. **Seguros:** De vida, desempleo, incapacidad
                            3. **Tasas ajustadas:** Primas de riesgo justificadas
                            4. **Plazos cortos:** Reducción de exposición
                            5. **Programas especiales:** Reestructuración, pagos graduales

                            **Instituciones alternativas en México:**
                            • **Sofomes:** Sociedades Financieras de Objeto Múltiple
                            • **Sofipos:** Sociedades Financieras Populares
                            • **Uniones de Crédito:** Cooperativas de ahorro y préstamo
                            • **Programas gubernamentales:** Nacional Financiera, Fondos de garantía
                            """)


def show_analysis_page():
    """Mostrar página de análisis"""
    st.title("📈 Análisis de Predicción")
    st.markdown("---")

    # Verificar si hay predicciones recientes
    user = auth_manager.get_current_user()
    predictions = db_manager.get_user_predictions(user['id'], limit=1)

    if predictions.empty:
        st.info("ℹ️ Realice una predicción primero para ver los análisis")
        return

    # Obtener última predicción
    last_prediction = predictions.iloc[0]

    # Obtener detalles completos
    details = db_manager.get_prediction_details(last_prediction['id'], user['id'])

    if not details:
        st.error("❌ No se pudieron obtener los detalles de la predicción")
        return

    # Convertir detalles JSON
    try:
        details_json = json.loads(details['details_json'])
        input_data = details_json.get('feature_values', {})
    except:
        input_data = {}

    # Mostrar análisis en pestañas
    tab1, tab2, tab3 = st.tabs(["📊 Factores Clave", "📈 Comparación", "🔍 Explicación"])

    with tab1:
        # Importancia de características
        model_info = prediction_manager.get_model_info()
        feature_importance = model_info.get('feature_importance', {})

        if feature_importance:
            fig = viz_manager.plot_feature_importance(feature_importance)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ No hay información de importancia de características disponible")

    with tab2:
        # Comparación con referencias
        if input_data:
            fig = viz_manager.plot_profile_comparison(input_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            # Tabla de valores
            st.subheader("Valores Ingresados")
            df_display = pd.DataFrame([{
                'Característica': viz_manager.get_friendly_name(k),
                'Valor': f"${v:,.2f}" if any(
                    keyword in k for keyword in ['amnt', 'inc', 'prncp', 'pymnt', 'recovery', 'fee', 'balance'])
                else f"{v:.1f}%" if any(keyword in k for keyword in ['rate', 'util', 'dti'])
                else f"{v:.2f}"
            } for k, v in input_data.items()])

            st.dataframe(df_display, use_container_width=True)

    with tab3:
        # Explicación del modelo (igual que Tkinter)
        st.markdown("""
        ### 🔍 Explicación del Modelo Random Forest (Igual que Tkinter)

        **🎯 CARACTERÍSTICAS DEL MODELO:**
        - **Algoritmo:** Random Forest (Bosque Aleatorio)
        - **Tipo:** Ensemble de árboles de decisión
        - **Objetivo:** Clasificación binaria (Aprobado/Rechazado)

        **📊 INTERPRETACIÓN DE RESULTADOS (igual que Tkinter):**

        **1. PROBABILIDAD DE RIESGO:**
        - **0-20%:** 🟢 RIESGO MÍNIMO - Aprobación automática
        - **20-40%:** 🟡 RIESGO BAJO - Aprobación estándar
        - **40-100%:** 🔴 RIESGO ALTO - Rechazo recomendado

        **2. FACTORES CLAVE IDENTIFICADOS:**
        - **Principal pendiente:** Indica cuánto capital sigue debiendo el solicitante
        - **Relación Deuda/Ingreso (DTI):** Porcentaje del ingreso destinado a pagar deudas
        - **Tasa de interés:** Tasa aplicada al crédito (mayor tasa = mayor riesgo percibido)
        - **Utilización de crédito:** Porcentaje del límite de crédito utilizado
        - **Historial de pagos:** Montos de pagos anteriores y recuperaciones

        **⚙️ UMBRAL AJUSTABLE (igual que Tkinter):**
        - El umbral de decisión puede ajustarse de 0.1 a 0.9
        - Umbral más bajo = Más aprobaciones (pero más riesgo potencial)
        - Umbral más alto = Menos aprobaciones (pero menos riesgo)
        - **Valor por defecto:** 40%

        **⚠️ CONSIDERACIONES IMPORTANTES:**
        - Este modelo fue entrenado con datos balanceados
        - Se recomienda validación humana para casos límite
        - Los resultados deben considerarse como una herramienta de apoyo a la decisión
        """)


def show_history_page():
    """Mostrar página de historial"""
    st.title("📋 Historial de Predicciones")
    st.markdown("---")

    user = auth_manager.get_current_user()

    # Obtener historial
    with st.spinner("Cargando historial..."):
        predictions = db_manager.get_user_predictions(user['id'], limit=100)

    if predictions.empty:
        st.info("ℹ️ No hay predicciones registradas")
        return

    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Predicciones", len(predictions))

    with col2:
        approved = len(predictions[predictions['decision'] == 'APROBADO'])
        st.metric("Aprobados", approved)

    with col3:
        avg_risk = predictions['risk_probability'].mean() * 100
        st.metric("Riesgo Promedio", f"{avg_risk:.1f}%")

    with col4:
        latest_date = predictions['created_at'].max()
        st.metric("Última Predicción", latest_date.strftime("%d/%m/%Y"))

    st.markdown("---")

    # Gráfico de evolución
    st.subheader("📈 Evolución de Predicciones")
    fig = viz_manager.plot_prediction_history(predictions)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabla de historial
    st.subheader("📋 Detalle de Predicciones")

    # Formatear DataFrame para visualización
    df_display = predictions.copy()
    df_display['created_at'] = pd.to_datetime(df_display['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    df_display['risk_probability'] = df_display['risk_probability'].apply(lambda x: f"{x:.1%}")
    df_display['out_prncp'] = df_display['out_prncp'].apply(lambda x: f"${x:,.2f}")
    df_display['annual_inc'] = df_display['annual_inc'].apply(lambda x: f"${x:,.2f}")

    # Mostrar tabla
    st.dataframe(
        df_display[[
            'created_at', 'decision', 'risk_level', 'risk_probability',
            'out_prncp', 'dti', 'annual_inc'
        ]],
        use_container_width=True,
        hide_index=True
    )

    # Selector para ver detalles de una predicción específica
    st.markdown("---")
    st.subheader("🔍 Ver Detalles de Predicción")

    prediction_ids = predictions['id'].tolist()
    selected_id = st.selectbox(
        "Seleccione una predicción para ver detalles completos",
        prediction_ids,
        format_func=lambda
            x: f"Predicción ID: {x} - {predictions[predictions['id'] == x]['created_at'].iloc[0].strftime('%Y-%m-%d %H:%M')}"
    )

    if selected_id:
        details = db_manager.get_prediction_details(selected_id, user['id'])
        if details:
            with st.expander("📋 Detalles completos"):
                st.json(details)


def show_configuration_page():
    """Mostrar página de configuración - VERSIÓN REAL"""
    st.title("⚙️ Configuración del Sistema")
    st.markdown("---")

    # Sección de modelo
    st.header("🤖 Configuración del Modelo")

    # Umbral de decisión (igual que Tkinter: 0.1 a 0.9)
    current_threshold = prediction_manager.threshold
    new_threshold = st.slider(
        "Umbral de Decisión",
        min_value=0.1,
        max_value=0.9,
        value=float(current_threshold),
        step=0.05,
        format="%.2f",
        help="Probabilidad mínima para clasificar como 'RECHAZADO' (igual que Tkinter)"
    )

    if new_threshold != current_threshold:
        prediction_manager.set_threshold(new_threshold)
        st.success(f"✅ Umbral actualizado a {new_threshold:.1%}")

    st.markdown("---")

    # Configuración de usuario - PERFIL
    st.header("👤 Configuración de Perfil")

    user = auth_manager.get_current_user()

    # Pestañas para Configuración de Usuario
    profile_tab, password_tab = st.tabs(["📝 Perfil", "🔐 Contraseña"])

    with profile_tab:
        with st.form("user_profile_form"):
            st.subheader("Información Personal")

            current_name = st.text_input(
                "Nombre Completo",
                value=user['full_name'],
                help="Su nombre completo para identificar su cuenta"
            )

            current_email = st.text_input(
                "Email",
                value=user['email'],
                disabled=True,
                help="El email no se puede modificar por seguridad"
            )

            submitted = st.form_submit_button("💾 Guardar Cambios de Perfil")

            if submitted:
                if not current_name or len(current_name.strip()) < 3:
                    st.error("❌ El nombre debe tener al menos 3 caracteres")
                else:
                    success, message = auth_manager.update_profile(
                        user['id'],
                        current_name.strip()
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with password_tab:
        with st.form("change_password_form"):
            st.subheader("Cambiar Contraseña")
            st.info("🔒 Para mayor seguridad, la contraseña debe tener al menos 8 caracteres")

            current_password = st.text_input(
                "Contraseña Actual",
                type="password",
                help="Ingrese su contraseña actual para verificar su identidad"
            )

            new_password = st.text_input(
                "Nueva Contraseña",
                type="password",
                help="La nueva contraseña debe tener al menos 8 caracteres"
            )

            confirm_password = st.text_input(
                "Confirmar Nueva Contraseña",
                type="password",
                help="Vuelva a ingresar la nueva contraseña"
            )

            # Indicador de fortaleza de contraseña
            if new_password:
                strength = 0
                if len(new_password) >= 8:
                    strength += 1
                if any(c.isupper() for c in new_password):
                    strength += 1
                if any(c.islower() for c in new_password):
                    strength += 1
                if any(c.isdigit() for c in new_password):
                    strength += 1
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password):
                    strength += 1

                if strength == 1:
                    st.warning("🔶 Contraseña débil")
                elif strength in [2, 3]:
                    st.info("🔷 Contraseña moderada")
                elif strength >= 4:
                    st.success("🔷 Contraseña fuerte")

            submitted_pw = st.form_submit_button("🔐 Cambiar Contraseña")

            if submitted_pw:
                if not all([current_password, new_password, confirm_password]):
                    st.error("❌ Complete todos los campos")
                else:
                    success, message = auth_manager.update_password(
                        user['id'],
                        current_password,
                        new_password,
                        confirm_password
                    )
                    if success:
                        st.success(message)
                        # Limpiar campos
                        st.session_state.password_changed = True
                        st.rerun()
                    else:
                        st.error(message)

    st.markdown("---")

    # Información del sistema
    st.header("ℹ️ Información del Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Base de Datos")
        if db_manager.test_connection():
            st.success("✅ Conectado")
            # Mostrar información de conexión básica
            with st.expander("Ver detalles de conexión"):
                #st.write(f"**Servidor:** {db_manager.server}")
                st.write(f"**Servidor (Host):** {db_manager.host}")
                st.write(f"**Base de datos:** {db_manager.database}")
                st.write(f"**Usuario:** {db_manager.username}")
        else:
            st.error("❌ No conectado")

    with col2:
        st.subheader("Modelo")
        model_info = prediction_manager.get_model_info()
        st.info(f"""
        - **Tipo:** {model_info.get('type', 'N/A')}
        - **Características:** {model_info.get('n_features', 'N/A')}
        - **Estado:** {'✅ Cargado' if prediction_manager.model else '❌ No cargado'}
        - **Umbral actual:** {prediction_manager.threshold:.1%}
        """)

        # Botón para recargar modelo
        if st.button("🔄 Recargar Modelo", use_container_width=True):
            with st.spinner("Recargando modelo..."):
                if prediction_manager.load_model():
                    st.success("✅ Modelo recargado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al recargar el modelo")

    st.markdown("---")

    # Sección de peligro (operaciones críticas)
    st.header("⚠️ Zona de Peligro")

    with st.expander("Operaciones Avanzadas"):
        st.warning("⚠️ Estas operaciones son irreversibles")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Limpiar Historial", use_container_width=True):
                st.warning("Esta funcionalidad aún no está implementada")
                # Aquí puedes agregar la lógica para limpiar el historial

        with col2:
            if st.button("📤 Exportar Datos", use_container_width=True):
                st.warning("Esta funcionalidad aún no está implementada")
                # Aquí puedes agregar la lógica para exportar datos

        # Información de cuenta
        st.subheader("Información de Cuenta")
        st.write(f"**ID de usuario:** {user['id']}")
        st.write(f"**Fecha de registro:** No disponible")  # Puedes agregar este campo a la BD

        # Botón para eliminar cuenta (con confirmación)
        delete_confirmed = st.checkbox("Entiendo que esta acción es irreversible")

        if st.button("🗑️ Eliminar Mi Cuenta",
                     disabled=not delete_confirmed,
                     type="secondary",
                     use_container_width=True):
            st.error("❌ Esta funcionalidad aún no está implementada")
            # Aquí puedes agregar la lógica para eliminar la cuenta

    # Puedes agregar esto en la sección de cambiar contraseña
    def check_password_strength(password):
        """Verificar fortaleza de la contraseña"""
        if not password:
            return 0, "Ingrese una contraseña"

        score = 0
        messages = []

        # Longitud
        if len(password) >= 8:
            score += 1
        else:
            messages.append("❌ Al menos 8 caracteres")

        # Mayúsculas
        if any(c.isupper() for c in password):
            score += 1
        else:
            messages.append("❌ Al menos una mayúscula")

        # Minúsculas
        if any(c.islower() for c in password):
            score += 1
        else:
            messages.append("❌ Al menos una minúscula")

        # Números
        if any(c.isdigit() for c in password):
            score += 1
        else:
            messages.append("❌ Al menos un número")

        # Caracteres especiales
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            messages.append("❌ Al menos un carácter especial")

        return score, messages

    # Luego en la interfaz:
    if new_password:
        score, messages = check_password_strength(new_password)

        progress_bar = st.progress(score / 5)

        if score == 0:
            st.error("Contraseña muy débil")
        elif score <= 2:
            st.warning("Contraseña débil")
        elif score <= 4:
            st.info("Contraseña buena")
        else:
            st.success("Contraseña excelente")

        for msg in messages:
            st.caption(msg)



# Punto de entrada principal
def main():
    """Función principal de la aplicación"""

    # Inicializar session_state primero
    initialize_session_state()

    # Verificar autenticación
    if not auth_manager.is_authenticated():
        show_login_page()
    else:
        show_main_page()


if __name__ == "__main__":
    main()