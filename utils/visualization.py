"""
Módulo para visualizaciones - VERSIÓN MEXICANA
"""
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import streamlit as st
from config.feature_translations import FEATURE_TRANSLATIONS, FEATURE_HELP_TEXTS


class VisualizationManager:
    """Gestor de visualizaciones - VERSIÓN MEXICANA"""

    def __init__(self):
        plt.style.use('seaborn-v0_8-darkgrid')
        self.primary_color = '#2c3e50'
        self.secondary_color = '#3498db'
        self.success_color = '#27ae60'
        self.warning_color = '#e74c3c'

    def get_friendly_name(self, feature_name, include_unit=True):
        """Obtener nombre amigable en español mexicano"""
        # Traducción principal
        friendly_name = FEATURE_TRANSLATIONS.get(feature_name, feature_name)

        # Agregar unidad monetaria si corresponde
        if include_unit:
            if any(keyword in feature_name for keyword in
                   ['amnt', 'inc', 'prncp', 'pymnt', 'recovery', 'fee', 'balance']):
                friendly_name += ' (MXN)'
            elif any(keyword in feature_name for keyword in ['rate', 'util', 'dti']):
                friendly_name += ' (%)'

        return friendly_name

    def get_help_text(self, feature_name):
        """Obtener texto de ayuda contextualizado para México"""
        return FEATURE_HELP_TEXTS.get(feature_name, "")

    def plot_prediction_result(self, probability, decision, risk_level):
        """Crear visualización del resultado de predicción"""
        fig = go.Figure()

        # Crear medidor
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=probability * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Probabilidad de Riesgo", 'font': {'size': 24}},
            delta={'reference': 40, 'increasing': {'color': self.warning_color}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': self.get_risk_color(probability)},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 20], 'color': self.success_color},
                    {'range': [20, 40], 'color': '#2ecc71'},
                    {'range': [40, 100], 'color': self.warning_color}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 40  # Umbral por defecto
                }
            }
        ))

        fig.update_layout(
            height=400,
            paper_bgcolor='white',
            font={'color': "darkblue", 'family': "Arial"},
            title={
                'text': f"Decisión: {decision}",
                'font': {'size': 28, 'color': self.get_decision_color(decision)}
            },
            annotations=[
                dict(
                    text=f"Nivel de riesgo: {risk_level}",
                    x=0.5,
                    y=0.2,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font={'size': 18}
                )
            ]
        )

        return fig

    def get_risk_color(self, probability):
        """Obtener color basado en probabilidad"""
        if probability < 0.2:
            return self.success_color
        elif probability < 0.4:
            return '#2ecc71'
        else:
            return self.warning_color

    def get_decision_color(self, decision):
        """Obtener color basado en decisión"""
        return self.success_color if decision == "APROBADO" else self.warning_color

    def plot_feature_importance(self, feature_importance, top_n=15):
        """Crear gráfico de importancia de características"""
        if not feature_importance:
            return None

        # Ordenar características por importancia
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_features) > top_n:
            sorted_features = sorted_features[:top_n]

        features = [item[0] for item in sorted_features]
        importances = [item[1] for item in sorted_features]

        # Usar nombres traducidos
        translated_features = [self.get_friendly_name(f, include_unit=False) for f in features]

        # Crear figura
        fig = go.Figure(go.Bar(
            x=importances,
            y=translated_features,
            orientation='h',
            marker=dict(color=self.secondary_color)
        ))

        fig.update_layout(
            title="Importancia de Características (Top 15)",
            xaxis_title="Importancia",
            yaxis_title="Característica",
            height=500,
            showlegend=False
        )

        return fig

    def plot_profile_comparison(self, input_data):
        """Crear gráfico de comparación de perfil"""
        # Valores de referencia para aprobación en contexto mexicano
        reference_values_mx = {
            'out_prncp': 0,  # Idealmente sin deuda pendiente
            'dti': 35,  # En México, DTI recomendado <35-40%
            'int_rate': 25,  # Tasa promedio en créditos personales México
            'bc_util': 30,  # Buró de Crédito recomienda <30%
            'annual_inc': 250000,  # Ingreso promedio formal en México
            'last_pymnt_amnt': 1000  # Pago mínimo esperado
        }

        # Preparar datos para comparación
        categories = []
        applicant_values = []
        reference = []

        for key, ref_val in reference_values_mx.items():
            if key in input_data:
                categories.append(self.get_friendly_name(key, include_unit=False))
                applicant_values.append(input_data[key])
                reference.append(ref_val)

        if not categories:
            return None

        # Crear gráfico
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Solicitante',
            x=categories,
            y=applicant_values,
            marker_color=self.secondary_color
        ))

        fig.add_trace(go.Bar(
            name='Referencia Mexicana',
            x=categories,
            y=reference,
            marker_color='lightgray',
            opacity=0.6
        ))

        fig.update_layout(
            title="Comparación con Referencias Mexicanas",
            barmode='group',
            height=400,
            showlegend=True,
            yaxis_title="Valor"
        )

        return fig

    def plot_profile_comparison_mx(self, input_data):
        """Alias para plot_profile_comparison (mantener compatibilidad)"""
        return self.plot_profile_comparison(input_data)

    def plot_prediction_history(self, history_df):
        """Crear gráfico de historial de predicciones"""
        if history_df.empty:
            return None

        # Preparar datos
        history_df['created_at'] = pd.to_datetime(history_df['created_at'])
        history_df = history_df.sort_values('created_at')

        # Crear figura
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=history_df['created_at'],
            y=history_df['risk_probability'] * 100,
            mode='lines+markers',
            name='Probabilidad de Riesgo',
            line=dict(color=self.secondary_color, width=2),
            marker=dict(size=8)
        ))

        # Añadir línea de umbral
        if 'threshold_used' in history_df.columns:
            avg_threshold = history_df['threshold_used'].mean() * 100
            fig.add_hline(
                y=avg_threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Umbral Promedio: {avg_threshold:.1f}%",
                annotation_position="bottom right"
            )

        fig.update_layout(
            title="Evolución de Predicciones",
            xaxis_title="Fecha",
            yaxis_title="Probabilidad de Riesgo (%)",
            height=400,
            hovermode='x unified'
        )

        return fig


# Instancia global de visualización
viz_manager = VisualizationManager()