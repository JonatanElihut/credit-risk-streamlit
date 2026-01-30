"""
Módulo para manejar predicciones del modelo - VERSIÓN CORREGIDA BASADA EN TKINTER
"""
import joblib
import pandas as pd
import numpy as np
import json
import os
import streamlit as st
from sklearn.preprocessing import StandardScaler


class PredictionManager:
    """Gestor de predicciones del modelo - VERSIÓN CORREGIDA"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.model_info = {}
        self.threshold = 0.4  # Umbral por defecto ajustado (40%)
        self.load_model()
        # ¡IMPORTANTE: En el código Tkinter, probability_inverted = True
        self.probability_inverted = True  # Las probabilidades están invertidas

    def load_model(self):
        """Cargar modelo y archivos relacionados"""
        try:
            # Cargar modelo
            model_path = "models/modelo_random_forest.pkl"
            if os.path.exists(model_path):
                loaded_data = joblib.load(model_path)

                # Verificar si es un diccionario con múltiples objetos
                if isinstance(loaded_data, dict):
                    self.model = loaded_data.get('model')
                    self.scaler = loaded_data.get('scaler')
                    self.feature_names = loaded_data.get('feature_names', [])
                    self.threshold = loaded_data.get('threshold', 0.4)
                else:
                    self.model = loaded_data
                    self.scaler = None

                # Obtener información del modelo
                self.extract_model_info()

                # Cargar hiperparámetros
                self.load_hyperparameters()

                st.success("✅ Modelo cargado exitosamente")
                print(f"INFO: Modelo tipo: {type(self.model).__name__}")
                print(f"INFO: Threshold: {self.threshold}")
                print(f"INFO: Características: {len(self.feature_names)}")

                # Detectar automáticamente si las probabilidades están invertidas
                self.detect_probability_inversion()
                return True
            else:
                st.error(f"❌ No se encontró el modelo en: {model_path}")
                return False

        except Exception as e:
            st.error(f"❌ Error al cargar el modelo: {str(e)}")
            return False

    def detect_probability_inversion(self):
        """Detectar automáticamente si las probabilidades están invertidas"""
        # Crear un perfil de riesgo mínimo (debería ser APROBADO)
        test_data = {
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
        }

        # Preparar datos
        df = self.prepare_input_data(test_data)

        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(df)

            if hasattr(self.model, 'classes_'):
                classes = self.model.classes_
                print(f"DEBUG - Clases del modelo: {classes}")
                print(f"DEBUG - Probabilidades: {probabilities}")

                # Si las clases son [0, 1], la clase 1 es normalmente "riesgo"
                if len(classes) == 2:
                    prob_class_0 = probabilities[0, 0]
                    prob_class_1 = probabilities[0, 1]

                    # Perfil de riesgo mínimo debería tener probabilidad BAJA de riesgo
                    profile_score = self.calculate_profile_score(test_data)
                    print(f"DEBUG - Puntuación de perfil: {profile_score}")

                    # Si el perfil es excelente pero prob_class_1 (clase 1) es alta,
                    # entonces las probabilidades están invertidas
                    if profile_score > 80 and prob_class_1 > 0.5:
                        print("DEBUG - Detectado: probabilidades invertidas")
                        self.probability_inverted = True
                    else:
                        self.probability_inverted = False

    def load_hyperparameters(self):
        """Cargar hiperparámetros del modelo"""
        try:
            hyperparams_path = "models/hiperparametros_random_forest.json"
            if os.path.exists(hyperparams_path):
                with open(hyperparams_path, 'r') as f:
                    self.model_info['hyperparameters'] = json.load(f)
        except Exception as e:
            st.warning(f"⚠️ No se pudieron cargar los hiperparámetros: {str(e)}")

    def extract_model_info(self):
        """Extraer información del modelo"""
        if self.model is None:
            return

        self.model_info['type'] = type(self.model).__name__

        if hasattr(self.model, 'n_features_in_'):
            self.model_info['n_features'] = self.model.n_features_in_

        if hasattr(self.model, 'feature_names_in_'):
            self.feature_names = list(self.model.feature_names_in_)
            self.model_info['feature_names'] = self.feature_names

        if hasattr(self.model, 'n_estimators'):
            self.model_info['n_estimators'] = self.model.n_estimators

        if hasattr(self.model, 'max_depth'):
            self.model_info['max_depth'] = self.model.max_depth

        if hasattr(self.model, 'feature_importances_'):
            self.model_info['has_feature_importance'] = True
            importances = self.model.feature_importances_

            if self.feature_names and len(self.feature_names) == len(importances):
                self.model_info['feature_importance'] = dict(zip(self.feature_names, importances))

        # Información de clases del modelo
        if hasattr(self.model, 'classes_'):
            self.model_info['classes'] = self.model.classes_.tolist()
            print(f"INFO: Clases del modelo: {self.model_info['classes']}")

    def validate_input(self, input_data):
        """Validar datos de entrada"""
        errors = []

        # Convertir todos a float y validar
        for key, value in input_data.items():
            try:
                if value is None or value == '':
                    input_data[key] = 0.0
                else:
                    input_data[key] = float(value)
            except ValueError:
                errors.append(f"{key}: Valor inválido '{value}'")
                input_data[key] = 0.0

        return input_data, errors

    def prepare_input_data(self, input_data):
        """Preparar datos para el modelo - BASADO EN CÓDIGO TKINTER"""
        # Crear DataFrame
        df = pd.DataFrame([input_data])

        # Asegurar que tenemos todas las características
        if self.feature_names:
            # Agregar características faltantes
            for feature in self.feature_names:
                if feature not in df.columns:
                    df[feature] = 0.0

            # Reordenar columnas
            df = df[self.feature_names]

        # Aplicar escalado si está disponible
        if self.scaler is not None:
            try:
                df_scaled = self.scaler.transform(df)
                df = pd.DataFrame(df_scaled, columns=df.columns)
                print("✅ Escalado aplicado")
            except Exception as e:
                print(f"⚠️ Error en escalado: {str(e)}")

        return df

    def predict(self, input_data):
        """Realizar predicción - VERSIÓN IDÉNTICA A TKINTER"""
        try:
            print(f"\n{'=' * 60}")
            print("INICIO DE PREDICCIÓN - VERSIÓN TKINTER")
            print(f"{'=' * 60}")

            # Preparar datos
            df = self.prepare_input_data(input_data)

            print(f"Datos preparados: {df.shape}")
            print(f"Columnas: {df.columns.tolist()}")

            # Verificar dimensiones
            if hasattr(self.model, 'n_features_in_'):
                expected_features = self.model.n_features_in_
                actual_features = df.shape[1]

                if actual_features != expected_features:
                    st.error(f"Error: Modelo espera {expected_features} características, recibió {actual_features}")
                    return None

            # Obtener probabilidades o predicción directa
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(df)

                print(f"\n📊 PROBABILIDADES CRUDAS DEL MODELO:")
                print(f"Forma: {probabilities.shape}")
                print(f"Valores: {probabilities[0]}")

                # Información de clases
                if hasattr(self.model, 'classes_'):
                    classes = self.model.classes_
                    print(f"Clases del modelo: {classes}")

                    # Mostrar probabilidades por clase
                    for i, cls in enumerate(classes):
                        print(f"  P(clase {cls}): {probabilities[0, i]:.4f}")

                # **CORRECCIÓN CRÍTICA**: Usar misma lógica que Tkinter
                probability_risk = self.determine_correct_probability_tkinter(probabilities, df)

            else:
                # Modelo sin predict_proba
                prediction = self.model.predict(df)[0]
                print(f"Predicción directa: {prediction}")

                # Asumir que 1 = riesgo, 0 = no riesgo
                probability_risk = 1.0 if prediction == 1 else 0.0

            print(f"\n🎯 PROBABILIDAD DE RIESGO CALCULADA: {probability_risk:.4f} ({probability_risk:.1%})")
            print(f"📈 UMBRAL ACTUAL: {self.threshold:.4f}")

            # **DECISIÓN**: Si probabilidad de riesgo > umbral, RECHAZADO
            prediction = 1 if probability_risk > self.threshold else 0
            decision = "RECHAZADO" if prediction == 1 else "APROBADO"

            print(f"🤖 DECISIÓN FINAL: {decision} (predicción={prediction})")
            print(f"{'=' * 60}\n")

            # Determinar nivel de riesgo (igual que Tkinter)
            risk_level = self.determine_risk_level_tkinter(probability_risk)

            # Calcular puntuación de perfil
            profile_score = self.calculate_profile_score(input_data)

            return {
                'probability': probability_risk,
                'decision': decision,
                'risk_level': risk_level,
                'profile_score': profile_score,
                'threshold': self.threshold,
                'model_used': self.model_info.get('type', 'Random Forest'),
                'prediction_raw': prediction,
                'details': {
                    'features_used': list(input_data.keys()),
                    'feature_values': input_data,
                    'processed_data': df.iloc[0].to_dict() if not df.empty else {}
                }
            }

        except Exception as e:
            print(f"❌ ERROR en predicción: {str(e)}")
            import traceback
            traceback.print_exc()
            st.error(f"Error en predicción: {str(e)}")
            return None

    def determine_correct_probability_tkinter(self, probabilities, processed_data):
        """Determinar automáticamente qué probabilidad representa el riesgo real - IDÉNTICO A TKINTER"""
        print(f"\n🔍 DETERMINANDO PROBABILIDAD CORRECTA (MÉTODO TKINTER)...")

        # Caso 1: Tenemos información de clases
        if hasattr(self.model, 'classes_'):
            classes = self.model.classes_

            # Convertir clases a lista si es numpy array
            if hasattr(classes, 'tolist'):
                classes = classes.tolist()

            print(f"Clases disponibles: {classes}")

            # CASO MÁS COMÚN: Clases son [0, 1] o [1, 0]
            if len(classes) == 2:
                # Suponer que la última clase es "riesgo/bad"
                # (esto es estándar en scikit-learn para problemas binarios)
                probability_risk = probabilities[0, -1]  # Última columna

                print(f"Usando última clase ({classes[-1]}) como riesgo: {probability_risk:.4f}")

                # Verificar si esto tiene sentido con los datos
                if self.should_invert_probability(probability_risk, processed_data):
                    print(f"⚠️  Invirtiendo probabilidad: {probability_risk:.4f} -> {1 - probability_risk:.4f}")
                    probability_risk = 1 - probability_risk

                return probability_risk

            # Otros casos
            else:
                return probabilities[0, 0]

        # Caso 2: No hay información de clases
        else:
            # Asumir que la segunda columna es riesgo (formato estándar)
            if probabilities.shape[1] > 1:
                probability_risk = probabilities[0, 1]
                print(f"Sin información de clases, usando columna 1 como riesgo: {probability_risk:.4f}")

                if self.should_invert_probability(probability_risk, processed_data):
                    print(f"⚠️  Invirtiendo probabilidad: {probability_risk:.4f} -> {1 - probability_risk:.4f}")
                    probability_risk = 1 - probability_risk

                return probability_risk
            else:
                return probabilities[0, 0]

    def should_invert_probability(self, probability_risk, processed_data):
        """Determinar si la probabilidad debe ser invertida basándose en los datos - IDÉNTICO A TKINTER"""

        # Análisis heurístico del perfil
        profile_score = self.analyze_profile_quality(processed_data)
        print(f"\n📊 ANÁLISIS DE CALIDAD DEL PERFIL:")
        print(f"  • Puntuación de calidad: {profile_score:.2f}/100")
        print(f"  • Probabilidad actual de riesgo: {probability_risk:.4f}")

        # REGLAS PARA DETECTAR INVERSIÓN NECESARIA:

        # 1. Perfil excelente (score > 80) pero probabilidad de riesgo alta (> 0.7)
        if profile_score > 80 and probability_risk > 0.7:
            print(f"  ❌ CONFLICTO: Perfil excelente pero probabilidad de riesgo alta")
            print(f"     -> Se necesita inversión")
            return True

        # 2. Perfil terrible (score < 20) pero probabilidad de riesgo baja (< 0.3)
        if profile_score < 20 and probability_risk < 0.3:
            print(f"  ❌ CONFLICTO: Perfil terrible pero probabilidad de riesgo baja")
            print(f"     -> Se necesita inversión")
            return True

        # 3. Coherencia general
        expected_risk = (100 - profile_score) / 100  # Perfil malo -> alta probabilidad esperada
        difference = abs(probability_risk - expected_risk)

        print(f"  • Probabilidad esperada basada en perfil: {expected_risk:.4f}")
        print(f"  • Diferencia con probabilidad actual: {difference:.4f}")

        if difference > 0.6:  # Diferencia muy grande
            print(f"  ❌ GRAN DISCREPANCIA: Diferencia > 0.6")
            print(f"     -> Se necesita inversión")
            return True

        print(f"  ✅ Probabilidad coherente con el perfil")
        return False

    def analyze_profile_quality(self, processed_data):
        """Analizar la calidad del perfil y dar una puntuación 0-100 - IDÉNTICO A TKINTER"""
        score = 100  # Empieza perfecto, restamos por problemas

        try:
            # FACTOR 1: Principal pendiente (0 es perfecto, >5000 es muy malo)
            if 'out_prncp' in processed_data.columns:
                value = processed_data['out_prncp'].iloc[0]
                if value > 5000:
                    score -= 40
                elif value > 2000:
                    score -= 20
                elif value > 500:
                    score -= 10

            # FACTOR 2: Último pago (alto es bueno, 0 es malo)
            if 'last_pymnt_amnt' in processed_data.columns:
                value = processed_data['last_pymnt_amnt'].iloc[0]
                if value == 0:
                    score -= 30
                elif value < 100:
                    score -= 15

            # FACTOR 3: Recuperaciones (0 es bueno, >0 es malo)
            if 'recoveries' in processed_data.columns:
                value = processed_data['recoveries'].iloc[0]
                if value > 1000:
                    score -= 35
                elif value > 100:
                    score -= 20
                elif value > 0:
                    score -= 10

            # FACTOR 4: DTI (bajo es bueno, alto es malo)
            if 'dti' in processed_data.columns:
                value = processed_data['dti'].iloc[0]
                if value > 40:
                    score -= 30
                elif value > 25:
                    score -= 15
                elif value > 15:
                    score -= 5

            # FACTOR 5: Tasa de interés (baja es buena, alta es mala)
            if 'int_rate' in processed_data.columns:
                value = processed_data['int_rate'].iloc[0]
                if value > 20:
                    score -= 25
                elif value > 15:
                    score -= 15
                elif value > 10:
                    score -= 5

            # Asegurar que el score esté entre 0 y 100
            score = max(0, min(100, score))

            return score

        except Exception as e:
            print(f"Error en analyze_profile_quality: {e}")
            return 50  # Valor por defecto

    def determine_risk_level_tkinter(self, probability):
        """Determinar nivel de riesgo basado en probabilidad - IDÉNTICO A TKINTER"""
        if probability < 0.2:
            return "RIESGO MÍNIMO"
        elif probability < 0.4:
            return "RIESGO BAJO"
        else:  # probability >= 0.4
            return "RIESGO ALTO"

    def calculate_profile_score(self, input_data):
        """Calcular puntuación de perfil (0-100) - MEJORADA"""
        score = 100  # Empieza perfecto, restamos por problemas

        try:
            # FACTOR 1: Principal pendiente (0 es perfecto, >5000 es muy malo)
            out_prncp = input_data.get('out_prncp', 0)
            if out_prncp > 5000:
                score -= 40
            elif out_prncp > 2000:
                score -= 20
            elif out_prncp > 500:
                score -= 10
            elif out_prncp == 0:
                score += 5  # Bonus por sin deuda pendiente

            # FACTOR 2: DTI (bajo es bueno, alto es malo)
            dti = input_data.get('dti', 0)
            if dti > 40:
                score -= 30
            elif dti > 25:
                score -= 15
            elif dti > 15:
                score -= 5
            elif dti < 10:
                score += 10  # Bonus por DTI excelente

            # FACTOR 3: Tasa de interés (baja es buena, alta es mala)
            int_rate = input_data.get('int_rate', 0)
            if int_rate > 20:
                score -= 25
            elif int_rate > 15:
                score -= 15
            elif int_rate > 10:
                score -= 5
            elif int_rate < 8:
                score += 10  # Bonus por tasa baja

            # FACTOR 4: Utilización de crédito
            bc_util = input_data.get('bc_util', 0)
            if bc_util > 80:
                score -= 20
            elif bc_util > 60:
                score -= 10
            elif bc_util > 40:
                score -= 5
            elif bc_util < 30:
                score += 10  # Bonus por utilización baja

            # FACTOR 5: Ingreso anual
            annual_inc = input_data.get('annual_inc', 0)
            if annual_inc > 100000:
                score += 15  # Bonus por ingreso alto
            elif annual_inc > 70000:
                score += 5
            elif annual_inc < 30000:
                score -= 20

            # FACTOR 6: Último pago
            last_pymnt_amnt = input_data.get('last_pymnt_amnt', 0)
            if last_pymnt_amnt == 0:
                score -= 30
            elif last_pymnt_amnt < 100:
                score -= 15
            elif last_pymnt_amnt > 300:
                score += 5

            # FACTOR 7: Recuperaciones (0 es bueno)
            recoveries = input_data.get('recoveries', 0)
            if recoveries > 1000:
                score -= 35
            elif recoveries > 100:
                score -= 20
            elif recoveries > 0:
                score -= 10

            # Asegurar que el score esté entre 0 y 100
            score = max(0, min(100, score))

            print(f"📊 Puntuación de perfil calculada: {score}/100")

            return score

        except Exception as e:
            print(f"Error en calculate_profile_score: {e}")
            return 50  # Valor por defecto

    def get_model_info(self):
        """Obtener información del modelo"""
        return self.model_info

    def set_threshold(self, threshold):
        """Establecer umbral de decisión"""
        self.threshold = threshold
        print(f"⚙️ Umbral actualizado a: {threshold:.3f}")


# Instancia global del predictor
prediction_manager = PredictionManager()