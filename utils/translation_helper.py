"""
Utilidades para traducción y adaptación al contexto mexicano
"""

import streamlit as st
from config.feature_translations import (
    FEATURE_TRANSLATIONS,
    FEATURE_CATEGORIES,
    FEATURE_HELP_TEXTS
)


class TranslationHelper:
    """Ayudante para traducciones y contexto mexicano"""

    @staticmethod
    def translate_feature(feature_name):
        """Traducir nombre de característica"""
        return FEATURE_TRANSLATIONS.get(feature_name, feature_name)

    @staticmethod
    def get_feature_help(feature_name):
        """Obtener ayuda contextualizada"""
        return FEATURE_HELP_TEXTS.get(feature_name, "")

    @staticmethod
    def get_categorized_features():
        """Obtener características agrupadas por categoría"""
        return FEATURE_CATEGORIES

    @staticmethod
    def create_mexican_context_info():
        """Crear información contextual para México"""
        return {
            'dti_info': {
                'title': 'Relación Deuda/Ingreso (DTI) en México',
                'content': """
                **Escala mexicana de DTI:**
                - **<30%:** Excelente capacidad de pago
                - **30-40%:** Capacidad adecuada (límite recomendado)
                - **40-50%:** Capacidad limitada (riesgo moderado)
                - **>50%:** Sobreendeudamiento (alto riesgo)

                **Consideraciones locales:**
                • Incluye todos los créditos (tarjetas, nómina, automotriz, hipotecario)
                • Considera ingresos netos después de impuestos (ISR)
                • En sector informal, verificar flujos de caja reales
                """
            },
            'income_info': {
                'title': 'Ingresos en Contexto Mexicano',
                'content': """
                **Referencias salariales 2024:**
                - **Salario mínimo:** $248.93 diarios ($7,468 mensuales)
                - **Ingreso promedio formal:** ~$12,000 - $25,000 mensuales
                - **Clase media:** $25,000 - $80,000 mensuales

                **Documentación requerida:**
                • Comprobantes de nómina (últimos 3 meses)
                • Estados de cuenta bancarios
                • Para independientes: declaraciones fiscales (DIOT)
                """
            },
            'interest_info': {
                'title': 'Tasas de Interés en México',
                'content': """
                **Rangos típicos 2024:**
                - **Tarjetas de crédito:** 35% - 65% anual
                - **Créditos personales:** 15% - 40% anual
                - **Nómina:** 12% - 25% anual
                - **Automotriz:** 8% - 15% anual

                **CAT (Costo Anual Total):** Incluye comisiones, seguros y todos los costos
                **Tasa de referencia:** TIIE + margen
                """
            }
        }

    @staticmethod
    def format_currency_mx(value, feature_name=""):
        """Formatear moneda en formato mexicano"""
        if any(keyword in feature_name for keyword in ['amnt', 'inc', 'prncp', 'pymnt', 'recovery', 'fee', 'balance']):
            return f"${value:,.2f} MXN"
        elif any(keyword in feature_name for keyword in ['rate', 'util', 'dti']):
            return f"{value:.1f}%"
        else:
            return f"{value:,.2f}"

    @staticmethod
    def create_input_field_with_context(feature_name, current_value, **kwargs):
        """Crear campo de entrada con contexto mexicano"""
        translated_name = TranslationHelper.translate_feature(feature_name)
        help_text = TranslationHelper.get_feature_help(feature_name)

        # Formatear valor para display
        display_value = TranslationHelper.format_currency_mx(current_value, feature_name)

        # Crear campo con contexto
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                new_value = st.number_input(
                    label=translated_name,
                    value=float(current_value),
                    help=help_text,
                    **kwargs
                )


        return new_value