"""
Módulo para manejar conexión a MySQL - VERSIÓN MYSQL
"""
import pandas as pd
from datetime import datetime
import json
import os
import numpy as np
from dotenv import load_dotenv
import streamlit as st
from sqlalchemy import create_engine, text, exc
from urllib.parse import quote_plus

# Cargar variables de entorno
load_dotenv()


class DatabaseManager:
    """Gestor de base de datos MySQL - VERSIÓN CORREGIDA"""

    def __init__(self):
        self.host = os.getenv('DB_HOST', 'sql.freedb.tech')
        self.port = os.getenv('DB_PORT', '3306')
        self.database = os.getenv('DB_NAME', 'freedb_CreditRiskDB')
        self.username = os.getenv('DB_USER', 'freedb_user_credit')
        self.password = os.getenv('DB_PASSWORD', 'w%%u6AW5EPy3rc6')
        self.engine = None
        self.connection = None
        self._init_engine()

    def _init_engine(self):
        """Inicializar motor de SQLAlchemy para MySQL"""
        try:
            # Codificar la contraseña para URL
            encoded_password = quote_plus(self.password)

            # Crear string de conexión para MySQL
            connection_string = f"mysql+mysqlconnector://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"

            self.engine = create_engine(
                connection_string,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'connect_timeout': 10,
                    'charset': 'utf8mb4'
                }
            )

            # Probar conexión
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            st.success("✅ Motor MySQL SQLAlchemy inicializado correctamente")
            return True
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al inicializar motor MySQL: {str(e)}")
            import traceback
            traceback.print_exc()
            self.engine = None
            return False

    def get_connection(self):
        """Obtener conexión directa"""
        try:
            if not self.engine:
                self._init_engine()

            return self.engine.connect()
        except Exception as e:
            st.error(f"❌ Error al obtener conexión: {str(e)}")
            return None

    def convert_numpy_types(self, value):
        """Convertir tipos numpy a tipos nativos de Python"""
        if isinstance(value, np.integer):
            return int(value)
        elif isinstance(value, np.floating):
            return float(value)
        elif isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        return value

    def save_user(self, email, full_name, hashed_password):
        """Guardar nuevo usuario en la base de datos"""
        if not self.engine:
            st.error("❌ Motor de base de datos no disponible")
            return False

        try:
            with self.engine.connect() as conn:
                stmt = text("""
                            INSERT INTO users (email, full_name, hashed_password, created_at, is_active)
                            VALUES (:email, :full_name, :hashed_password, NOW(), 1)
                            """)

                conn.execute(stmt, {
                    'email': email,
                    'full_name': full_name,
                    'hashed_password': hashed_password
                })
                conn.commit()

            return True
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al guardar usuario: {str(e)}")
            return False

    def get_user_by_email(self, email):
        """Obtener usuario por email"""
        if not self.engine:
            return None

        try:
            with self.engine.connect() as conn:
                stmt = text("""
                            SELECT id, email, full_name, hashed_password
                            FROM users
                            WHERE email = :email
                              AND is_active = 1
                            """)

                result = conn.execute(stmt, {'email': email}).fetchone()

                if result:
                    return {
                        'id': int(result[0]),
                        'email': result[1],
                        'full_name': result[2],
                        'hashed_password': result[3]
                    }
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al obtener usuario: {str(e)}")

        return None

    def save_prediction(self, user_id, input_data, results):
        """Guardar predicción en la base de datos - VERSIÓN MySQL"""
        if not self.engine:
            st.error("❌ Motor de base de datos no disponible")
            return None

        try:
            user_id = self.convert_numpy_types(user_id)
            details_json = json.dumps(results.get('details', {}))

            with self.engine.connect() as conn:
                stmt = text("""
                            INSERT INTO predictions (user_id, out_prncp, out_prncp_inv, last_pymnt_amnt,
                                                     total_rec_prncp, recoveries, collection_recovery_fee,
                                                     total_pymnt, installment, funded_amnt_inv,
                                                     total_pymnt_inv, total_rec_int, hardship_payoff_balance_amount,
                                                     orig_projected_additional_accrued_interest, int_rate,
                                                     hardship_amount, total_rec_late_fee, hardship_last_payment_amount,
                                                     dti, annual_inc, bc_util, risk_probability,
                                                     decision, risk_level, threshold_used, model_used,
                                                     profile_score, details_json, created_at)
                            VALUES (:user_id, :out_prncp, :out_prncp_inv, :last_pymnt_amnt,
                                    :total_rec_prncp, :recoveries, :collection_recovery_fee,
                                    :total_pymnt, :installment, :funded_amnt_inv,
                                    :total_pymnt_inv, :total_rec_int, :hardship_payoff_balance_amount,
                                    :orig_projected_additional_accrued_interest, :int_rate,
                                    :hardship_amount, :total_rec_late_fee, :hardship_last_payment_amount,
                                    :dti, :annual_inc, :bc_util, :risk_probability,
                                    :decision, :risk_level, :threshold_used, :model_used,
                                    :profile_score, :details_json, NOW())
                            """)

                params = {
                    'user_id': user_id,
                    'out_prncp': float(input_data.get('out_prncp', 0)),
                    'out_prncp_inv': float(input_data.get('out_prncp_inv', 0)),
                    'last_pymnt_amnt': float(input_data.get('last_pymnt_amnt', 0)),
                    'total_rec_prncp': float(input_data.get('total_rec_prncp', 0)),
                    'recoveries': float(input_data.get('recoveries', 0)),
                    'collection_recovery_fee': float(input_data.get('collection_recovery_fee', 0)),
                    'total_pymnt': float(input_data.get('total_pymnt', 0)),
                    'installment': float(input_data.get('installment', 0)),
                    'funded_amnt_inv': float(input_data.get('funded_amnt_inv', 0)),
                    'total_pymnt_inv': float(input_data.get('total_pymnt_inv', 0)),
                    'total_rec_int': float(input_data.get('total_rec_int', 0)),
                    'hardship_payoff_balance_amount': float(input_data.get('hardship_payoff_balance_amount', 0)),
                    'orig_projected_additional_accrued_interest': float(
                        input_data.get('orig_projected_additional_accrued_interest', 0)),
                    'int_rate': float(input_data.get('int_rate', 0)),
                    'hardship_amount': float(input_data.get('hardship_amount', 0)),
                    'total_rec_late_fee': float(input_data.get('total_rec_late_fee', 0)),
                    'hardship_last_payment_amount': float(input_data.get('hardship_last_payment_amount', 0)),
                    'dti': float(input_data.get('dti', 0)),
                    'annual_inc': float(input_data.get('annual_inc', 0)),
                    'bc_util': float(input_data.get('bc_util', 0)),
                    'risk_probability': float(results.get('probability', 0)),
                    'decision': str(results.get('decision', '')),
                    'risk_level': str(results.get('risk_level', '')),
                    'threshold_used': float(results.get('threshold', 0.4)),
                    'model_used': str(results.get('model_used', 'Random Forest')),
                    'profile_score': int(results.get('profile_score', 0)),
                    'details_json': details_json
                }

                conn.execute(stmt, params)
                conn.commit()

                # Obtener último ID insertado (MySQL)
                result = conn.execute(text("SELECT LAST_INSERT_ID() as last_id"))
                prediction_id = result.scalar()

                return int(prediction_id) if prediction_id else None

        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al guardar predicción: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def get_user_predictions(self, user_id, limit=50):
        """Obtener historial de predicciones del usuario"""
        if not self.engine:
            return pd.DataFrame()

        try:
            user_id = self.convert_numpy_types(user_id)

            query = """
                    SELECT id, \
                           created_at, \
                           risk_probability, \
                           decision, \
                           risk_level, \
                           threshold_used, \
                           model_used, \
                           profile_score, \
                           out_prncp, \
                           dti, \
                           annual_inc
                    FROM predictions
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC LIMIT :limit \
                    """

            df = pd.read_sql(
                text(query),
                self.engine,
                params={'limit': limit, 'user_id': user_id}
            )

            return df

        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al obtener predicciones: {str(e)}")
            return pd.DataFrame()

    def get_prediction_details(self, prediction_id, user_id):
        """Obtener detalles completos de una predicción"""
        if not self.engine:
            return None

        try:
            prediction_id = self.convert_numpy_types(prediction_id)
            user_id = self.convert_numpy_types(user_id)

            with self.engine.connect() as conn:
                stmt = text("""
                            SELECT *
                            FROM predictions
                            WHERE id = :prediction_id
                              AND user_id = :user_id
                            """)

                cursor = conn.execute(stmt, {
                    'prediction_id': prediction_id,
                    'user_id': user_id
                })
                result = cursor.fetchone()

                if result:
                    columns = cursor.keys()
                    details = {}

                    for idx, column in enumerate(columns):
                        value = result[idx]
                        details[column] = self.convert_numpy_types(value)

                    return details

        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al obtener detalles: {str(e)}")
            import traceback
            traceback.print_exc()

        return None

    def update_user_password(self, user_id, new_hashed_password):
        """Actualizar contraseña del usuario"""
        if not self.engine:
            st.error("❌ Motor de base de datos no disponible")
            return False

        try:
            with self.engine.connect() as conn:
                stmt = text("""
                            UPDATE users
                            SET hashed_password = :new_password,
                                updated_at      = NOW()
                            WHERE id = :user_id
                            """)

                conn.execute(stmt, {
                    'new_password': new_hashed_password,
                    'user_id': user_id
                })
                conn.commit()

                return True
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al actualizar contraseña: {str(e)}")
            return False

    def update_user_profile(self, user_id, full_name, email=None):
        """Actualizar perfil del usuario"""
        if not self.engine:
            st.error("❌ Motor de base de datos no disponible")
            return False, "Base de datos no disponible"

        try:
            with self.engine.connect() as conn:
                if email:
                    # Verificar si el email ya existe
                    check_stmt = text("""
                                      SELECT id
                                      FROM users
                                      WHERE email = :email
                                        AND id != :user_id
                                      """)

                    existing = conn.execute(check_stmt, {
                        'email': email,
                        'user_id': user_id
                    }).fetchone()

                    if existing:
                        return False, "❌ Este email ya está en uso por otro usuario"

                    # Actualizar email y nombre
                    update_stmt = text("""
                                       UPDATE users
                                       SET full_name  = :full_name,
                                           email      = :email,
                                           updated_at = NOW()
                                       WHERE id = :user_id
                                       """)

                    conn.execute(update_stmt, {
                        'full_name': full_name,
                        'email': email,
                        'user_id': user_id
                    })
                else:
                    # Solo actualizar nombre
                    update_stmt = text("""
                                       UPDATE users
                                       SET full_name  = :full_name,
                                           updated_at = NOW()
                                       WHERE id = :user_id
                                       """)

                    conn.execute(update_stmt, {
                        'full_name': full_name,
                        'user_id': user_id
                    })

                conn.commit()
                return True, "✅ Perfil actualizado exitosamente"

        except exc.SQLAlchemyError as e:
            return False, f"❌ Error al actualizar perfil: {str(e)}"

    def test_connection(self):
        """Probar conexión a la base de datos"""
        if not self.engine:
            return False

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                return result[0] == 1
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error en test de conexión: {str(e)}")
            return False

    def execute_query(self, query, params=None):
        """Ejecutar query personalizada"""
        if not self.engine:
            return None

        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))

                conn.commit()
                return result
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error ejecutando query: {str(e)}")
            return None

    def get_dataframe(self, query, params=None):
        """Obtener DataFrame desde una query"""
        if not self.engine:
            return pd.DataFrame()

        try:
            if params:
                df = pd.read_sql(text(query), self.engine, params=params)
            else:
                df = pd.read_sql(text(query), self.engine)

            return df
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error obteniendo DataFrame: {str(e)}")
            return pd.DataFrame()

    def create_database_if_not_exists(self):
        """Crear la base de datos si no existe"""
        try:
            # Conectar sin especificar base de datos
            temp_engine = create_engine(
                f"mysql+mysqlconnector://{self.username}:{quote_plus(self.password)}@{self.host}:{self.port}/",
                echo=False
            )

            with temp_engine.connect() as conn:
                # Crear base de datos si no existe
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.database}"))
                conn.execute(text(f"USE {self.database}"))

            st.success(f"✅ Base de datos '{self.database}' verificada/creada")
            return True
        except exc.SQLAlchemyError as e:
            st.error(f"❌ Error al crear base de datos: {str(e)}")
            return False


# ⭐⭐ ESTA ES LA LÍNEA IMPORTANTE ⭐⭐
# Crear instancia global que se importará en otros módulos
db_manager = DatabaseManager()