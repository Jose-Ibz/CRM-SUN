"""
crm.py — CRM de Visitas Comerciales · Náutica Viamar
Stack: Python + Streamlit + PostgreSQL (Supabase) + Claude API
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go

import crm_db as db
import crm_ia as ia

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CRM Visitas · Sun Ibiza",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar DB (crea tablas si no existen)
@st.cache_resource
def init_db():
    db.inicializar_db()

init_db()

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Google Font: Inter ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Base ── */
    html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox,
    .stTextArea, .stButton, .stRadio, .stCheckbox, .stExpander,
    [data-testid="stSidebar"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ── Fondo principal ── */
    .main { background: #f1f5f9 !important; }
    .block-container {
        padding: 1.8rem 2.4rem 3rem !important;
        max-width: 1400px !important;
    }

    /* ── Sidebar oscuro ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(175deg, #0c1e35 0%, #162d4a 60%, #1a3a5c 100%) !important;
        border-right: none !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span:not([data-testid]),
    section[data-testid="stSidebar"] small {
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f1f5f9 !important;
    }
    /* Radio de navegación en sidebar */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 4px !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 8px !important;
        padding: 9px 14px !important;
        transition: background 0.15s ease !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.92em !important;
        cursor: pointer !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.1) !important;
        color: #f1f5f9 !important;
    }
    /* Input en sidebar */
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    /* Separadores sidebar */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
    }
    /* Botón cerrar sesión en sidebar */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.08) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.15) !important;
        color: #f1f5f9 !important;
        border-color: rgba(255,255,255,0.3) !important;
    }

    /* ── KPI Cards ── */
    [data-testid="metric-container"] {
        background: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 20px 22px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05), 0 4px 20px rgba(0,0,0,0.04) !important;
        border-top: 3px solid #3b82f6 !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease !important;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stMetricLabel"] > div {
        font-size: 0.73em !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
        color: #64748b !important;
    }
    [data-testid="stMetricValue"] > div {
        font-size: 1.75em !important;
        font-weight: 700 !important;
        color: #0f2444 !important;
        line-height: 1.2 !important;
    }

    /* ── Botones ── */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a3a5c 0%, #2563eb 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px !important;
        padding: 10px 22px !important;
        box-shadow: 0 2px 10px rgba(37,99,235,0.22) !important;
        transition: all 0.18s ease !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(37,99,235,0.35) !important;
    }
    .stButton > button:not([kind="primary"]),
    .stFormSubmitButton > button:not([kind="primary"]) {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        background: white !important;
        color: #374151 !important;
        font-weight: 500 !important;
        transition: all 0.18s ease !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: #f8fafc !important;
        border-color: #3b82f6 !important;
        color: #1a3a5c !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        font-size: 0.94em !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
        background: white !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    }
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        font-size: 0.94em !important;
        transition: border-color 0.15s ease !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    }
    .stSelectbox > div > div > div {
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        font-size: 0.94em !important;
        background: white !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: white !important;
        border-radius: 12px !important;
        padding: 5px !important;
        border: 1.5px solid #e2e8f0 !important;
        gap: 3px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 500 !important;
        color: #64748b !important;
        font-size: 0.9em !important;
        padding: 8px 14px !important;
        transition: all 0.15s !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1a3a5c 0%, #2563eb 100%) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 12px !important;
        border: 1.5px solid #e2e8f0 !important;
        font-weight: 600 !important;
        color: #1a2b4a !important;
        padding: 12px 16px !important;
    }
    .streamlit-expanderContent {
        background: white !important;
        border: 1.5px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    }

    /* ── Chat IA ── */
    .chat-user {
        background: linear-gradient(135deg, #1a3a5c 0%, #2563eb 100%);
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0 8px 22%;
        font-size: 0.93em;
        line-height: 1.65;
        box-shadow: 0 2px 10px rgba(37,99,235,0.2);
    }
    .chat-bot {
        background: white;
        border: 1.5px solid #e2e8f0;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 18px;
        margin: 8px 22% 8px 0;
        font-size: 0.93em;
        line-height: 1.65;
        box-shadow: 0 1px 6px rgba(0,0,0,0.05);
        color: #1a2b4a;
    }
    .chat-wrapper {
        max-height: 420px;
        overflow-y: auto;
        padding: 12px 14px;
        background: #f8fafc;
        border-radius: 14px;
        margin-bottom: 12px;
        border: 1.5px solid #e2e8f0;
    }

    /* ── Alertas ── */
    .alerta {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 0.9em;
        box-shadow: 0 1px 4px rgba(245,158,11,0.08);
    }

    /* ── Títulos ── */
    h1 {
        color: #0f2444 !important;
        font-weight: 700 !important;
        letter-spacing: -0.4px !important;
        margin-bottom: 0.2rem !important;
    }
    h2, h3 {
        color: #1a3a5c !important;
        font-weight: 600 !important;
        letter-spacing: -0.3px !important;
    }
    .section-title {
        font-size: 1em;
        font-weight: 700;
        color: #0f2444;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
        letter-spacing: -0.2px;
    }

    /* ── Mensajes de estado ── */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }
    .stSuccess > div {
        background: #f0fdf4 !important;
        border-left: 4px solid #22c55e !important;
        border-radius: 10px !important;
    }
    .stInfo > div {
        background: #eff6ff !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 10px !important;
    }
    .stWarning > div {
        background: #fffbeb !important;
        border-left: 4px solid #f59e0b !important;
        border-radius: 10px !important;
    }
    .stError > div {
        background: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 10px !important;
    }

    /* ── Captions ── */
    .stCaption {
        color: #94a3b8 !important;
        font-size: 0.82em !important;
    }

    /* ── Divisores ── */
    hr {
        border: none !important;
        border-top: 1.5px solid #e2e8f0 !important;
        opacity: 1 !important;
        margin: 1.2rem 0 !important;
    }

    /* ── Formularios ── */
    [data-testid="stForm"] {
        background: white;
        border-radius: 16px;
        padding: 24px 28px;
        border: 1.5px solid #e2e8f0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "chat_historia" not in st.session_state:
    st.session_state.chat_historia = []
if "rol" not in st.session_state:
    st.session_state.rol = None  # None = no logueado
if "cliente_id_nueva_visita" not in st.session_state:
    st.session_state.cliente_id_nueva_visita = None
if "login_intentos" not in st.session_state:
    st.session_state.login_intentos = 0
if "login_bloqueado_hasta" not in st.session_state:
    st.session_state.login_bloqueado_hasta = None


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
_MAX_INTENTOS = 5
_BLOQUEO_SEGUNDOS = 300  # 5 minutos


def _get_pwd():
    """Devuelve (pwd_control_list, pwd_comercial_str) desde secrets o valores de entorno."""
    try:
        return list(st.secrets["PWD_CONTROL"]), str(st.secrets["PWD_COMERCIAL"])
    except Exception:
        # Fallback a variables de entorno para desarrollo local
        import os
        ctrl = os.environ.get("PWD_CONTROL", "").split(",")
        com  = os.environ.get("PWD_COMERCIAL", "")
        if ctrl and com:
            return [c.strip() for c in ctrl if c.strip()], com.strip()
        # Si no hay nada configurado, bloquear con un mensaje claro
        return [], ""


def _login_bloqueado() -> bool:
    """Devuelve True si el usuario está bloqueado por intentos fallidos."""
    from datetime import datetime as _dt
    hasta = st.session_state.login_bloqueado_hasta
    if hasta and _dt.now() < hasta:
        secs = int((hasta - _dt.now()).total_seconds())
        st.error(f"Demasiados intentos fallidos. Espera {secs} segundos.")
        return True
    if hasta and _dt.now() >= hasta:
        st.session_state.login_intentos = 0
        st.session_state.login_bloqueado_hasta = None
    return False


def _registrar_intento_fallido():
    from datetime import datetime as _dt, timedelta as _td
    st.session_state.login_intentos += 1
    if st.session_state.login_intentos >= _MAX_INTENTOS:
        st.session_state.login_bloqueado_hasta = _dt.now() + _td(seconds=_BLOQUEO_SEGUNDOS)
        st.error(f"Cuenta bloqueada por {_BLOQUEO_SEGUNDOS // 60} minutos tras {_MAX_INTENTOS} intentos fallidos.")
    else:
        restantes = _MAX_INTENTOS - st.session_state.login_intentos
        st.error(f"Contraseña incorrecta. Intentos restantes: {restantes}")


def _verificar_clave(clave: str) -> str | None:
    """Devuelve el rol si la clave es correcta, None si no."""
    pwd_control, pwd_comercial = _get_pwd()
    if not pwd_control and not pwd_comercial:
        st.error("Las contraseñas no están configuradas. Añade PWD_CONTROL y PWD_COMERCIAL en secrets.")
        return None
    if clave in pwd_control:
        return "control"
    if pwd_comercial and clave == pwd_comercial:
        return "comercial"
    return None


def pantalla_login():
    # Fondo de pantalla completa para login
    st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #0c1e35 0%, #1a3a5c 50%, #0f2444 100%) !important; }
        .block-container { display: flex; align-items: center; justify-content: center;
                           min-height: 90vh; padding: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    col_center = st.columns([1, 1.6, 1])[1]
    with col_center:
        st.markdown("""
        <div style="background:white;border-radius:20px;padding:40px 44px 36px;
                    box-shadow:0 20px 60px rgba(0,0,0,0.25);text-align:center;">
        """, unsafe_allow_html=True)

        try:
            st.image("logo.png", width=180)
        except Exception:
            st.markdown("""
            <div style="font-size:2.5em;margin-bottom:4px">⚓</div>
            <div style="font-size:1.4em;font-weight:800;color:#0f2444;letter-spacing:-0.5px">
                Viamar CRM
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="color:#64748b;font-size:0.9em;margin:8px 0 24px;font-weight:500">
            CRM de Visitas Comerciales · Sun Ibiza
        </div>
        </div>
        """, unsafe_allow_html=True)

        if _login_bloqueado():
            st.stop()

        clave = st.text_input("Contraseña", type="password",
                              placeholder="Introduce tu contraseña",
                              label_visibility="collapsed")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Entrar →", type="primary", use_container_width=True):
            rol = _verificar_clave(clave)
            if rol:
                st.session_state.rol = rol
                st.session_state.login_intentos = 0
                st.rerun()
            else:
                _registrar_intento_fallido()

        st.markdown("""
        <div style="text-align:center;margin-top:18px;color:#94a3b8;font-size:0.78em">
            ☀️ Sun Ibiza · Náutica Viamar
        </div>
        """, unsafe_allow_html=True)

# Detectar modo visita rápida por URL (?modo=visita)
MODO_VISITA = st.query_params.get("modo", "") == "visita"

if st.session_state.rol is None:
    # En modo visita el login es más simple
    if MODO_VISITA:
        col = st.columns([1, 2, 1])[1]
        with col:
            try:
                st.image("logo.png", width=160)
            except Exception:
                st.markdown("## ☀️ Sun Ibiza")
            st.markdown("### ➕ Registrar Visita")
            if _login_bloqueado():
                st.stop()
            clave_v = st.text_input("Contraseña", type="password", key="pwd_visita")
            if st.button("Entrar", type="primary", use_container_width=True):
                rol = _verificar_clave(clave_v)
                if rol:
                    st.session_state.rol = rol
                    st.session_state.login_intentos = 0
                    st.rerun()
                else:
                    _registrar_intento_fallido()
        st.stop()
    else:
        pantalla_login()
        st.stop()

# ── MODO VISITA RÁPIDA ──────────────────────────
if MODO_VISITA:
    # Pantalla completa optimizada para móvil
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none; }
        .block-container { padding: 1rem 1rem; max-width: 600px; margin: auto; }
        div[data-testid="stForm"] { background: white; border-radius: 12px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

    try:
        st.image("logo.png", width=130)
    except Exception:
        pass
    st.markdown("## ➕ Nueva Visita")

    try:
        comerciales_v = db.get_comerciales()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.stop()

    # Selector de cliente
    modo_v = st.radio("", ["Buscar cliente", "Cliente nuevo"], horizontal=True, key="modo_v")

    cliente_id_v = st.session_state.get("cliente_id_nueva_visita")

    if modo_v == "Buscar cliente":
        busq_v = st.text_input("Nombre o teléfono", key="busq_v")
        clientes_v = db.get_clientes(busqueda=busq_v if busq_v else None)
        if clientes_v:
            opciones_v = {f"{c['nombre']} · {c.get('zona','-')}": c["id"] for c in clientes_v}
            sel_v = st.selectbox("Cliente", list(opciones_v.keys()), key="sel_cl_v")
            st.session_state.cliente_id_nueva_visita = opciones_v[sel_v]
            cliente_id_v = opciones_v[sel_v]
    else:
        nv1, nv2, nv3 = st.columns(3)
        n_nom_v  = nv1.text_input("Nombre *", key="n_nom_v")
        n_tel_v  = nv2.text_input("Teléfono", key="n_tel_v")
        n_zona_v = nv3.text_input("Zona", key="n_zona_v")
        if st.button("Crear cliente", type="primary", key="btn_crear_cl_v"):
            if n_nom_v.strip():
                nid_v = db.add_cliente(n_nom_v, n_tel_v, n_zona_v)
                st.session_state.cliente_id_nueva_visita = nid_v
                st.success(f"✅ {n_nom_v} creado")
                st.rerun()
            else:
                st.error("El nombre es obligatorio")

    cliente_id_v = st.session_state.get("cliente_id_nueva_visita")
    if cliente_id_v:
        cl_v = db.get_cliente(cliente_id_v)
        if cl_v:
            st.info(f"✅ **{cl_v['nombre']}** · {cl_v.get('zona','-')}")

    st.markdown("---")

    # Comercial
    nombres_com_v = [c["nombre"] for c in comerciales_v]
    comercial_v = st.selectbox("Comercial", nombres_com_v, key="com_v")
    comercial_obj_v = next(c for c in comerciales_v if c["nombre"] == comercial_v)

    from datetime import datetime as _dt_v
    ahora_v = _dt_v.now()
    st.info(f"🕐 **{ahora_v.strftime('%d/%m/%Y %H:%M')}**")

    _TIPO_OPS = ["Presencial", "Telefónico", "Email", "Videollamada", "Feria/Evento"]
    _OPO_OPS  = ["Ninguna", "Baja", "Media", "Alta"]

    with st.form("form_visita_rapida", clear_on_submit=True):
        vr1, vr2 = st.columns(2)
        tipo_vr  = vr1.selectbox("Tipo", _TIPO_OPS, key="tipo_vr")
        opo_vr   = vr2.selectbox("Oportunidad", _OPO_OPS, key="opo_vr")
        temas_vr = st.text_input("Temas", placeholder="Antifouling, Sadira, motor...", key="temas_vr")
        com_vr   = st.text_area("Comentarios *", height=140,
                                 placeholder="Qué se habló, estado del cliente, necesidades...",
                                 key="com_vr")
        st.markdown("**Seguimiento**")
        sr1, sr2 = st.columns(2)
        seg_vr   = sr1.text_input("Acción pendiente", key="seg_vr")
        fseg_vr  = sr2.date_input("Fecha", value=date.today() + timedelta(days=7), key="fseg_vr")

        if st.form_submit_button("💾 GUARDAR VISITA", type="primary", use_container_width=True):
            if not cliente_id_v:
                st.error("Selecciona o crea un cliente primero.")
            elif not com_vr.strip():
                st.error("Los comentarios son obligatorios.")
            else:
                db.add_visita(
                    cliente_id=cliente_id_v,
                    comercial_id=comercial_obj_v["id"],
                    fecha=ahora_v.strftime("%Y-%m-%d %H:%M"),
                    tipo_contacto=tipo_vr,
                    comentarios=com_vr,
                    temas=temas_vr,
                    seguimiento=seg_vr,
                    fecha_seguimiento=fseg_vr if seg_vr else None,
                    oportunidad=opo_vr,
                    importe_estimado=0
                )
                st.session_state.cliente_id_nueva_visita = None
                st.success("✅ ¡Visita guardada!")
                st.balloons()
    st.stop()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
TIPO_CONTACTO_OPS = ["Presencial", "Telefónico", "Email", "Videollamada", "Feria/Evento"]
OPORTUNIDAD_OPS   = ["Ninguna", "Baja", "Media", "Alta"]
COLOR_OPO = {"Ninguna": "#94a3b8", "Baja": "#60a5fa", "Media": "#f59e0b", "Alta": "#22c55e"}

def get_temas_ops():
    try:
        return db.get_temas()
    except Exception:
        return ["Precios", "Stock", "Garantía", "Soporte técnico", "Otro"]

def _api_key():
    """Obtiene la API key exclusivamente desde secrets de Streamlit."""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return ""


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("logo.png", width=180)
    except Exception:
        st.markdown("""
        <div style="text-align:center;padding:10px 0 4px">
            <span style="font-size:2em">⚓</span><br>
            <span style="color:#f1f5f9;font-size:1.1em;font-weight:700;letter-spacing:-0.3px">
                Viamar CRM
            </span>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:4px">
        <span style="color:#64748b;font-size:0.75em;letter-spacing:0.5px;text-transform:uppercase;
                     font-weight:600">CRM · Sun Ibiza</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Menú según rol
    if st.session_state.rol == "control":
        opciones_menu = ["📊 Dashboard", "➕ Nueva Visita", "📋 Visitas",
                         "👥 Clientes", "✅ Tareas", "📈 Informes IA", "⚙️ Configuración"]
    else:
        opciones_menu = ["➕ Nueva Visita", "📋 Visitas", "👥 Clientes", "✅ Tareas"]

    pagina = st.radio("Navegación", opciones_menu, label_visibility="collapsed")

    st.markdown("---")

    # Comercial activo
    try:
        comerciales = db.get_comerciales()
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        st.stop()

    nombres_com = [c["nombre"] for c in comerciales]
    if not nombres_com:
        st.warning("No hay comerciales. Añade uno.")
        st.stop()

    st.markdown('<span style="color:#64748b;font-size:0.78em;font-weight:600;'
                'text-transform:uppercase;letter-spacing:0.5px">Comercial activo</span>',
                unsafe_allow_html=True)
    comercial_sel_nombre = st.selectbox("Comercial", nombres_com, label_visibility="collapsed")
    comercial_sel = next(c for c in comerciales if c["nombre"] == comercial_sel_nombre)

    # Estado API IA solo en modo control
    if st.session_state.rol == "control":
        st.markdown("---")
        if _api_key():
            st.markdown("""
            <div style="background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.25);
                        border-radius:8px;padding:8px 12px;font-size:0.82em;color:#86efac;
                        display:flex;align-items:center;gap:6px">
                🤖 <span>API IA activa</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.25);
                        border-radius:8px;padding:8px 12px;font-size:0.82em;color:#fcd34d">
                ⚠️ API IA no configurada
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        with st.expander("➕ Añadir comercial"):
            nuevo_com = st.text_input("Nombre del comercial", key="input_nuevo_com",
                                       label_visibility="collapsed",
                                       placeholder="Nombre del comercial")
            if st.button("Añadir", use_container_width=True):
                if nuevo_com.strip():
                    try:
                        db.add_comercial(nuevo_com)
                        st.success("Añadido")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    st.markdown("---")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.rol = None
        st.rerun()


# ══════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════
if pagina == "📊 Dashboard":
    hoy_str = date.today().strftime("%A, %d de %B de %Y")
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                margin-bottom:1.4rem;">
        <div>
            <h1 style="margin:0;font-size:1.8em">Dashboard Comercial</h1>
            <span style="color:#64748b;font-size:0.9em;font-weight:500">{hoy_str}</span>
        </div>
        <div style="background:white;border-radius:12px;padding:10px 18px;
                    border:1.5px solid #e2e8f0;
                    box-shadow:0 1px 4px rgba(0,0,0,0.05);
                    color:#1a3a5c;font-weight:600;font-size:0.92em">
            👤 {comercial_sel_nombre}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs globales ──
    try:
        resumen = db.stats_resumen_global()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

    anyo_actual = date.today().year
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total visitas", resumen["total_visitas"])
    k2.metric("Visitas este mes", resumen["visitas_mes"])
    k3.metric("Visitas este año", resumen["visitas_anyo"])
    k4.metric("Clientes", resumen["total_clientes"])
    k5.metric("Pipeline total", f"{resumen['pipeline_euros']:,.0f} €")
    k6.metric("Oportunidades calientes", f"{resumen['pipeline_alta_euros']:,.0f} €")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Gráficos ──
    col_g1, col_g2, col_g3 = st.columns([2, 1, 1])

    with col_g1:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:20px 22px 10px;
                    border:1.5px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,0.04)">
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-title">📅 Visitas por mes</div>', unsafe_allow_html=True)
        anyo_sel = st.selectbox("Año", list(range(anyo_actual, anyo_actual - 4, -1)),
                                 key="anyo_dash", label_visibility="collapsed")
        stats_mes = db.stats_visitas_por_mes(anyo=anyo_sel)
        if stats_mes:
            df_mes = pd.DataFrame(stats_mes)
            todos_meses = [f"{anyo_sel}-{m:02d}" for m in range(1, 13)]
            df_mes = (pd.DataFrame({"mes": todos_meses})
                      .merge(df_mes, on="mes", how="left")
                      .fillna(0))
            df_mes["mes_label"] = df_mes["mes"].str[5:]
            fig = px.bar(df_mes, x="mes_label", y="total",
                         color_discrete_sequence=["#2563eb"],
                         labels={"mes_label": "", "total": "Visitas"})
            fig.update_layout(margin=dict(t=6, b=6, l=0, r=0), height=230,
                               plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="Inter, sans-serif"))
            fig.update_traces(marker_line_width=0, marker_cornerradius=4)
            fig.update_yaxes(gridcolor="#f1f5f9", gridwidth=1)
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos para este año")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_g2:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:20px 22px 10px;
                    border:1.5px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,0.04)">
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-title">📞 Tipo de contacto</div>', unsafe_allow_html=True)
        stats_tipo = db.stats_visitas_por_tipo()
        if stats_tipo:
            df_tipo = pd.DataFrame(stats_tipo)
            fig = px.pie(df_tipo, values="total", names="tipo_contacto",
                         color_discrete_sequence=["#2563eb","#0891b2","#7c3aed","#059669","#f59e0b"],
                         hole=0.45)
            fig.update_layout(margin=dict(t=6, b=6, l=0, r=0), height=230,
                               showlegend=True,
                               legend=dict(font=dict(size=10, family="Inter, sans-serif"),
                                           orientation="h", y=-0.15),
                               font=dict(family="Inter, sans-serif"))
            fig.update_traces(textfont=dict(family="Inter, sans-serif"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_g3:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:20px 22px 10px;
                    border:1.5px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,0.04)">
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Oportunidades</div>', unsafe_allow_html=True)
        stats_opo = db.stats_oportunidades()
        if stats_opo:
            df_opo = pd.DataFrame(stats_opo)
            COLOR_OPO_MODERN = {"Ninguna": "#cbd5e1", "Baja": "#60a5fa",
                                "Media": "#f59e0b", "Alta": "#22c55e"}
            fig = px.bar(df_opo, x="oportunidad", y="total",
                         color="oportunidad", color_discrete_map=COLOR_OPO_MODERN,
                         labels={"oportunidad": "", "total": "Nº visitas"})
            fig.update_layout(margin=dict(t=6, b=6, l=0, r=0), height=230,
                               showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="Inter, sans-serif"))
            fig.update_traces(marker_line_width=0, marker_cornerradius=4)
            fig.update_yaxes(gridcolor="#f1f5f9", gridwidth=1)
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Informe Agenda ──
    with st.expander("📄 Generar informe agenda de visitas (exportable a PDF)"):
        ag1, ag2, ag3 = st.columns([2, 2, 1])
        ag_desde = ag1.date_input("Desde", value=date.today().replace(day=1), key="ag_desde")
        ag_hasta = ag2.date_input("Hasta", value=date.today(), key="ag_hasta")
        ag_todos = ag3.checkbox("Todos los comerciales")

        if st.button("📋 Generar agenda", type="primary"):
            visitas_ag = db.get_visitas(
                comercial_id=None if ag_todos else comercial_sel["id"],
                fecha_desde=ag_desde,
                fecha_hasta=ag_hasta
            )
            if not visitas_ag:
                st.info("No hay visitas en ese periodo.")
            else:
                st.session_state["agenda_visitas"] = visitas_ag
                st.session_state["agenda_desde"]   = ag_desde
                st.session_state["agenda_hasta"]   = ag_hasta

        if "agenda_visitas" in st.session_state and st.session_state["agenda_visitas"]:
            visitas_ag = st.session_state["agenda_visitas"]
            ag_desde_s = st.session_state["agenda_desde"]
            ag_hasta_s = st.session_state["agenda_hasta"]

            COLOR_OPO_BD = {"Alta": "#22c55e", "Media": "#f59e0b", "Baja": "#60a5fa", "Ninguna": "#94a3b8"}

            # Construir HTML del informe
            filas_html = ""
            for v in visitas_ag:
                borde = COLOR_OPO_BD.get(v.get("oportunidad","Ninguna"), "#94a3b8")
                seg = ""
                if v.get("seguimiento"):
                    seg = f"<p style='margin:4px 0 0;font-size:0.85em;color:#64748b'>🔔 {v['seguimiento']}"
                    if v.get("fecha_seguimiento"):
                        seg += f" ({v['fecha_seguimiento']})"
                    seg += "</p>"
                filas_html += f"""
                <div style='border-left:4px solid {borde};padding:10px 14px;
                            margin-bottom:10px;background:#fafafa;border-radius:6px;
                            page-break-inside:avoid'>
                    <div style='display:flex;justify-content:space-between'>
                        <strong style='font-size:1em'>{v['fecha']} — {v['cliente_nombre']}</strong>
                        <span style='font-size:0.82em;color:#64748b'>{v['tipo_contacto']} | {v.get('oportunidad','')}</span>
                    </div>
                    {f"<p style='margin:4px 0;font-size:0.85em;color:#888'>🏷️ {v['temas']}</p>" if v.get('temas') else ''}
                    <p style='margin:6px 0 0;line-height:1.6'>{v.get('comentarios','')}</p>
                    {seg}
                </div>"""

            html_completo = f"""
            <html><head><meta charset='utf-8'>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 13px; color: #1a2b4a; padding: 24px; }}
                h1 {{ color: #1a2b4a; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; }}
                h2 {{ color: #1a73e8; font-size: 1em; margin-bottom: 16px; }}
                @media print {{ body {{ padding: 0; }} }}
            </style></head>
            <body>
                <h1>📋 Informe de Visitas — Sun Ibiza</h1>
                <h2>Periodo: {ag_desde_s.strftime('%d/%m/%Y')} — {ag_hasta_s.strftime('%d/%m/%Y')} &nbsp;|&nbsp; {len(visitas_ag)} visitas</h2>
                {filas_html}
            </body></html>"""

            # Mostrar en pantalla
            st.markdown(f"**{len(visitas_ag)} visitas del {ag_desde_s.strftime('%d/%m/%Y')} al {ag_hasta_s.strftime('%d/%m/%Y')}**")
            for v in visitas_ag:
                borde = COLOR_OPO_BD.get(v.get("oportunidad","Ninguna"), "#94a3b8")
                st.markdown(f"""
                <div style='border-left:4px solid {borde};padding:10px 14px;
                            margin-bottom:8px;background:white;border-radius:6px;
                            box-shadow:0 1px 3px rgba(0,0,0,0.06)'>
                    <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                        <strong>{v['fecha']} — {v['cliente_nombre']}</strong>
                        <span style='font-size:0.82em;color:#64748b'>{v['tipo_contacto']} | {v.get('oportunidad','')}</span>
                    </div>
                    {f"<span style='font-size:0.82em;color:#888'>🏷️ {v['temas']}</span>" if v.get('temas') else ''}
                    <p style='margin:6px 0 0;line-height:1.6'>{v.get('comentarios','')}</p>
                    {f"<p style='margin:4px 0 0;font-size:0.85em;color:#64748b'>🔔 {v['seguimiento']}</p>" if v.get('seguimiento') else ''}
                </div>""", unsafe_allow_html=True)

            # Botón descarga HTML (se imprime como PDF desde el navegador)
            st.download_button(
                label="⬇️ Descargar informe (abrir y Ctrl+P para guardar como PDF)",
                data=html_completo.encode("utf-8"),
                file_name=f"agenda_visitas_{ag_desde_s.isoformat()}_{ag_hasta_s.isoformat()}.html",
                mime="text/html"
            )
            st.caption("💡 Tip: abre el archivo descargado en el navegador y pulsa Ctrl+P → 'Guardar como PDF'")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Alertas + Chat IA en columnas ──
    col_al, col_chat = st.columns([1, 2])

    with col_al:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:20px 22px;
                    border:1.5px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,0.04);
                    min-height:300px">
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚠️ Alertas</div>', unsafe_allow_html=True)

        pendientes = db.get_seguimientos_pendientes(comercial_id=comercial_sel["id"])
        if pendientes:
            for p in pendientes[:4]:
                st.markdown(
                    f'<div class="alerta">📞 <b>{p["cliente_nombre"]}</b><br>'
                    f'{p.get("seguimiento","")}<br>'
                    f'<small>Vence: {p.get("fecha_seguimiento","")}</small></div>',
                    unsafe_allow_html=True
                )
        else:
            st.success("Sin seguimientos vencidos")

        sin_visita = db.clientes_sin_visita_reciente(dias=60)
        if sin_visita:
            st.markdown('<div class="section-title" style="margin-top:16px">🕐 Sin visita (60 días)</div>',
                        unsafe_allow_html=True)
            for c in sin_visita[:5]:
                ultima = c.get("ultima_visita") or "Nunca"
                st.markdown(
                    f'<div class="alerta" style="border-color:#94a3b8;background:#f8fafc">'
                    f'👤 <b>{c["nombre"]}</b> ({c.get("zona","-")})<br>'
                    f'<small>Última visita: {ultima}</small></div>',
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chat:
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:20px 22px;
                    border:1.5px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,0.04)">
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-title">🤖 Pregunta a la IA sobre tus visitas</div>',
                    unsafe_allow_html=True)

        api_key_ia = _api_key()
        if not api_key_ia:
            st.info("Configura la API Key de Anthropic en el panel lateral para activar el chat.")
        else:
            # Historial del chat
            chat_html = '<div class="chat-wrapper">'
            for msg in st.session_state.chat_historia:
                if msg["rol"] == "usuario":
                    chat_html += f'<div class="chat-user">{msg["texto"]}</div>'
                else:
                    # Convertir saltos de línea a <br>
                    texto = msg["texto"].replace("\n", "<br>")
                    chat_html += f'<div class="chat-bot">{texto}</div>'
            if not st.session_state.chat_historia:
                chat_html += '<div style="color:#94a3b8;text-align:center;padding:20px">'\
                             'Haz una pregunta sobre tus visitas comerciales...</div>'
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)

            # Input y envío
            col_inp, col_btn = st.columns([4, 1])
            pregunta_chat = col_inp.text_input(
                "Pregunta",
                placeholder="Ej: ¿Qué clientes tienen oportunidad alta este año?",
                label_visibility="collapsed",
                key="chat_input"
            )
            limpiar = col_btn.button("🗑️", help="Limpiar chat")

            if limpiar:
                st.session_state.chat_historia = []
                st.rerun()

            col_send, col_periodo = st.columns([3, 2])
            enviar = col_send.button("Enviar pregunta", type="primary", use_container_width=True)
            periodo_chat = col_periodo.selectbox(
                "Contexto",
                ["Este año", "Este mes", "Últimos 3 meses", "Todo"],
                label_visibility="collapsed"
            )

            if enviar and pregunta_chat.strip():
                # Cargar visitas según periodo seleccionado
                hoy = date.today()
                if periodo_chat == "Este mes":
                    desde = hoy.replace(day=1)
                elif periodo_chat == "Últimos 3 meses":
                    desde = hoy - timedelta(days=90)
                elif periodo_chat == "Este año":
                    desde = hoy.replace(month=1, day=1)
                else:
                    desde = None

                visitas_ctx = db.get_visitas(fecha_desde=desde)

                st.session_state.chat_historia.append({
                    "rol": "usuario",
                    "texto": pregunta_chat
                })

                with st.spinner("Analizando..."):
                    try:
                        respuesta = ia.pregunta_libre(pregunta_chat, visitas_ctx, api_key_ia)
                        st.session_state.chat_historia.append({
                            "rol": "bot",
                            "texto": respuesta
                        })
                    except Exception as e:
                        st.session_state.chat_historia.append({
                            "rol": "bot",
                            "texto": f"Error: {e}"
                        })
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Copia de seguridad ──
    if st.session_state.rol == "control":
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white;border-radius:16px;padding:20px 22px;
                    border:1.5px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,0.04)">
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-title">💾 Copia de seguridad</div>', unsafe_allow_html=True)
        col_bk1, col_bk2 = st.columns(2)
        with col_bk1:
            if st.button("⬇️ Descargar visitas (Excel)", use_container_width=True):
                df_bk = db.exportar_visitas_csv()
                if not df_bk.empty:
                    import io
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        df_bk.to_excel(w, index=False, sheet_name="Visitas")
                    st.download_button(
                        "⬇️ Guardar archivo",
                        data=buf.getvalue(),
                        file_name=f"visitas_sun_{date.today().isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_visitas_dash"
                    )
                else:
                    st.info("No hay visitas aún.")
        with col_bk2:
            if st.button("⬇️ Descargar clientes (Excel)", use_container_width=True):
                df_cl_bk = db.exportar_clientes_csv()
                if not df_cl_bk.empty:
                    import io
                    buf2 = io.BytesIO()
                    with pd.ExcelWriter(buf2, engine="openpyxl") as w:
                        df_cl_bk.to_excel(w, index=False, sheet_name="Clientes")
                    st.download_button(
                        "⬇️ Guardar archivo",
                        data=buf2.getvalue(),
                        file_name=f"clientes_sun_{date.today().isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_clientes_dash"
                    )
                else:
                    st.info("No hay clientes aún.")
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# PÁGINA: NUEVA VISITA
# ══════════════════════════════════════════════
elif pagina == "➕ Nueva Visita":
    st.markdown("""
    <h1 style="margin-bottom:0.1rem">➕ Registrar Nueva Visita</h1>
    <p style="color:#64748b;font-size:0.9em;margin-bottom:1.4rem">
        Selecciona o crea el cliente y rellena los datos de la visita
    </p>
    """, unsafe_allow_html=True)

    st.subheader("1. Cliente")
    modo = st.radio("", ["Buscar cliente existente", "Crear cliente nuevo"], horizontal=True)

    # Resetear cliente si cambia el modo
    if modo == "Buscar cliente existente":
        busq = st.text_input("Buscar por nombre o teléfono")
        clientes = db.get_clientes(busqueda=busq if busq else None)
        if clientes:
            opciones = {f"{c['nombre']} · {c.get('zona','-')} · {c.get('telefono','-')}": c["id"]
                        for c in clientes}
            sel = st.selectbox("Selecciona cliente", list(opciones.keys()))
            st.session_state.cliente_id_nueva_visita = opciones[sel]
        else:
            st.info("No se encontraron clientes. Crea uno nuevo.")
    else:
        with st.form("form_cliente_rapido"):
            r1, r2, r3 = st.columns(3)
            r_nombre = r1.text_input("Nombre *")
            r_tel    = r2.text_input("Teléfono")
            r_zona   = r3.text_input("Zona")
            if st.form_submit_button("Crear y continuar", type="primary"):
                if r_nombre.strip():
                    nuevo_id = db.add_cliente(r_nombre, r_tel, r_zona)
                    st.session_state.cliente_id_nueva_visita = nuevo_id
                    st.success(f"✅ Cliente '{r_nombre}' creado. Ahora rellena los datos de la visita.")
                else:
                    st.error("El nombre es obligatorio.")

    cliente_id = st.session_state.cliente_id_nueva_visita
    if cliente_id:
        cl = db.get_cliente(cliente_id)
        if cl:
            st.info(f"Cliente seleccionado: **{cl['nombre']}** · {cl.get('zona','-')} · {cl.get('telefono','-')}")

    st.markdown("---")
    st.subheader("2. Datos de la visita")

    # Fecha y hora automática — se registra al abrir el formulario
    from datetime import datetime as _dt
    ahora = _dt.now()
    st.info(f"🕐 Fecha y hora de la visita: **{ahora.strftime('%d/%m/%Y %H:%M')}**  _(se guarda automáticamente)_")
    fecha_v = ahora.date()

    with st.form("form_visita", clear_on_submit=True):
        v1, v2 = st.columns(2)
        tipo_v        = v1.selectbox("Tipo de contacto", TIPO_CONTACTO_OPS)
        oportunidad_v = v2.selectbox("Oportunidad", OPORTUNIDAD_OPS)

        temas_v       = st.text_input("Temas tratados",
                                       placeholder="Ej: Antifouling, Sadira, motor 300HP, oferta invierno...")
        comentarios_v = st.text_area("Comentarios *", height=160,
                                      placeholder="Describe qué se habló, estado del cliente, necesidades, actitud...")

        st.markdown("**Seguimiento**")
        s1, s2, s3 = st.columns(3)
        seguimiento_v  = s1.text_input("Acción pendiente", placeholder="Ej: Enviar oferta de motor")
        fecha_seg_v    = s2.date_input("Fecha de seguimiento", value=date.today() + timedelta(days=7))
        importe_v      = s3.number_input("Importe estimado (€)", min_value=0.0, step=100.0)

        ok = st.form_submit_button("💾 Guardar visita", type="primary", use_container_width=True)

        if ok:
            if not cliente_id:
                st.error("Primero selecciona o crea un cliente.")
            elif not comentarios_v.strip():
                st.error("Los comentarios son obligatorios.")
            else:
                db.add_visita(
                    cliente_id=cliente_id,
                    comercial_id=comercial_sel["id"],
                    fecha=ahora.strftime("%Y-%m-%d %H:%M"),
                    tipo_contacto=tipo_v,
                    comentarios=comentarios_v,
                    temas=temas_v,
                    seguimiento=seguimiento_v,
                    fecha_seguimiento=fecha_seg_v if seguimiento_v else None,
                    oportunidad=oportunidad_v,
                    importe_estimado=importe_v
                )
                st.session_state.cliente_id_nueva_visita = None
                st.success("✅ Visita guardada correctamente.")
                st.balloons()


# ══════════════════════════════════════════════
# PÁGINA: VISITAS
# ══════════════════════════════════════════════
elif pagina == "📋 Visitas":
    st.markdown("""
    <h1 style="margin-bottom:0.1rem">📋 Historial de Visitas</h1>
    <p style="color:#64748b;font-size:0.9em;margin-bottom:1.2rem">
        Consulta, filtra y edita el registro de visitas comerciales
    </p>
    """, unsafe_allow_html=True)

    with st.expander("Filtros", expanded=True):
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        f_desde = fc1.date_input("Desde", value=date(date.today().year, 1, 1))
        f_hasta = fc2.date_input("Hasta", value=date.today())
        f_opo   = fc3.selectbox("Oportunidad", ["Todas"] + OPORTUNIDAD_OPS)
        f_zona  = fc4.selectbox("Zona", ["Todas"] + db.get_zonas())
        f_mias  = fc5.checkbox("Solo mis visitas", value=True)

    visitas = db.get_visitas(
        comercial_id=comercial_sel["id"] if f_mias else None,
        fecha_desde=f_desde,
        fecha_hasta=f_hasta,
        oportunidad=f_opo if f_opo != "Todas" else None
    )

    f_busq = st.text_input("🔍 Buscar en comentarios o temas")
    if f_zona != "Todas":
        visitas = [v for v in visitas if v.get("zona") == f_zona]
    if f_busq:
        bl = f_busq.lower()
        visitas = [v for v in visitas
                   if bl in (v.get("comentarios") or "").lower()
                   or bl in (v.get("temas") or "").lower()]

    st.caption(f"{len(visitas)} visitas encontradas")

    if visitas:
        COLOR_OPO_BG = {"Alta": "#dcfce7", "Media": "#fef9c3", "Baja": "#dbeafe", "Ninguna": "#f8fafc"}
        COLOR_OPO_BD = {"Alta": "#22c55e", "Media": "#f59e0b", "Baja": "#60a5fa", "Ninguna": "#cbd5e1"}

        for v in visitas:
            opo       = v.get("oportunidad", "Ninguna")
            bg        = COLOR_OPO_BG.get(opo, "#f8fafc")
            borde     = COLOR_OPO_BD.get(opo, "#cbd5e1")
            temas_txt = v.get("temas") or ""
            comentario = v.get("comentarios") or "—"
            seg_txt   = v.get("seguimiento") or ""
            fecha_seg = v.get("fecha_seguimiento") or ""

            temas_parte = f'<span style="color:#888;font-size:0.85em">🏷️ {temas_txt}</span>' if temas_txt else ""
            seg_parte = (
                f'<div style="margin-top:8px;padding:6px 12px;background:#f0f4ff;'
                f'border-radius:6px;border-left:3px solid #1a73e8;font-size:0.88em;color:#1a2b4a">'
                f'🔔 <b>Seguimiento:</b> {seg_txt}'
                f'{f" · <span style=\'color:#64748b\'>{fecha_seg}</span>" if fecha_seg else ""}'
                f'</div>'
            ) if seg_txt else ""

            zona_txt = v.get("zona") or "-"
            tipo_txt = v.get("tipo_contacto") or ""

            st.markdown(
                f'<div style="background:{bg};border-left:5px solid {borde};'
                f'border-radius:10px;padding:16px 22px;margin-bottom:12px;'
                f'box-shadow:0 1px 4px rgba(0,0,0,0.06)">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">'
                f'<div>'
                f'<span style="font-size:1.05em;font-weight:700;color:#1a2b4a">{v["cliente_nombre"]}</span>'
                f'<span style="margin-left:10px;color:#64748b;font-size:0.88em">'
                f'📅 {v["fecha"]} &nbsp;·&nbsp; {tipo_txt} &nbsp;·&nbsp; 📍 {zona_txt}'
                f'</span>'
                f'</div>'
                f'<span style="background:{borde};color:white;padding:2px 10px;'
                f'border-radius:10px;font-size:0.8em;white-space:nowrap">{opo}</span>'
                f'</div>'
                f'{f"<div style=\'margin-bottom:6px\'>{temas_parte}</div>" if temas_parte else ""}'
                f'<div style="font-size:0.97em;color:#1a2b4a;line-height:1.75;'
                f'padding:10px 14px;background:white;border-radius:8px;border:1px solid #e2e8f0">'
                f'{comentario}</div>'
                f'{seg_parte}'
                f'</div>',
                unsafe_allow_html=True
            )

        # Edición
        with st.expander("Editar / Eliminar visita"):
            labels = [f"#{v['id']} · {v['fecha']} · {v['cliente_nombre']}" for v in visitas]
            sel_ed_label = st.selectbox("Selecciona visita", labels)
            sel_idx = labels.index(sel_ed_label)
            ved = visitas[sel_idx]

            with st.form("form_editar"):
                e1, e2, e3 = st.columns(3)
                ed_tipo   = e1.selectbox("Tipo", TIPO_CONTACTO_OPS,
                                          index=TIPO_CONTACTO_OPS.index(ved["tipo_contacto"])
                                          if ved["tipo_contacto"] in TIPO_CONTACTO_OPS else 0)
                ed_opo    = e2.selectbox("Oportunidad", OPORTUNIDAD_OPS,
                                          index=OPORTUNIDAD_OPS.index(ved["oportunidad"])
                                          if ved["oportunidad"] in OPORTUNIDAD_OPS else 0)
                ed_import = e3.number_input("Importe €", value=float(ved.get("importe_estimado") or 0), step=100.0)
                ed_temas  = st.text_input("Temas", value=ved.get("temas") or "")
                ed_com    = st.text_area("Comentarios", value=ved.get("comentarios") or "", height=100)
                ed_seg    = st.text_input("Seguimiento", value=ved.get("seguimiento") or "")
                ed_fseg   = st.date_input("Fecha seguimiento",
                                           value=date.fromisoformat(ved["fecha_seguimiento"])
                                           if ved.get("fecha_seguimiento") else date.today())

                c_save, c_del = st.columns(2)
                if c_save.form_submit_button("Guardar cambios", type="primary"):
                    db.update_visita(ved["id"], ed_tipo, ed_com, ed_temas,
                                     ed_seg, ed_fseg if ed_seg else None, ed_opo, ed_import)
                    st.success("Visita actualizada")
                    st.rerun()
                if c_del.form_submit_button("Eliminar visita"):
                    db.delete_visita(ved["id"])
                    st.warning("Visita eliminada")
                    st.rerun()
    else:
        st.info("No hay visitas con los filtros seleccionados.")


# ══════════════════════════════════════════════
# PÁGINA: CLIENTES
# ══════════════════════════════════════════════
elif pagina == "👥 Clientes":
    st.markdown("""
    <h1 style="margin-bottom:0.1rem">👥 Clientes</h1>
    <p style="color:#64748b;font-size:0.9em;margin-bottom:1.2rem">
        Gestiona el directorio de clientes y consulta fichas individuales
    </p>
    """, unsafe_allow_html=True)

    tab_lista, tab_ficha, tab_nuevo, tab_editar = st.tabs([
        "Lista de clientes", "📋 Ficha de cliente", "Nuevo cliente", "Editar cliente"
    ])

    with tab_lista:
        c_busq = st.text_input("Buscar")
        c_zona = st.selectbox("Zona", ["Todas"] + db.get_zonas())
        clientes = db.get_clientes(
            zona=c_zona if c_zona != "Todas" else None,
            busqueda=c_busq if c_busq else None
        )
        if clientes:
            df_cl = pd.DataFrame(clientes)[["id", "nombre", "telefono", "zona", "fecha_alta"]]
            df_cl.columns = ["ID", "Nombre", "Teléfono", "Zona", "Alta"]
            st.dataframe(df_cl, use_container_width=True, hide_index=True)
            st.caption(f"{len(clientes)} clientes")
        else:
            st.info("No se encontraron clientes")

    # ── Ficha visual de cliente ──
    with tab_ficha:
        cl_todos_f = db.get_clientes()
        if not cl_todos_f:
            st.info("No hay clientes registrados")
        else:
            sel_ficha = st.selectbox(
                "Selecciona cliente",
                [c["id"] for c in cl_todos_f],
                format_func=lambda i: next(c["nombre"] for c in cl_todos_f if c["id"] == i),
                key="sel_ficha"
            )
            cl_f = db.get_cliente(sel_ficha)
            vis_f = db.get_visitas(cliente_id=sel_ficha)

            if cl_f:
                # Cabecera del cliente
                st.markdown(f"""
                <div style="background:white;border-radius:12px;padding:20px;
                            border-left:5px solid #1a73e8;margin-bottom:16px;
                            box-shadow:0 1px 4px rgba(0,0,0,0.08)">
                    <h2 style="margin:0;color:#1a2b4a">{cl_f['nombre']}</h2>
                    <span style="color:#64748b">📍 {cl_f.get('zona') or '-'} &nbsp;|&nbsp;
                    📞 {cl_f.get('telefono') or '-'} &nbsp;|&nbsp;
                    🗓️ Cliente desde {cl_f.get('fecha_alta','')}</span>
                </div>
                """, unsafe_allow_html=True)

                if cl_f.get("notas"):
                    st.info(f"📝 {cl_f['notas']}")

                # KPIs rápidos
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Total visitas", len(vis_f))
                opos_altas = len([v for v in vis_f if v["oportunidad"] == "Alta"])
                k2.metric("Oportunidades altas", opos_altas)
                importe_total = sum(v.get("importe_estimado") or 0 for v in vis_f)
                k3.metric("Importe pipeline", f"{importe_total:,.0f} €")
                ultima = vis_f[0]["fecha"] if vis_f else "Sin visitas"
                k4.metric("Última visita", ultima)

                st.markdown("---")
                st.markdown("### 📅 Historial de visitas")

                if vis_f:
                    COLOR_OPO_BG = {
                        "Alta": "#dcfce7", "Media": "#fef9c3",
                        "Baja": "#dbeafe", "Ninguna": "#f8fafc"
                    }
                    COLOR_OPO_BD = {
                        "Alta": "#22c55e", "Media": "#f59e0b",
                        "Baja": "#60a5fa", "Ninguna": "#cbd5e1"
                    }
                    for v in vis_f:
                        opo       = v.get("oportunidad", "Ninguna")
                        bg        = COLOR_OPO_BG.get(opo, "#f8fafc")
                        borde     = COLOR_OPO_BD.get(opo, "#cbd5e1")
                        temas_txt = v.get("temas") or ""
                        comentario = v.get("comentarios") or "—"
                        fecha_seg  = v.get("fecha_seguimiento") or ""
                        seg_txt    = v.get("seguimiento") or ""

                        temas_parte = f'<span style="margin-left:12px;color:#888;font-size:0.85em">🏷️ {temas_txt}</span>' if temas_txt else ""
                        fecha_seg_parte = f' · {fecha_seg}' if fecha_seg else ""
                        seg_parte = (
                            f'<div style="margin-top:10px;padding:8px 12px;background:#f0f4ff;'
                            f'border-radius:6px;border-left:3px solid #1a73e8;font-size:0.9em;color:#1a2b4a">'
                            f'🔔 <b>Seguimiento:</b> {seg_txt}'
                            f'<span style="color:#64748b">{fecha_seg_parte}</span></div>'
                        ) if seg_txt else ""

                        html_visita = (
                            f'<div style="background:{bg};border-left:5px solid {borde};'
                            f'border-radius:10px;padding:18px 24px;margin-bottom:14px;'
                            f'box-shadow:0 1px 4px rgba(0,0,0,0.06)">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                            f'<div>'
                            f'<span style="font-size:1.1em;font-weight:700;color:#1a2b4a">📅 {v["fecha"]}</span>'
                            f'<span style="margin-left:12px;color:#64748b;font-size:0.9em">{v["tipo_contacto"]}</span>'
                            f'{temas_parte}'
                            f'</div>'
                            f'<span style="background:{borde};color:white;padding:3px 12px;'
                            f'border-radius:12px;font-size:0.82em">{opo}</span>'
                            f'</div>'
                            f'<div style="font-size:1em;color:#1a2b4a;line-height:1.8;'
                            f'padding:10px 14px;background:white;border-radius:8px;border:1px solid #e2e8f0">'
                            f'{comentario}</div>'
                            f'{seg_parte}'
                            f'</div>'
                        )
                        st.markdown(html_visita, unsafe_allow_html=True)
                else:
                    st.info("Este cliente aún no tiene visitas registradas.")

    with tab_nuevo:
        with st.form("nuevo_cl"):
            n1, n2, n3 = st.columns(3)
            n_nom  = n1.text_input("Nombre *")
            n_tel  = n2.text_input("Teléfono")
            n_zona = n3.text_input("Zona")
            n_nota = st.text_area("Notas")
            if st.form_submit_button("Crear cliente", type="primary"):
                if n_nom.strip():
                    nid = db.add_cliente(n_nom, n_tel, n_zona, n_nota)
                    st.success(f"Cliente '{n_nom}' creado (ID: {nid})")
                else:
                    st.error("El nombre es obligatorio")

    with tab_editar:
        cl_todos = db.get_clientes()
        if cl_todos:
            sel_eid = st.selectbox("Selecciona cliente",
                                    [c["id"] for c in cl_todos],
                                    format_func=lambda i: next(c["nombre"] for c in cl_todos if c["id"] == i))
            cl_ed = db.get_cliente(sel_eid)
            if cl_ed:
                with st.form("editar_cl"):
                    e1, e2, e3 = st.columns(3)
                    e_nom  = e1.text_input("Nombre", value=cl_ed["nombre"])
                    e_tel  = e2.text_input("Teléfono", value=cl_ed.get("telefono") or "")
                    e_zona = e3.text_input("Zona", value=cl_ed.get("zona") or "")
                    e_nota = st.text_area("Notas", value=cl_ed.get("notas") or "")
                    if st.form_submit_button("Guardar cambios", type="primary"):
                        db.update_cliente(sel_eid, e_nom, e_tel, e_zona, e_nota)
                        st.success("Cliente actualizado")
                        st.rerun()
        else:
            st.info("No hay clientes")


# ══════════════════════════════════════════════
# PÁGINA: TAREAS
# ══════════════════════════════════════════════
elif pagina == "✅ Tareas":
    st.markdown("""
    <h1 style="margin-bottom:0.1rem">✅ Tareas y Seguimientos</h1>
    <p style="color:#64748b;font-size:0.9em;margin-bottom:1.2rem">
        Pendientes, vencimientos y acciones de seguimiento
    </p>
    """, unsafe_allow_html=True)

    es_control = st.session_state.rol == "control"

    # En control ve todos; el comercial solo las suyas
    com_id_filtro = None if es_control else comercial_sel["id"]

    tab_pend, tab_hist = st.tabs(["📌 Pendientes", "✔️ Historial completadas"])

    # ── PENDIENTES ──
    with tab_pend:
        pendientes = db.get_tareas_pendientes(comercial_id=com_id_filtro)

        if not pendientes:
            st.success("🎉 No hay tareas pendientes.")
        else:
            st.caption(f"{len(pendientes)} tareas pendientes")

            for t in pendientes:
                fecha_seg = t.get("fecha_seguimiento") or "Sin fecha"
                # Alerta si vence hoy o ya pasó
                from datetime import date as _date
                vencida = False
                if t.get("fecha_seguimiento"):
                    try:
                        vencida = t["fecha_seguimiento"] <= _date.today().isoformat()
                    except Exception:
                        pass

                color_borde = "#ef4444" if vencida else "#f59e0b"
                color_bg    = "#fef2f2" if vencida else "#fffbeb"
                icono       = "🔴" if vencida else "🟡"

                with st.container():
                    comercial_parte = f" &nbsp;·&nbsp; 👤 {t['comercial_nombre']}" if es_control else ""
                    comentario_prev = (t.get("comentarios") or "")[:80]
                    puntos = "..." if len(t.get("comentarios") or "") > 80 else ""
                    st.markdown(
                        f'<div style="background:{color_bg};border-left:5px solid {color_borde};'
                        f'border-radius:10px;padding:14px 20px;margin-bottom:6px">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<div>'
                        f'<span style="font-size:1.05em;font-weight:700;color:#1a2b4a">'
                        f'{icono} {t["cliente_nombre"]}</span>'
                        f'<span style="margin-left:10px;color:#64748b;font-size:0.88em">'
                        f'📅 Vence: {fecha_seg}{comercial_parte}'
                        f'</span>'
                        f'</div>'
                        f'</div>'
                        f'<div style="margin-top:6px;font-size:0.95em;color:#1a2b4a">'
                        f'<b>Tarea:</b> {t["seguimiento"]}'
                        f'</div>'
                        f'<div style="margin-top:4px;font-size:0.85em;color:#64748b">'
                        f'Visita del {t["fecha"]} · {comentario_prev}{puntos}'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    # Formulario inline para completar
                    with st.expander(f"✔️ Marcar como completada — {t['cliente_nombre']}"):
                        with st.form(f"form_completar_{t['id']}"):
                            resultado = st.text_area(
                                "¿Qué se hizo? ¿Cuál fue el resultado?",
                                placeholder="Ej: Se envió presupuesto de antifouling. Cliente lo aceptó.\n"
                                            "Ej: Llamada realizada. Pendiente de respuesta.\n"
                                            "Ej: Presupuesto rechazado, precio demasiado alto.",
                                height=80
                            )
                            if st.form_submit_button("✅ Completar tarea", type="primary"):
                                db.completar_tarea(t["id"], resultado)
                                st.success("Tarea marcada como completada.")
                                st.rerun()
                    st.markdown("")

    # ── HISTORIAL ──
    with tab_hist:
        completadas = db.get_tareas_completadas(comercial_id=com_id_filtro)

        if not completadas:
            st.info("No hay tareas completadas aún.")
        else:
            st.caption(f"{len(completadas)} tareas completadas")
            for t in completadas:
                resultado = t.get("tarea_resultado") or "Sin detalle"
                cierre    = t.get("tarea_fecha_cierre") or ""

                com_hist = f" &nbsp;·&nbsp; {t['comercial_nombre']}" if es_control else ""
                st.markdown(
                    f'<div style="background:#f0fdf4;border-left:5px solid #22c55e;'
                    f'border-radius:10px;padding:14px 20px;margin-bottom:10px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">'
                    f'<span style="font-weight:700;color:#1a2b4a">✔️ {t["cliente_nombre"]}</span>'
                    f'<span style="font-size:0.82em;color:#64748b">Cerrada: {cierre}{com_hist}</span>'
                    f'</div>'
                    f'<div style="font-size:0.9em;color:#374151"><b>Tarea:</b> {t["seguimiento"]}</div>'
                    f'<div style="margin-top:6px;padding:8px 12px;background:white;border-radius:6px;'
                    f'border:1px solid #bbf7d0;font-size:0.9em;color:#166534">'
                    f'📝 {resultado}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # Botón para reabrir si fue un error
                if st.button(f"↩️ Reabrir tarea", key=f"reabrir_{t['id']}"):
                    db.reabrir_tarea(t["id"])
                    st.rerun()


# ══════════════════════════════════════════════
# PÁGINA: INFORMES IA
# ══════════════════════════════════════════════
elif pagina == "📈 Informes IA":
    st.markdown("""
    <h1 style="margin-bottom:0.1rem">📈 Informes IA</h1>
    <p style="color:#64748b;font-size:0.9em;margin-bottom:1.2rem">
        Análisis inteligente con Claude · informes de cliente, pipeline y seguimientos
    </p>
    """, unsafe_allow_html=True)

    api_key_ia = _api_key()
    if not api_key_ia:
        st.warning("Configura la API Key de Anthropic en el panel lateral para usar esta sección.")
        st.stop()

    tab_cliente, tab_periodo, tab_pipeline, tab_briefing = st.tabs([
        "📄 Informe de cliente",
        "📅 Informe periódico",
        "💰 Pipeline",
        "🔔 Seguimientos"
    ])

    # ── Informe de cliente ──
    with tab_cliente:
        st.subheader("Informe completo de cliente")
        clientes = db.get_clientes()
        if not clientes:
            st.info("No hay clientes registrados")
        else:
            sel_cl = st.selectbox("Cliente",
                                   [c["id"] for c in clientes],
                                   format_func=lambda i: next(c["nombre"] for c in clientes if c["id"] == i))
            cl_data = db.get_cliente(sel_cl)
            vis_cl  = db.get_visitas(cliente_id=sel_cl)
            st.caption(f"{len(vis_cl)} visitas para este cliente")
            if st.button("Generar informe", type="primary", key="btn_inf_cl"):
                with st.spinner("Analizando con Claude..."):
                    try:
                        resp = ia.informe_cliente(cl_data, vis_cl, api_key_ia)
                        st.markdown(resp)
                    except Exception as e:
                        st.error(str(e))

    # ── Informe periódico ──
    with tab_periodo:
        st.subheader("Informe de actividad del periodo")
        p1, p2 = st.columns(2)
        p_desde = p1.date_input("Desde", value=date.today().replace(day=1))
        p_hasta = p2.date_input("Hasta", value=date.today())
        p_todos = st.checkbox("Incluir todos los comerciales")
        vis_p   = db.get_visitas(
            comercial_id=None if p_todos else comercial_sel["id"],
            fecha_desde=p_desde,
            fecha_hasta=p_hasta
        )
        st.caption(f"{len(vis_p)} visitas en el periodo")
        if st.button("Generar informe periódico", type="primary", key="btn_inf_p"):
            with st.spinner("Procesando..."):
                try:
                    periodo_str = f"{p_desde.strftime('%d/%m/%Y')} — {p_hasta.strftime('%d/%m/%Y')}"
                    resp = ia.informe_periodico(vis_p, periodo_str,
                                                "Todos" if p_todos else comercial_sel_nombre,
                                                api_key_ia)
                    st.markdown(resp)
                except Exception as e:
                    st.error(str(e))

    # ── Pipeline ──
    with tab_pipeline:
        st.subheader("Análisis del pipeline de oportunidades")
        pip_desde = st.date_input("Visitas desde", value=date(date.today().year, 1, 1))
        vis_pip   = db.get_visitas(comercial_id=comercial_sel["id"], fecha_desde=pip_desde)
        n_pip     = len([v for v in vis_pip if v["oportunidad"] in ("Media", "Alta")])
        st.caption(f"{n_pip} oportunidades Media/Alta")
        if st.button("Analizar pipeline", type="primary", key="btn_pip"):
            with st.spinner("Analizando..."):
                try:
                    resp = ia.analisis_oportunidades(vis_pip, api_key_ia)
                    st.markdown(resp)
                except Exception as e:
                    st.error(str(e))

    # ── Seguimientos ──
    with tab_briefing:
        st.subheader("Briefing de seguimientos pendientes")
        pend = db.get_seguimientos_pendientes(comercial_id=comercial_sel["id"])
        st.caption(f"{len(pend)} seguimientos vencidos")
        if pend:
            df_pend = pd.DataFrame(pend)[["cliente_nombre", "fecha", "seguimiento", "fecha_seguimiento"]]
            df_pend.columns = ["Cliente", "Visita", "Acción", "Fecha límite"]
            st.dataframe(df_pend, use_container_width=True, hide_index=True)
        if st.button("Generar briefing", type="primary", key="btn_brief"):
            with st.spinner("Generando..."):
                try:
                    resp = ia.resumen_seguimientos(pend, api_key_ia)
                    st.markdown(resp)
                except Exception as e:
                    st.error(str(e))


# ══════════════════════════════════════════════
# PÁGINA: CONFIGURACIÓN
# ══════════════════════════════════════════════
elif pagina == "⚙️ Configuración":
    st.markdown("""
    <h1 style="margin-bottom:0.1rem">⚙️ Configuración</h1>
    <p style="color:#64748b;font-size:0.9em;margin-bottom:1.2rem">
        Temas de visita, copias de seguridad y ajustes del sistema
    </p>
    """, unsafe_allow_html=True)

    tab_temas, tab_backup = st.tabs(["🏷️ Temas de visita", "💾 Copia de seguridad"])

    # ── Temas configurables ──
    with tab_temas:
        st.subheader("Temas tratados en las visitas")
        st.caption("Añade, elimina o personaliza los temas que aparecen al registrar una visita: marcas, segmentos, productos, etc.")

        temas_actuales = db.get_temas()

        # Mostrar temas actuales con botón de eliminar
        st.markdown("**Temas actuales:**")
        for tema in temas_actuales:
            col_t, col_del = st.columns([5, 1])
            col_t.markdown(f"🏷️ {tema}")
            if col_del.button("🗑️", key=f"del_tema_{tema}", help=f"Eliminar '{tema}'"):
                db.delete_tema(tema)
                st.rerun()

        st.markdown("---")
        st.markdown("**Añadir nuevo tema:**")
        with st.form("form_nuevo_tema"):
            nuevo_tema = st.text_input("Nombre del tema", placeholder="Ej: Marca Volvo, Segmento Recreo, Winterización...")
            if st.form_submit_button("➕ Añadir tema", type="primary"):
                if nuevo_tema.strip():
                    try:
                        db.add_tema(nuevo_tema)
                        st.success(f"Tema '{nuevo_tema}' añadido")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e} (puede que ya exista)")
                else:
                    st.warning("Escribe un nombre para el tema")

    # ── Copia de seguridad ──
    with tab_backup:
        st.subheader("Copia de seguridad de datos")
        st.info(
            "Los datos están guardados en Supabase (nube). Puedes descargar una copia "
            "en Excel en cualquier momento desde aquí."
        )

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("**Exportar visitas**")
            if st.button("📥 Descargar visitas (Excel)", use_container_width=True):
                df_exp = db.exportar_visitas_csv()
                if not df_exp.empty:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df_exp.to_excel(writer, index=False, sheet_name="Visitas")
                    st.download_button(
                        label="⬇️ Haz clic aquí para guardar el archivo",
                        data=buffer.getvalue(),
                        file_name=f"visitas_sun_{date.today().isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No hay visitas para exportar")

        with col_b2:
            st.markdown("**Exportar clientes**")
            if st.button("📥 Descargar clientes (Excel)", use_container_width=True):
                df_cl_exp = db.exportar_clientes_csv()
                if not df_cl_exp.empty:
                    import io
                    buffer2 = io.BytesIO()
                    with pd.ExcelWriter(buffer2, engine="openpyxl") as writer:
                        df_cl_exp.to_excel(writer, index=False, sheet_name="Clientes")
                    st.download_button(
                        label="⬇️ Haz clic aquí para guardar el archivo",
                        data=buffer2.getvalue(),
                        file_name=f"clientes_sun_{date.today().isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No hay clientes para exportar")
