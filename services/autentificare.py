"""Login securizat prin Auth0 (folosind st.login din Streamlit).

Auth0 se ocupă de parole, cod prin email/SMS, Google etc. Noi primim doar cine e omul
(„sub” = id-ul unic Auth0, plus email și nume) și îl legăm de un cont SKILLIO.

Configurarea stă în .streamlit/secrets.toml (model: .streamlit/secrets.toml.example):
    [auth]
    redirect_uri = "http://localhost:8501/oauth2callback"
    cookie_secret = "un-sir-lung-si-aleatoriu"
    [auth.auth0]
    client_id = "..."
    client_secret = "..."
    server_metadata_url = "https://DOMENIUL-TAU.auth0.com/.well-known/openid-configuration"

Fără acest fișier, aplicația folosește intrarea demo cu numărul de telefon.
"""
import streamlit as st

from core import config, logica

PROVIDER = "auth0"


def activ() -> bool:
    try:
        return "auth" in st.secrets and PROVIDER in st.secrets["auth"]
    except Exception:          # nu există secrets.toml
        return False


def logat() -> bool:
    try:
        return activ() and bool(st.user.is_logged_in)
    except Exception:
        return False


def info() -> dict:
    """Ce știe Auth0 despre omul logat."""
    if not logat():
        return {}
    u = st.user
    return {"sub": u.get("sub"), "email": u.get("email"), "nume": u.get("name") or u.get("nickname") or "",
            "telefon": u.get("phone_number") or ""}


def user_curent():
    """Contul SKILLIO al omului logat prin Auth0, sau None (nelogat sau fără profil încă)."""
    i = info()
    if not i.get("sub"):
        return None
    return logica.user_dupa_auth(i["sub"], i.get("email"))


def intra():
    st.login(PROVIDER)


def iesi():
    if logat():
        st.logout()


def e_admin_dupa_email(email) -> bool:
    return bool(email) and email.lower() in config.ADMIN_EMAILS
