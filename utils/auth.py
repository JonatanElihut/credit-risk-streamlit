# auth.py
"""
Módulo para manejar autenticación de usuarios
"""
import bcrypt
import streamlit as st
from utils.database import db_manager
import re


class AuthManager:
    """Gestor de autenticación de usuarios"""

    def __init__(self):
        # NO inicializar session_state aquí
        pass

    def _ensure_session_state(self):
        """Garantizar que el session_state esté inicializado"""
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False

    def hash_password(self, password):
        """Hashear contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, hashed_password):
        """Verificar contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def validate_email(self, email):
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def register_user(self, email, full_name, password, confirm_password):
        """Registrar nuevo usuario"""
        # Validaciones
        if not self.validate_email(email):
            return False, "❌ Email inválido"

        if len(password) < 8:
            return False, "❌ La contraseña debe tener al menos 8 caracteres"

        if password != confirm_password:
            return False, "❌ Las contraseñas no coinciden"

        # Verificar si el usuario ya existe
        existing_user = db_manager.get_user_by_email(email)
        if existing_user:
            return False, "❌ Este email ya está registrado"

        # Hashear contraseña
        hashed_password = self.hash_password(password)

        # Guardar en base de datos
        if db_manager.save_user(email, full_name, hashed_password):
            return True, "✅ Usuario registrado exitosamente"
        else:
            return False, "❌ Error al registrar usuario"

    def login_user(self, email, password):
        """Iniciar sesión de usuario"""
        # Obtener usuario
        user = db_manager.get_user_by_email(email)

        if not user:
            return False, "❌ Usuario no encontrado"

        # Verificar contraseña
        if self.verify_password(password, user['hashed_password']):
            # Actualizar estado de sesión
            self._ensure_session_state()
            st.session_state.user = user
            st.session_state.authenticated = True
            return True, "✅ Inicio de sesión exitoso"
        else:
            return False, "❌ Contraseña incorrecta"

    def logout(self):
        """Cerrar sesión"""
        self._ensure_session_state()
        st.session_state.user = None
        st.session_state.authenticated = False

    def is_authenticated(self):
        """Verificar si el usuario está autenticado"""
        self._ensure_session_state()
        return st.session_state.authenticated

    def get_current_user(self):
        """Obtener usuario actual"""
        self._ensure_session_state()
        return st.session_state.user

    def require_auth(self):
        """Redirigir a login si no está autenticado"""
        if not self.is_authenticated():
            st.warning("🔐 Por favor, inicie sesión para acceder a esta página")
            st.stop()

    # auth.py - Agrega estos métodos en la clase AuthManager

    def update_password(self, user_id, current_password, new_password, confirm_password):
        """Actualizar contraseña del usuario"""
        # Validaciones
        if not current_password:
            return False, "❌ Ingrese su contraseña actual"

        if len(new_password) < 8:
            return False, "❌ La nueva contraseña debe tener al menos 8 caracteres"

        if new_password != confirm_password:
            return False, "❌ Las nuevas contraseñas no coinciden"

        if current_password == new_password:
            return False, "❌ La nueva contraseña debe ser diferente a la actual"

        # Obtener usuario para verificar contraseña actual
        user = self.get_current_user()
        if not user:
            return False, "❌ No se pudo obtener información del usuario"

        # Verificar contraseña actual
        if not self.verify_password(current_password, user['hashed_password']):
            return False, "❌ Contraseña actual incorrecta"

        # Hashear nueva contraseña
        new_hashed_password = self.hash_password(new_password)

        # Actualizar en base de datos
        if db_manager.update_user_password(user_id, new_hashed_password):
            # Actualizar en session state si es el usuario actual
            if user_id == user['id']:
                user['hashed_password'] = new_hashed_password
                st.session_state.user = user

            return True, "✅ Contraseña actualizada exitosamente"
        else:
            return False, "❌ Error al actualizar la contraseña"

    def update_profile(self, user_id, full_name, email=None):
        """Actualizar perfil del usuario"""
        if not full_name or len(full_name.strip()) < 3:
            return False, "❌ El nombre debe tener al menos 3 caracteres"

        if email and not self.validate_email(email):
            return False, "❌ Email inválido"

        # Actualizar en base de datos
        success, message = db_manager.update_user_profile(user_id, full_name, email)

        if success:
            # Actualizar en session state si es el usuario actual
            user = self.get_current_user()
            if user and user_id == user['id']:
                user['full_name'] = full_name
                if email:
                    user['email'] = email
                st.session_state.user = user

        return success, message


# Instancia global de autenticación
auth_manager = AuthManager()