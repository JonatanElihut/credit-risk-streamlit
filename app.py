"""
app.py — Sistema de Predicción de Riesgo Crediticio
Versión adaptada para usuario final sin conocimientos financieros.

MEJORAS INCLUIDAS:
- Monto del préstamo solicitado
- Plazo en meses (6-60 meses)
- Tasa de interés anual visible y editable
- CAT (Costo Anual Total) estimado
- Mensualidad calculada automáticamente
- Intereses totales visibles
- Mapeo correcto al modelo (funded_amnt_inv, int_rate)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import json

st.set_page_config(
    page_title="🏦 Simulador de Crédito",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.auth import auth_manager
from utils.database import db_manager
from utils.prediction import prediction_manager
from utils.visualization import viz_manager
from utils.translation_helper import TranslationHelper

# ---------------------------------------------------------------------------
# CONSTANTES Y VALORES POR DEFECTO
# ---------------------------------------------------------------------------

FEATURE_KEYS = [
    'out_prncp', 'out_prncp_inv', 'last_pymnt_amnt', 'total_rec_prncp',
    'recoveries', 'collection_recovery_fee', 'total_pymnt', 'installment',
    'funded_amnt_inv', 'total_pymnt_inv', 'total_rec_int',
    'hardship_payoff_balance_amount', 'orig_projected_additional_accrued_interest',
    'int_rate', 'hardship_amount', 'total_rec_late_fee',
    'hardship_last_payment_amount', 'dti', 'annual_inc', 'bc_util'
]

DEFAULT_VALUES = {
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
    'int_rate': 18.0,  # Tasa por defecto actualizada
    'hardship_amount': 0.0,
    'total_rec_late_fee': 0.0,
    'hardship_last_payment_amount': 0.0,
    'dti': 10.0,
    'annual_inc': 95000.0,
    'bc_util': 15.0
}

# Perfiles actualizados con monto, plazo y tasa
PROFILES = {
    "minimal": {
        'name': "🟢 Riesgo mínimo (0–20%)",
        'values': {
            'out_prncp': 0.0, 'out_prncp_inv': 0.0, 'last_pymnt_amnt': 450.0,
            'total_rec_prncp': 9800.0, 'recoveries': 0.0, 'collection_recovery_fee': 0.0,
            'total_pymnt': 10500.0, 'installment': 300.0, 'funded_amnt_inv': 10000.0,
            'total_pymnt_inv': 10500.0, 'total_rec_int': 700.0,
            'hardship_payoff_balance_amount': 0.0,
            'orig_projected_additional_accrued_interest': 0.0,
            'int_rate': 12.0, 'hardship_amount': 0.0, 'total_rec_late_fee': 0.0,
            'hardship_last_payment_amount': 0.0, 'dti': 8.5,
            'annual_inc': 120000.0, 'bc_util': 15.5
        },
        'loan_amount': 50000,
        'loan_term': 24,
        'interest_rate': 12.0,
        'expected_result': "APROBADO",
        'description': "Perfil premium — ingresos altos, sin deudas pendientes"
    },
    "low": {
        'name': "🟡 Riesgo bajo (20–40%)",
        'values': {
            'out_prncp': 500.0, 'out_prncp_inv': 400.0, 'last_pymnt_amnt': 350.0,
            'total_rec_prncp': 4500.0, 'recoveries': 0.0, 'collection_recovery_fee': 0.0,
            'total_pymnt': 5000.0, 'installment': 250.0, 'funded_amnt_inv': 8000.0,
            'total_pymnt_inv': 5000.0, 'total_rec_int': 500.0,
            'hardship_payoff_balance_amount': 0.0,
            'orig_projected_additional_accrued_interest': 0.0,
            'int_rate': 16.0, 'hardship_amount': 0.0, 'total_rec_late_fee': 0.0,
            'hardship_last_payment_amount': 0.0, 'dti': 12.5,
            'annual_inc': 85000.0, 'bc_util': 25.5
        },
        'loan_amount': 30000,
        'loan_term': 18,
        'interest_rate': 16.0,
        'expected_result': "APROBADO",
        'description': "Perfil sólido — empleado formal con historial limpio"
    },
    "high": {
        'name': "🔴 Riesgo alto (40–60%)",
        'values': {
            'out_prncp': 6000.0, 'out_prncp_inv': 5500.0, 'last_pymnt_amnt': 100.0,
            'total_rec_prncp': 800.0, 'recoveries': 500.0, 'collection_recovery_fee': 75.0,
            'total_pymnt': 1200.0, 'installment': 450.0, 'funded_amnt_inv': 15000.0,
            'total_pymnt_inv': 1200.0, 'total_rec_int': 100.0,
            'hardship_payoff_balance_amount': 2500.0,
            'orig_projected_additional_accrued_interest': 300.0,
            'int_rate': 32.0, 'hardship_amount': 3000.0, 'total_rec_late_fee': 50.0,
            'hardship_last_payment_amount': 100.0, 'dti': 38.5,
            'annual_inc': 45000.0, 'bc_util': 75.5
        },
        'loan_amount': 80000,
        'loan_term': 36,
        'interest_rate': 32.0,
        'expected_result': "RECHAZADO",
        'description': "Perfil de riesgo — sobreendeudamiento, historial problemático"
    },
    "default": {
        'name': "⚙️ Valores predeterminados",
        'values': DEFAULT_VALUES.copy(),
        'loan_amount': 20000,
        'loan_term': 12,
        'interest_rate': 18.0,
        'expected_result': "APROBADO",
        'description': "Valores iniciales del sistema"
    }
}


# ---------------------------------------------------------------------------
# FUNCIONES FINANCIERAS
# ---------------------------------------------------------------------------

def obtener_tasa_estimada(dti, bc_util, ingreso_mensual, monto_prestamo, plazo_meses):
    """
    Estima una tasa de interés basada en el perfil de riesgo del usuario.
    Considera DTI, uso de crédito, ingreso, monto y plazo.

    Returns:
        float: Tasa anual estimada (%)
    """
    # Base inicial (tasa base del mercado mexicano para créditos personales 2024-2025)
    tasa_base = 18.0

    # 1. Ajuste por DTI (deuda vs ingreso)
    if dti < 15:
        tasa_base -= 4  # Excelente capacidad
    elif dti < 30:
        tasa_base -= 2  # Buen perfil
    elif dti < 40:
        tasa_base += 1  # Riesgo moderado
    elif dti < 50:
        tasa_base += 4  # Riesgo alto
    else:
        tasa_base += 8  # Riesgo extremo

    # 2. Ajuste por bc_util (uso de crédito en buró)
    if bc_util < 30:
        tasa_base -= 3  # Saludable
    elif bc_util < 50:
        tasa_base -= 1  # Moderado
    elif bc_util < 75:
        tasa_base += 2  # Elevado
    else:
        tasa_base += 6  # Comprometido

    # 3. Ajuste por ingreso mensual
    if ingreso_mensual > 50000:
        tasa_base -= 3  # Alto ingreso
    elif ingreso_mensual > 25000:
        tasa_base -= 1  # Ingreso medio-alto
    elif ingreso_mensual < 15000:
        tasa_base += 3  # Ingreso bajo
    elif ingreso_mensual < 10000:
        tasa_base += 6  # Ingreso muy bajo

    # 4. Ajuste por monto del préstamo
    if monto_prestamo > 200000:
        tasa_base += 3
    elif monto_prestamo > 100000:
        tasa_base += 1
    elif monto_prestamo < 20000:
        tasa_base -= 1

    # 5. Ajuste por plazo
    if plazo_meses > 36:
        tasa_base += 2
    elif plazo_meses > 24:
        tasa_base += 1
    elif plazo_meses <= 12:
        tasa_base -= 1

    # Límites realistas para México
    tasa_base = max(9.0, min(65.0, tasa_base))

    return round(tasa_base, 1)


def calcular_mensualidad(monto, plazo_meses, tasa_anual_porcentaje):
    """
    Calcula la mensualidad de un préstamo usando fórmula de interés compuesto.

    Args:
        monto (float): Monto del préstamo
        plazo_meses (int): Plazo en meses
        tasa_anual_porcentaje (float): Tasa de interés anual (%)

    Returns:
        float: Mensualidad
    """
    if plazo_meses <= 0 or monto <= 0:
        return 0.0

    tasa_mensual = (tasa_anual_porcentaje / 100) / 12

    if tasa_mensual == 0:
        return monto / plazo_meses

    # Fórmula: P = [r * PV] / [1 - (1 + r)^(-n)]
    mensualidad = (tasa_mensual * monto) / (1 - (1 + tasa_mensual) ** (-plazo_meses))

    return round(mensualidad, 2)


def calcular_cat_estimado(tasa_anual, monto, plazo_meses):
    """
    Calcula un CAT estimado (Costo Anual Total) incluyendo comisiones típicas.
    En México, el CAT suele ser 2-5% más alto que la tasa de interés.
    """
    # Comisiones típicas en México
    comision_apertura_porcentaje = 2.0  # 2% del monto
    comision_anual_porcentaje = 0.5  # 0.5% anual

    # Cálculo simplificado del CAT
    ajuste_anual = comision_anual_porcentaje
    ajuste_apertura = (comision_apertura_porcentaje * 12) / plazo_meses

    cat_estimado = tasa_anual + ajuste_anual + ajuste_apertura

    # El CAT no puede ser más del 50% superior a la tasa
    return round(min(cat_estimado, tasa_anual * 1.5), 1)


def calcular_intereses_totales(monto, plazo_meses, tasa_anual_porcentaje):
    """Calcula el total de intereses pagados durante la vida del préstamo"""
    mensualidad = calcular_mensualidad(monto, plazo_meses, tasa_anual_porcentaje)
    total_pagado = mensualidad * plazo_meses
    intereses = total_pagado - monto
    return max(0, round(intereses, 2))


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

def initialize_session_state():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'form_initialized' not in st.session_state:
        st.session_state.form_initialized = False
    if 'password_changed' not in st.session_state:
        st.session_state.password_changed = False
    if 'tiene_historial' not in st.session_state:
        st.session_state.tiene_historial = False
    if 'tuvo_cobranza' not in st.session_state:
        st.session_state.tuvo_cobranza = False
    # Campos del préstamo
    if 'loan_amount' not in st.session_state:
        st.session_state.loan_amount = 20000.0
    if 'loan_term' not in st.session_state:
        st.session_state.loan_term = 12
    if 'user_interest_rate' not in st.session_state:
        st.session_state.user_interest_rate = 18.0
    if 'use_suggested_rate' not in st.session_state:
        st.session_state.use_suggested_rate = True


def init_form_values():
    """Inicializar los campos del formulario en session_state si aún no existen."""
    if not st.session_state.form_initialized:
        for key, value in DEFAULT_VALUES.items():
            st.session_state[key] = value
        st.session_state.form_initialized = True
        st.session_state.current_profile = "default"
        st.session_state.loan_amount = 20000.0
        st.session_state.loan_term = 12
        st.session_state.user_interest_rate = 18.0
        st.session_state.use_suggested_rate = True


# ---------------------------------------------------------------------------
# HELPER: INYECTAR CAMPOS OCULTOS
# ---------------------------------------------------------------------------

def inject_hidden_fields():
    """
    Calcula y escribe en session_state los campos que el modelo necesita.
    IMPORTANTE:
    - funded_amnt_inv = monto del préstamo
    - int_rate = tasa de interés seleccionada por el usuario
    - installment = mensualidad calculada (o la que el usuario puede pagar)
    """
    loan_amount = st.session_state.get('loan_amount', 20000.0)
    loan_term = st.session_state.get('loan_term', 12)
    interest_rate = st.session_state.get('user_interest_rate', 18.0)
    installment = st.session_state.get('installment', 0.0)
    annual_inc = st.session_state.get('annual_inc', 95000.0)
    recoveries = st.session_state.get('recoveries', 0.0)
    out_prncp = st.session_state.get('out_prncp', 0.0)
    last_pymnt_amnt = st.session_state.get('last_pymnt_amnt', 0.0)
    dti = st.session_state.get('dti', 10.0)
    bc_util = st.session_state.get('bc_util', 15.0)

    # ============================================================
    # CAMPOS CLAVE PARA EL MODELO
    # ============================================================
    st.session_state['funded_amnt_inv'] = loan_amount
    st.session_state['int_rate'] = interest_rate

    # Si el usuario no especificó mensualidad, calcularla
    if installment == 0 or installment is None:
        installment = calcular_mensualidad(loan_amount, loan_term, interest_rate)
        st.session_state['installment'] = installment

    # Derivados basados en el préstamo
    total_pagado_estimado = installment * loan_term
    st.session_state['total_pymnt'] = round(total_pagado_estimado, 2)
    st.session_state['total_pymnt_inv'] = round(total_pagado_estimado, 2)

    # Otros derivados
    st.session_state['out_prncp_inv'] = round(out_prncp * 0.9, 2)
    st.session_state['total_rec_prncp'] = round(max(0.0, (annual_inc * 0.1) - out_prncp), 2)
    st.session_state['total_rec_int'] = round(interest_rate * installment / 100, 2)
    st.session_state['collection_recovery_fee'] = round(recoveries * 0.25, 2)

    # Campos siempre en cero
    st.session_state['hardship_payoff_balance_amount'] = 0.0
    st.session_state['hardship_amount'] = 0.0
    st.session_state['hardship_last_payment_amount'] = 0.0
    st.session_state['orig_projected_additional_accrued_interest'] = 0.0
    st.session_state['total_rec_late_fee'] = 0.0


# ---------------------------------------------------------------------------
# HELPER: EVALUACIÓN DE FACTORES
# ---------------------------------------------------------------------------

def evaluate_factor(factor, value):
    """Devuelve dict con status, text e icon para un campo dado."""
    if factor == 'out_prncp':
        if value == 0:
            return {'status': 'good', 'text': 'Sin deuda pendiente', 'icon': '✅'}
        elif value < 10000:
            return {'status': 'good', 'text': 'Saldo bajo — buen manejo', 'icon': '👍'}
        elif value < 50000:
            return {'status': 'medium', 'text': 'Saldo moderado — vigilar', 'icon': '⚠️'}
        else:
            return {'status': 'bad', 'text': 'Saldo alto — sobreendeudamiento', 'icon': '❌'}
    elif factor == 'dti':
        if value < 30:
            return {'status': 'good', 'text': 'Excelente — capacidad de sobra', 'icon': '✅'}
        elif value < 40:
            return {'status': 'good', 'text': 'Adecuado — dentro del límite', 'icon': '👍'}
        elif value < 50:
            return {'status': 'medium', 'text': 'Limitado — riesgo moderado', 'icon': '⚠️'}
        else:
            return {'status': 'bad', 'text': 'Muy alto — sobreendeudamiento', 'icon': '❌'}
    elif factor == 'int_rate':
        if value < 15:
            return {'status': 'good', 'text': 'Tasa baja — muy competitiva', 'icon': '✅'}
        elif value < 25:
            return {'status': 'good', 'text': 'Tasa estándar del mercado', 'icon': '👍'}
        elif value < 40:
            return {'status': 'medium', 'text': 'Tasa alta — riesgo elevado', 'icon': '⚠️'}
        else:
            return {'status': 'bad', 'text': 'Tasa muy alta', 'icon': '❌'}
    elif factor == 'bc_util':
        if value < 30:
            return {'status': 'good', 'text': 'Buró saludable', 'icon': '✅'}
        elif value < 50:
            return {'status': 'good', 'text': 'Uso moderado', 'icon': '👍'}
        elif value < 75:
            return {'status': 'medium', 'text': 'Uso elevado — vigilar', 'icon': '⚠️'}
        else:
            return {'status': 'bad', 'text': 'Capacidad comprometida', 'icon': '❌'}
    elif factor == 'annual_inc':
        monthly = value / 12
        if monthly >= 45000:
            return {'status': 'good', 'text': 'Ingreso alto', 'icon': '✅'}
        elif monthly >= 25000:
            return {'status': 'good', 'text': 'Ingreso clase media', 'icon': '👍'}
        elif monthly >= 12000:
            return {'status': 'medium', 'text': 'Ingreso básico', 'icon': '⚠️'}
        else:
            return {'status': 'bad', 'text': 'Ingreso muy bajo', 'icon': '❌'}
    elif factor == 'last_pymnt_amnt':
        if value == 0:
            return {'status': 'bad', 'text': 'Sin pago reciente', 'icon': '❌'}
        elif value < 500:
            return {'status': 'medium', 'text': 'Pago parcial', 'icon': '⚠️'}
        else:
            return {'status': 'good', 'text': 'Pago regular', 'icon': '✅'}
    elif factor == 'recoveries':
        if value == 0:
            return {'status': 'good', 'text': 'Sin cobranza previa', 'icon': '✅'}
        elif value < 500:
            return {'status': 'medium', 'text': 'Cobranza menor', 'icon': '⚠️'}
        else:
            return {'status': 'bad', 'text': 'Cobranza significativa', 'icon': '❌'}
    else:
        return {'status': 'neutral', 'text': 'Normal', 'icon': '📝'}


# ---------------------------------------------------------------------------
# PÁGINA DE LOGIN / REGISTRO
# ---------------------------------------------------------------------------

def show_login_page():
    st.title("🏦 Simulador de Crédito")
    st.markdown("Evalúa tu solicitud de préstamo de forma rápida y sencilla.")
    st.markdown("---")

    with st.spinner("Verificando conexión..."):
        if not db_manager.test_connection():
            st.error("❌ No se pudo conectar a la base de datos. Verifica tu archivo .env")
            st.stop()

    tab1, tab2 = st.tabs(["🔐 Iniciar sesión", "📝 Crear cuenta"])

    with tab1:
        st.subheader("Bienvenido de vuelta")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            if submit:
                if not email or not password:
                    st.error("❌ Por favor completa todos los campos")
                else:
                    success, message = auth_manager.login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab2:
        st.subheader("Crea tu cuenta")
        with st.form("register_form"):
            full_name = st.text_input("Nombre completo")
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar contraseña", type="password")
            submit = st.form_submit_button("Registrarme", use_container_width=True)
            if submit:
                if not all([full_name, email, password, confirm_password]):
                    st.error("❌ Por favor completa todos los campos")
                else:
                    success, message = auth_manager.register_user(
                        email, full_name, password, confirm_password
                    )
                    if success:
                        st.success(message)
                        st.info("✅ Ahora puedes iniciar sesión")
                    else:
                        st.error(message)


# ---------------------------------------------------------------------------
# BARRA LATERAL + NAVEGACIÓN
# ---------------------------------------------------------------------------

def show_sidebar(user):
    with st.sidebar:
        st.markdown(f"### 👋 Hola, {user['full_name'].split()[0]}")
        st.caption(user['email'])
        st.markdown("---")

        st.markdown("**Menú**")
        page = st.selectbox(
            "Ir a",
            ["📊 Simulación", "📈 Análisis", "📋 Historial", "⚙️ Configuración"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        model_info = prediction_manager.get_model_info()
        st.caption(f"Modelo: {model_info.get('type', 'Random Forest')}")
        st.caption(f"Umbral: {prediction_manager.threshold:.0%}")

        if st.checkbox("Ver detalle del modelo"):
            st.json(model_info.get('hyperparameters', {}))

        st.markdown("---")
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            auth_manager.logout()
            st.rerun()

    return page


# ---------------------------------------------------------------------------
# PÁGINA PRINCIPAL
# ---------------------------------------------------------------------------

def show_main_page():
    user = auth_manager.get_current_user()
    page = show_sidebar(user)

    if page == "📊 Simulación":
        show_prediction_page()
    elif page == "📈 Análisis":
        show_analysis_page()
    elif page == "📋 Historial":
        show_history_page()
    elif page == "⚙️ Configuración":
        show_configuration_page()


# ---------------------------------------------------------------------------
# PÁGINA DE PREDICCIÓN — FORMULARIO COMPLETO
# ---------------------------------------------------------------------------

def show_prediction_page():
    st.title("📊 Simulación de crédito")
    st.markdown("Responde estas preguntas con honestidad. Solo te tomará 2 minutos.")
    st.markdown("---")

    init_form_values()

    # -----------------------------------------------------------------------
    # PERFILES DE PRUEBA
    # -----------------------------------------------------------------------
    with st.expander("🧪 Cargar perfil de prueba", expanded=False):
        st.caption("Útil para probar el sistema con datos de ejemplo.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🟢 Riesgo mínimo", use_container_width=True):
                profile = PROFILES["minimal"]
                for k, v in profile['values'].items():
                    st.session_state[k] = v
                st.session_state.loan_amount = profile['loan_amount']
                st.session_state.loan_term = profile['loan_term']
                st.session_state.user_interest_rate = profile['interest_rate']
                st.session_state.current_profile = "minimal"
                st.session_state.tiene_historial = True
                st.session_state.tuvo_cobranza = False
                st.rerun()
        with col2:
            if st.button("🟡 Riesgo bajo", use_container_width=True):
                profile = PROFILES["low"]
                for k, v in profile['values'].items():
                    st.session_state[k] = v
                st.session_state.loan_amount = profile['loan_amount']
                st.session_state.loan_term = profile['loan_term']
                st.session_state.user_interest_rate = profile['interest_rate']
                st.session_state.current_profile = "low"
                st.session_state.tiene_historial = True
                st.session_state.tuvo_cobranza = False
                st.rerun()
        with col3:
            if st.button("🔴 Riesgo alto", use_container_width=True):
                profile = PROFILES["high"]
                for k, v in profile['values'].items():
                    st.session_state[k] = v
                st.session_state.loan_amount = profile['loan_amount']
                st.session_state.loan_term = profile['loan_term']
                st.session_state.user_interest_rate = profile['interest_rate']
                st.session_state.current_profile = "high"
                st.session_state.tiene_historial = True
                st.session_state.tuvo_cobranza = True
                st.rerun()
        with col4:
            if st.button("⚙️ Predeterminados", use_container_width=True):
                profile = PROFILES["default"]
                for k, v in profile['values'].items():
                    st.session_state[k] = v
                st.session_state.loan_amount = profile['loan_amount']
                st.session_state.loan_term = profile['loan_term']
                st.session_state.user_interest_rate = profile['interest_rate']
                st.session_state.current_profile = "default"
                st.session_state.tiene_historial = False
                st.session_state.tuvo_cobranza = False
                st.rerun()

    st.markdown("---")

    # -----------------------------------------------------------------------
    # BLOQUE 1 — INFORMACIÓN BÁSICA
    # -----------------------------------------------------------------------
    st.subheader("💰 Tu situación económica actual")

    col1, col2 = st.columns(2)

    with col1:
        ingreso_mensual = st.number_input(
            "¿Cuánto ganas al mes? (MXN)",
            min_value=0.0,
            max_value=1000000.0,
            value=round(st.session_state.get('annual_inc', 95000.0) / 12, 0),
            step=500.0,
            key="ingreso_mensual_input",
            help="Tu ingreso antes de impuestos. Si eres independiente, pon el promedio de los últimos 3 meses."
        )
        st.session_state['annual_inc'] = round(ingreso_mensual * 12, 2)

        salario_minimo_mensual = 7468
        veces_salario = ingreso_mensual / salario_minimo_mensual if ingreso_mensual > 0 else 0
        st.caption(f"Equivale a {veces_salario:.1f}x el salario mínimo mensual")

    with col2:
        deuda_mensual = st.number_input(
            "¿Cuánto pagas al mes en otras deudas? (MXN)",
            min_value=0.0,
            max_value=500000.0,
            value=round(st.session_state.get('dti', 10.0) * ingreso_mensual / 100, 0)
            if ingreso_mensual > 0 else 0.0,
            step=100.0,
            key="deuda_mensual_input",
            help="Suma todo lo que pagas al mes: tarjetas, crédito de nómina, automotriz, etc."
        )
        if ingreso_mensual > 0:
            dti_calculado = round((deuda_mensual / ingreso_mensual) * 100, 1)
        else:
            dti_calculado = 0.0
        st.session_state['dti'] = dti_calculado

        if dti_calculado <= 30:
            st.success(f"DTI(% de Ingresos Comprometidos en Deudas): {dti_calculado:.1f}% — Excelente capacidad de pago")
        elif dti_calculado <= 40:
            st.info(f"DTI(% de Ingresos Comprometidos en Deudas): {dti_calculado:.1f}% — Capacidad adecuada")
        elif dti_calculado <= 50:
            st.warning(f"DTI(% de Ingresos Comprometidos en Deudas): {dti_calculado:.1f}% — Capacidad limitada")
        else:
            st.error(f"DTI(% de Ingresos Comprometidos en Deudas): {dti_calculado:.1f}% — Nivel de deuda muy alto")

    st.markdown("---")
    st.subheader("💳 Tu crédito y tarjetas")

    col1, col2 = st.columns(2)

    with col1:
        limite_total = st.number_input(
            "¿Cuánto es el límite total de tus tarjetas de crédito? (MXN)",
            min_value=0.0,
            max_value=2000000.0,
            value=10000.0,
            step=1000.0,
            key="limite_total_input",
            help="Suma los límites de todas tus tarjetas. Si no tienes tarjeta, deja en 0."
        )

    with col2:
        deuda_tarjetas = st.number_input(
            "¿Cuánto debes actualmente en tus tarjetas? (MXN)",
            min_value=0.0,
            max_value=2000000.0,
            value=0.0,
            step=500.0,
            key="deuda_tarjetas_input",
            help="El saldo total que debes hoy en todas tus tarjetas."
        )

    if limite_total > 0:
        bc_util_calculado = round((deuda_tarjetas / limite_total) * 100, 1)
    else:
        bc_util_calculado = 0.0
    st.session_state['bc_util'] = bc_util_calculado

    if bc_util_calculado <= 30:
        st.success(f"Uso de crédito: {bc_util_calculado:.1f}% — Buró saludable (ideal menor al 30%)")
    elif bc_util_calculado <= 50:
        st.info(f"Uso de crédito: {bc_util_calculado:.1f}% — Uso moderado")
    elif bc_util_calculado <= 75:
        st.warning(f"Uso de crédito: {bc_util_calculado:.1f}% — Uso elevado")
    else:
        st.error(f"Uso de crédito: {bc_util_calculado:.1f}% — Capacidad comprometida")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # BLOQUE: EL PRÉSTAMO QUE DESEAS (con tasa de interés visible)
    # -----------------------------------------------------------------------
    st.subheader("🏷️ El préstamo que deseas")

    col_loan1, col_loan2 = st.columns(2)

    with col_loan1:
        monto_prestamo = st.number_input(
            "💰 ¿Cuánto dinero necesitas? (MXN)",
            min_value=1000.0,
            max_value=5000000.0,
            value=float(st.session_state.get('loan_amount', 20000.0)),
            step=1000.0,
            key="loan_amount_input",
            help="El monto total que deseas solicitar."
        )
        st.session_state['loan_amount'] = monto_prestamo

    with col_loan2:
        plazo_meses = st.selectbox(
            "📅 ¿En cuántos meses pagarías?",
            options=[6, 9, 12, 18, 24, 36, 48, 60],
            index=[6, 9, 12, 18, 24, 36, 48, 60].index(st.session_state.get('loan_term', 12)),
            key="loan_term_select",
            help="Plazos más largos reducen la mensualidad pero aumentan el interés total."
        )
        st.session_state['loan_term'] = plazo_meses

    st.markdown("---")

    # -----------------------------------------------------------------------
    # TASA DE INTERÉS - CAMPO VISIBLE Y EDITABLE
    # -----------------------------------------------------------------------
    st.subheader("📊 Tasa de interés")

    # Calcular tasa sugerida basada en el perfil actual
    dti_actual = st.session_state.get('dti', 10.0)
    bc_util_actual = st.session_state.get('bc_util', 15.0)
    ingreso_mensual_actual = st.session_state.get('annual_inc', 95000) / 12
    tasa_sugerida = obtener_tasa_estimada(
        dti_actual, bc_util_actual, ingreso_mensual_actual,
        monto_prestamo, plazo_meses
    )

    # Opción para usar tasa sugerida o manual
    col_rate1, col_rate2 = st.columns([1, 3])

    with col_rate1:
        usar_sugerida = st.checkbox(
            "Usar tasa sugerida",
            value=st.session_state.get('use_suggested_rate', True),
            key="use_suggested_rate_check",
            help="El sistema sugiere una tasa según tu perfil de riesgo"
        )
        st.session_state.use_suggested_rate = usar_sugerida

    with col_rate2:
        if usar_sugerida:
            tasa_anual = tasa_sugerida
            st.session_state.user_interest_rate = tasa_anual
            st.info(f"📈 **Tasa sugerida para tu perfil:** {tasa_anual:.1f}% anual")

            # Mostrar tabla de referencia de tasas
            with st.expander("📊 Referencia de tasas en México"):
                st.markdown("""
                | Tipo de crédito | Tasa anual aproximada |
                |----------------|----------------------|
                | Hipotecario | 9% - 12% |
                | Automotriz | 12% - 18% |
                | Personal (nómina) | 15% - 25% |
                | Personal (sin nómina) | 25% - 45% |
                | Tarjeta de crédito | 35% - 65% |
                | Préstamo de aplicación | 60% - 120% |
                """)
        else:
            tasa_anual = st.number_input(
                "📉 Tasa de interés anual (%)",
                min_value=5.0,
                max_value=80.0,
                value=float(st.session_state.get('user_interest_rate', 18.0)),
                step=0.5,
                key="interest_rate_manual",
                help="La tasa que te ofrece la institución financiera. En México, las tasas personales suelen estar entre 15% y 45%."
            )
            st.session_state.user_interest_rate = tasa_anual

    st.markdown("---")

    # -----------------------------------------------------------------------
    # CÁLCULOS DEL PRÉSTAMO
    # -----------------------------------------------------------------------
    mensualidad_calculada = calcular_mensualidad(monto_prestamo, plazo_meses, tasa_anual)
    cat_estimado = calcular_cat_estimado(tasa_anual, monto_prestamo, plazo_meses)
    intereses_totales = calcular_intereses_totales(monto_prestamo, plazo_meses, tasa_anual)
    total_pagar = monto_prestamo + intereses_totales

    # Mostrar resumen financiero
    st.subheader("💰 Resumen financiero del préstamo")

    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)

    with col_sum1:
        st.metric(
            "📆 Mensualidad",
            f"${mensualidad_calculada:,.2f}",
            help="Pago mensual que tendrías que hacer"
        )

    with col_sum2:
        st.metric(
            "💸 Intereses totales",
            f"${intereses_totales:,.2f}",
            delta=f"{((intereses_totales / monto_prestamo) * 100):.1f}% del monto",
            delta_color="off"
        )

    with col_sum3:
        st.metric(
            "🏦 Total a pagar",
            f"${total_pagar:,.2f}",
            help="Monto del préstamo + intereses"
        )

    with col_sum4:
        st.metric(
            "📋 CAT estimado",
            f"{cat_estimado:.1f}%",
            help="Costo Anual Total (incluye comisiones estimadas)"
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MENSUALIDAD QUE EL USUARIO PUEDE PAGAR
    # -----------------------------------------------------------------------
    st.subheader("💵 ¿Cuánto puedes pagar al mes?")

    col_pay1, col_pay2 = st.columns(2)

    with col_pay1:
        mensualidad_deseada = st.number_input(
            "Mensualidad que puedes pagar cómodamente (MXN)",
            min_value=0.0,
            max_value=200000.0,
            value=float(mensualidad_calculada),
            step=100.0,
            key="installment_input",
            help="La mensualidad que puedes cubrir sin afectar tus gastos básicos."
        )
        st.session_state['installment'] = mensualidad_deseada

    with col_pay2:
        porcentaje_ingreso = (mensualidad_deseada / ingreso_mensual * 100) if ingreso_mensual > 0 else 0

        if mensualidad_deseada > 0:
            if mensualidad_deseada >= mensualidad_calculada:
                st.success(f"✅ Puedes pagar la mensualidad requerida (${mensualidad_calculada:,.2f})")
            else:
                faltante = mensualidad_calculada - mensualidad_deseada
                st.warning(f"⚠️ Te faltan ${faltante:,.2f} mensuales para cubrir el préstamo")

            if porcentaje_ingreso <= 30:
                st.success(f"Representa el {porcentaje_ingreso:.1f}% de tu ingreso — Excelente")
            elif porcentaje_ingreso <= 40:
                st.info(f"Representa el {porcentaje_ingreso:.1f}% de tu ingreso — Adecuado")
            else:
                st.warning(f"⚠️ Representa el {porcentaje_ingreso:.1f}% de tu ingreso — Alto")

    # -----------------------------------------------------------------------
    # BLOQUE 2 — HISTORIAL PREVIO (condicional)
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 ¿Tienes créditos o préstamos anteriores?")

    tiene_historial = st.radio(
        "¿Has tenido algún préstamo, crédito de nómina o financiamiento antes?",
        options=["No, es mi primer crédito", "Sí, tengo o tuve créditos antes"],
        index=1 if st.session_state.get('tiene_historial', False) else 0,
        key="tiene_historial_radio",
        horizontal=True
    )
    st.session_state['tiene_historial'] = (tiene_historial == "Sí, tengo o tuve créditos antes")

    if st.session_state['tiene_historial']:

        col1, col2 = st.columns(2)

        with col1:
            saldo_pendiente = st.number_input(
                "¿Cuánto debes todavía de capital en ese crédito? (MXN)",
                min_value=0.0,
                max_value=5000000.0,
                value=float(st.session_state.get('out_prncp', 0.0)),
                step=1000.0,
                key="out_prncp_input",
                help="Solo el capital, sin contar intereses."
            )
            st.session_state['out_prncp'] = saldo_pendiente

        with col2:
            ultimo_pago = st.number_input(
                "¿Cuánto fue tu último pago a ese crédito? (MXN)",
                min_value=0.0,
                max_value=500000.0,
                value=float(st.session_state.get('last_pymnt_amnt', 0.0)),
                step=100.0,
                key="last_pymnt_amnt_input"
            )
            st.session_state['last_pymnt_amnt'] = ultimo_pago

        st.markdown("---")
        tuvo_cobranza = st.radio(
            "¿Alguna vez un banco o financiera tuvo que recurrir a cobranza?",
            options=[
                "No, siempre he pagado a tiempo",
                "Sí, hubo algún proceso de cobranza"
            ],
            index=1 if st.session_state.get('tuvo_cobranza', False) else 0,
            key="tuvo_cobranza_radio",
            horizontal=True
        )
        st.session_state['tuvo_cobranza'] = (tuvo_cobranza == "Sí, hubo algún proceso de cobranza")

        if st.session_state['tuvo_cobranza']:
            monto_cobranza = st.number_input(
                "¿Aproximadamente cuánto dinero recuperaron por esa cobranza? (MXN)",
                min_value=0.0,
                max_value=500000.0,
                value=float(st.session_state.get('recoveries', 0.0)),
                step=500.0,
                key="recoveries_input"
            )
            st.session_state['recoveries'] = monto_cobranza
        else:
            st.session_state['recoveries'] = 0.0

    else:
        st.session_state['out_prncp'] = 0.0
        st.session_state['last_pymnt_amnt'] = 0.0
        st.session_state['recoveries'] = 0.0
        st.session_state['tuvo_cobranza'] = False
        st.info("✅ Al ser tu primer crédito, el sistema usará valores base para el análisis.")

    # -----------------------------------------------------------------------
    # RESUMEN ANTES DE PREDECIR
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Resumen de tu perfil")

    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        ev_dti = evaluate_factor('dti', st.session_state.get('dti', 0))
        st.metric(
            "Deudas vs. ingresos",
            f"{st.session_state.get('dti', 0):.1f}%",
            delta=f"{ev_dti['icon']} {ev_dti['text']}",
            delta_color="off"
        )
    with rc2:
        monthly_inc = st.session_state.get('annual_inc', 0) / 12
        ev_inc = evaluate_factor('annual_inc', st.session_state.get('annual_inc', 0))
        st.metric(
            "Ingreso mensual",
            f"${monthly_inc:,.0f}",
            delta=f"{ev_inc['icon']} {ev_inc['text']}",
            delta_color="off"
        )
    with rc3:
        ev_bcu = evaluate_factor('bc_util', st.session_state.get('bc_util', 0))
        st.metric(
            "Uso de crédito",
            f"{st.session_state.get('bc_util', 0):.1f}%",
            delta=f"{ev_bcu['icon']} {ev_bcu['text']}",
            delta_color="off"
        )
    with rc4:
        ev_rate = evaluate_factor('int_rate', tasa_anual)
        st.metric(
            "Tasa interés",
            f"{tasa_anual:.1f}%",
            delta=f"{ev_rate['icon']} {ev_rate['text']}",
            delta_color="off"
        )

    # Resumen del préstamo
    st.markdown("---")
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    with col_res1:
        st.metric("💰 Monto solicitado", f"${monto_prestamo:,.0f}")
    with col_res2:
        st.metric("📅 Plazo", f"{plazo_meses} meses")
    with col_res3:
        st.metric("💵 Mensualidad", f"${mensualidad_deseada:,.0f}")
    with col_res4:
        st.metric("📊 Tasa", f"{tasa_anual:.1f}%")

    # -----------------------------------------------------------------------
    # BOTÓN DE PREDICCIÓN
    # -----------------------------------------------------------------------
    st.markdown("---")
    if st.button("🎯 Analizar mi solicitud", type="primary", use_container_width=True):

        # Validaciones
        if monto_prestamo <= 0:
            st.error("❌ Por favor ingresa un monto de préstamo válido")
            return
        if plazo_meses <= 0:
            st.error("❌ Por favor selecciona un plazo válido")
            return
        if mensualidad_deseada <= 0:
            st.error("❌ Por favor ingresa la mensualidad que puedes pagar")
            return

        # Inyectar campos ocultos derivados
        inject_hidden_fields()

        # Construir input_data con los 20 campos
        input_data = {k: float(st.session_state.get(k, 0.0)) for k in FEATURE_KEYS}

        input_data, errors = prediction_manager.validate_input(input_data)
        if errors:
            for err in errors:
                st.error(err)
        else:
            with st.spinner("Analizando tu solicitud..."):
                results = prediction_manager.predict(input_data)

            if results:
                show_results(results, input_data, monto_prestamo, plazo_meses, tasa_anual)


# ---------------------------------------------------------------------------
# MOSTRAR RESULTADOS
# ---------------------------------------------------------------------------

def show_results(results, input_data, loan_amount, loan_term, interest_rate):
    st.markdown("---")
    st.markdown("## Resultado de tu análisis")

    decision = results['decision']
    prob = results['probability']
    risk_level = results['risk_level']
    profile_score = results['profile_score']

    # Encabezado de resultado
    if decision == "APROBADO":
        st.success(f"### ✅ Tu solicitud tiene buenas posibilidades de aprobarse")
    else:
        st.error(f"### ❌ Tu solicitud presenta factores de riesgo elevado")

    col_res1, col_res2 = st.columns([2, 1])

    with col_res1:
        fig = viz_manager.plot_prediction_result(prob, decision, risk_level)
        st.plotly_chart(fig, use_container_width=True)

    with col_res2:
        st.metric("Nivel de riesgo", risk_level)
        st.metric("Puntuación de perfil", f"{profile_score:.0f} / 100")
        st.metric("Probabilidad de riesgo", f"{prob:.1%}")
        st.caption(f"Umbral de decisión: {results['threshold']:.0%}")

    # Mostrar resumen del préstamo en resultados
    st.markdown("---")
    st.subheader("📋 Resumen de tu solicitud")

    col_loan_r1, col_loan_r2, col_loan_r3, col_loan_r4 = st.columns(4)
    with col_loan_r1:
        st.metric("💰 Monto", f"${loan_amount:,.0f}")
    with col_loan_r2:
        st.metric("📅 Plazo", f"{loan_term} meses")
    with col_loan_r3:
        mensualidad_calc = calcular_mensualidad(loan_amount, loan_term, interest_rate)
        st.metric("💵 Mensualidad requerida", f"${mensualidad_calc:,.0f}")
    with col_loan_r4:
        st.metric("📊 Tasa de interés", f"{interest_rate:.1f}%")

    # -----------------------------------------------------------------------
    # EXPLICACIÓN DETALLADA
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔍 ¿Por qué obtuve este resultado?")

    factores_visibles = [
        ('dti', "Proporción de tus deudas vs. ingresos"),
        ('annual_inc', "Tus ingresos anuales"),
        ('bc_util', "Qué tanto usas tu crédito disponible"),
        ('int_rate', "Tasa de interés del préstamo"),
        ('out_prncp', "Saldo que aún debes de créditos anteriores"),
        ('last_pymnt_amnt', "Tu último pago registrado"),
        ('recoveries', "Historial de cobranza"),
    ]

    cols_factores = st.columns(3)
    for i, (campo, etiqueta) in enumerate(factores_visibles):
        valor = input_data.get(campo, 0)
        ev = evaluate_factor(campo, valor)
        color_map = {'good': 'normal', 'medium': 'off', 'bad': 'inverse', 'neutral': 'normal'}
        with cols_factores[i % 3]:
            if any(kw in campo for kw in ['amnt', 'inc', 'prncp', 'pymnt', 'recovery']):
                valor_fmt = f"${valor:,.0f}"
            elif any(kw in campo for kw in ['rate', 'util', 'dti']):
                valor_fmt = f"{valor:.1f}%"
            else:
                valor_fmt = f"{valor:,.2f}"
            st.metric(
                etiqueta,
                valor_fmt,
                delta=f"{ev['icon']} {ev['text']}",
                delta_color=color_map[ev['status']]
            )

    # -----------------------------------------------------------------------
    # EXPLICACIÓN NARRATIVA
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("💡 ¿Qué significa esto para ti?")

    if prob < 0.2:
        st.markdown("""
        **Tu perfil financiero es muy sólido.** Tienes buena capacidad de pago, tus deudas
        son manejables y tu historial crediticio es positivo.

        **La tasa de interés** que se te podría ofrecer estaría en el rango bajo del mercado.
        """)
    elif prob < 0.4:
        st.markdown("""
        **Tu perfil es estable y dentro de los parámetros normales.** Tienes capacidad de
        pago, aunque hay algunas áreas de oportunidad.

        **La tasa de interés** dependerá de la institución, pero estaría en rangos estándar.
        """)
    else:
        st.markdown("""
        **Tu perfil presenta factores que incrementan el riesgo.** Esto puede deberse a un
        nivel alto de deudas, historial de cobranza o ingreso insuficiente.

        **La tasa de interés** probablemente sería alta. Considera:
        - Solicitar un monto menor
        - Buscar un aval
        - Mejorar tu historial antes de solicitar
        """)

    # Factores específicos
    factores_negativos = []
    if input_data.get('dti', 0) > 40:
        factores_negativos.append("Tu nivel de deudas es alto en relación a tu ingreso (DTI > 40%)")
    if input_data.get('bc_util', 0) > 75:
        factores_negativos.append("Estás usando más del 75% de tu crédito disponible")
    if input_data.get('recoveries', 0) > 0:
        factores_negativos.append("Tienes historial de cobranza registrado")
    if input_data.get('out_prncp', 0) > 5000:
        factores_negativos.append("Aún tienes un saldo importante de capital por pagar")
    if interest_rate > 35:
        factores_negativos.append(
            f"La tasa de interés es alta ({interest_rate:.1f}%) — esto aumenta el riesgo de impago")

    if factores_negativos:
        with st.expander("⚠️ Factores que más influyeron en tu resultado"):
            for f in factores_negativos:
                st.markdown(f"- {f}")

    # -----------------------------------------------------------------------
    # GUARDAR EN BASE DE DATOS
    # -----------------------------------------------------------------------
    user = auth_manager.get_current_user()
    prediction_id = db_manager.save_prediction(user['id'], input_data, results)
    if prediction_id:
        st.caption(f"Análisis guardado — ID: {prediction_id}")

    # Detalles técnicos opcionales
    with st.expander("🔧 Ver datos técnicos completos del análisis"):
        st.json(results)
        st.subheader("Valores procesados por el modelo")
        df_vals = pd.DataFrame([
            {
                'Campo técnico': k,
                'Valor': f"${v:,.2f}" if any(
                    kw in k for kw in ['amnt', 'inc', 'prncp', 'pymnt', 'recovery', 'fee', 'balance']) else f"{v:.2f}",
                'Impacto': '🔴 Alto' if k in ['recoveries', 'out_prncp', 'last_pymnt_amnt', 'dti', 'annual_inc',
                                             'int_rate'] else '🟡 Medio' if k in ['bc_util', 'total_pymnt',
                                                                                 'installment'] else '⚪ Bajo'
            }
            for k, v in input_data.items()
        ])
        st.dataframe(df_vals, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA DE ANÁLISIS
# ---------------------------------------------------------------------------

def show_analysis_page():
    st.title("📈 Análisis de mi última simulación")
    st.markdown("---")

    user = auth_manager.get_current_user()
    predictions = db_manager.get_user_predictions(user['id'], limit=1)

    if predictions.empty:
        st.info("ℹ️ Realiza una simulación primero para ver el análisis aquí.")
        return

    last_pred = predictions.iloc[0]
    details = db_manager.get_prediction_details(last_pred['id'], user['id'])

    if not details:
        st.error("❌ No se pudieron obtener los detalles")
        return

    try:
        details_json = json.loads(details['details_json'])
        input_data = details_json.get('feature_values', {})
    except Exception:
        input_data = {}

    tab1, tab2, tab3 = st.tabs(["📊 Factores clave", "📈 Comparación", "🔍 Cómo funciona el modelo"])

    with tab1:
        model_info = prediction_manager.get_model_info()
        feature_importance = model_info.get('feature_importance', {})
        if feature_importance:
            fig = viz_manager.plot_feature_importance(feature_importance)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ No hay importancia de características disponible en este modelo.")

    with tab2:
        if input_data:
            fig = viz_manager.plot_profile_comparison(input_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            etiquetas = {
                'dti': '% de ingresos en deudas',
                'annual_inc': 'Ingresos anuales',
                'bc_util': 'Uso de crédito',
                'installment': 'Mensualidad',
                'out_prncp': 'Saldo capital pendiente',
                'last_pymnt_amnt': 'Último pago',
                'recoveries': 'Monto de cobranza',
                'int_rate': 'Tasa de interés',
            }
            rows = []
            for k, v in input_data.items():
                if k in etiquetas:
                    rows.append({'Concepto': etiquetas[k],
                                 'Valor': f"${v:,.2f}" if 'inc' in k or 'amnt' in k or 'prncp' in k or 'pymnt' in k or 'recovery' in k else f"{v:.1f}%"})
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("""
        ### Cómo toma decisiones el sistema

        El sistema usa un modelo de inteligencia artificial llamado **Random Forest**.

        **Los factores que más pesan en la decisión son:**

        1. **Historial de cobranza** — Señal de mayor riesgo
        2. **Saldo pendiente de capital** — Deudas actuales
        3. **Tasa de interés** — Tasas altas sugieren mayor riesgo percibido
        4. **Proporción deudas/ingresos (DTI)**
        5. **Ingresos** — Capacidad real de pago
        6. **Monto del préstamo** — Montos altos = más riesgo

        **El umbral de decisión** está en {threshold:.0%}.
        """.format(threshold=prediction_manager.threshold))


# ---------------------------------------------------------------------------
# PÁGINA DE HISTORIAL
# ---------------------------------------------------------------------------

def show_history_page():
    st.title("📋 Mis simulaciones anteriores")
    st.markdown("---")

    user = auth_manager.get_current_user()

    with st.spinner("Cargando historial..."):
        predictions = db_manager.get_user_predictions(user['id'], limit=100)

    if predictions.empty:
        st.info("ℹ️ Aún no tienes simulaciones registradas.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de simulaciones", len(predictions))
    with col2:
        aprobados = len(predictions[predictions['decision'] == 'APROBADO'])
        st.metric("Con resultado favorable", aprobados)
    with col3:
        avg_risk = predictions['risk_probability'].mean() * 100
        st.metric("Riesgo promedio", f"{avg_risk:.1f}%")
    with col4:
        ultima = predictions['created_at'].max()
        st.metric("Última simulación", ultima.strftime("%d/%m/%Y"))

    st.markdown("---")
    st.subheader("📈 Evolución de tus simulaciones")
    fig = viz_manager.plot_prediction_history(predictions)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Detalle")

    df_display = predictions.copy()
    df_display['created_at'] = pd.to_datetime(df_display['created_at']).dt.strftime('%d/%m/%Y %H:%M')
    df_display['risk_probability'] = df_display['risk_probability'].apply(lambda x: f"{x:.1%}")
    df_display['annual_inc'] = df_display['annual_inc'].apply(lambda x: f"${x:,.0f}")
    df_display['out_prncp'] = df_display['out_prncp'].apply(lambda x: f"${x:,.2f}")
    df_display['loan_amount'] = df_display['loan_amount'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    df_display['loan_term'] = df_display['loan_term'].apply(lambda x: f"{int(x)} meses" if pd.notna(x) else "N/A")

    col_map = {
        'created_at': 'Fecha',
        'decision': 'Resultado',
        'risk_level': 'Nivel de riesgo',
        'risk_probability': 'Probabilidad',
        'loan_amount': 'Monto solicitado',
        'loan_term': 'Plazo',
        'out_prncp': 'Saldo pendiente',
        'dti': 'DTI (%)',
        'annual_inc': 'Ingresos anuales'
    }
    df_show = df_display[list(col_map.keys())].rename(columns=col_map)
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PÁGINA DE CONFIGURACIÓN
# ---------------------------------------------------------------------------

def show_configuration_page():
    st.title("⚙️ Configuración")
    st.markdown("---")

    user = auth_manager.get_current_user()

    st.header("🤖 Ajustes del modelo")

    col1, col2 = st.columns([3, 1])
    with col1:
        current_threshold = prediction_manager.threshold
        new_threshold = st.slider(
            "Umbral de decisión",
            min_value=0.1, max_value=0.9,
            value=float(current_threshold),
            step=0.05, format="%.2f",
            help="Probabilidad mínima para clasificar como rechazado"
        )
        if new_threshold != current_threshold:
            prediction_manager.set_threshold(new_threshold)
            st.success(f"✅ Umbral actualizado a {new_threshold:.0%}")
    with col2:
        st.metric("Umbral actual", f"{current_threshold:.0%}")
        if st.button("🔄 Restablecer", use_container_width=True):
            prediction_manager.set_threshold(0.4)
            st.success("✅ Restablecido a 40%")
            st.rerun()

    st.markdown("---")

    st.header("👤 Mi perfil")
    profile_tab, password_tab = st.tabs(["📝 Datos personales", "🔐 Cambiar contraseña"])

    with profile_tab:
        with st.form("user_profile_form"):
            current_name = st.text_input("Nombre completo", value=user['full_name'])
            st.text_input("Correo electrónico", value=user['email'], disabled=True)
            submitted = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
            if submitted:
                if not current_name or len(current_name.strip()) < 3:
                    st.error("❌ El nombre debe tener al menos 3 caracteres")
                else:
                    success, message = auth_manager.update_profile(user['id'], current_name.strip())
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with password_tab:
        with st.form("change_password_form"):
            st.info("🔒 La contraseña debe tener al menos 8 caracteres")
            current_password = st.text_input("Contraseña actual", type="password")
            new_password = st.text_input("Nueva contraseña", type="password")
            confirm_password = st.text_input("Confirmar nueva contraseña", type="password")

            if new_password:
                score = sum([
                    len(new_password) >= 8,
                    any(c.isupper() for c in new_password),
                    any(c.islower() for c in new_password),
                    any(c.isdigit() for c in new_password),
                    any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password)
                ])
                labels = ["", "Muy débil", "Débil", "Moderada", "Buena", "Excelente"]
                st.progress(score / 5, text=f"Fortaleza: {labels[score]}")

            submitted_pw = st.form_submit_button("🔐 Cambiar contraseña", use_container_width=True)
            if submitted_pw:
                if not all([current_password, new_password, confirm_password]):
                    st.error("❌ Completa todos los campos")
                else:
                    success, message = auth_manager.update_password(
                        user['id'], current_password, new_password, confirm_password
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    st.markdown("---")

    st.header("ℹ️ Estado del sistema")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Base de datos")
        if db_manager.test_connection():
            st.success("✅ Conectada")
            with st.expander("Ver detalles"):
                st.write(f"**Servidor:** {db_manager.host}")
                st.write(f"**Base de datos:** {db_manager.database}")
                st.write(f"**Usuario:** {db_manager.username}")
        else:
            st.error("❌ Sin conexión")

    with col2:
        st.subheader("Modelo")
        model_info = prediction_manager.get_model_info()
        st.info(f"""
        - **Tipo:** {model_info.get('type', 'N/A')}
        - **Características:** {model_info.get('n_features', 'N/A')}
        - **Estado:** {'✅ Cargado' if prediction_manager.model else '❌ No cargado'}
        - **Umbral:** {prediction_manager.threshold:.0%}
        """)
        if st.button("🔄 Recargar modelo", use_container_width=True):
            with st.spinner("Recargando..."):
                if prediction_manager.load_model():
                    st.success("✅ Modelo recargado")
                    st.rerun()
                else:
                    st.error("❌ Error al recargar el modelo")


# ---------------------------------------------------------------------------
# PUNTO DE ENTRADA
# ---------------------------------------------------------------------------

def main():
    initialize_session_state()
    if not auth_manager.is_authenticated():
        show_login_page()
    else:
        show_main_page()


if __name__ == "__main__":
    main()