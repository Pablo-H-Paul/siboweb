"""
Autenticación con Supabase.
Expone login(), logout() y get_user().
Las credenciales se leen de variables de entorno (.env local o Streamlit Secrets en producción).
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


@st.cache_resource
def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Faltan SUPABASE_URL y/o SUPABASE_ANON_KEY. "
            "Definilas en .env (local) o en Streamlit Secrets (producción)."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def login(email: str, password: str) -> dict | None:
    """
    Intenta autenticar al usuario.
    Si tiene éxito guarda la sesión en st.session_state y retorna el user.
    Retorna None si las credenciales son incorrectas.
    """
    try:
        client = _get_client()
        resp   = client.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"]         = resp.user
        st.session_state["access_token"] = resp.session.access_token
        return resp.user
    except Exception:
        return None


def logout():
    """Cierra la sesión y limpia el estado."""
    try:
        _get_client().auth.sign_out()
    except Exception:
        pass
    for key in ["user", "access_token"]:
        st.session_state.pop(key, None)


def get_user():
    """Retorna el usuario autenticado o None."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    return get_user() is not None
