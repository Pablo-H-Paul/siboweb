"""
Autenticación con Supabase.
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
        raise ValueError("Faltan SUPABASE_URL y/o SUPABASE_ANON_KEY.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def login(email: str, password: str):
    try:
        client = _get_client()
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = resp.user
        st.session_state["access_token"] = resp.session.access_token
        return resp.user
    except Exception:
        return None


def logout():
    try:
        _get_client().auth.sign_out()
    except Exception:
        pass
    for key in ["user", "access_token"]:
        st.session_state.pop(key, None)


def get_user():
    return st.session_state.get("user")


def is_authenticated() -> bool:
    return get_user() is not None
