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
    page_title="CRM Visitas · Viamar",
    page_icon="⚓",
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
    /* Fondo general */
    .main { background-color: #f7f9fc; }

    /* KPI cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* Chat IA */
    .chat-user {
        background: #1a73e8;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 10px 16px;
        margin: 6px 0 6px 20%;
        font-size: 0.95em;
    }
    .chat-bot {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 18px 18px 18px 4px;
        padding: 10px 16px;
        margin: 6px 20% 6px 0;
        font-size: 0.95em;
        line-height: 1.6;
    }
    .chat-wrapper {
        max-height: 420px;
        overflow-y: auto;
        padding: 8px;
        background: #f7f9fc;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    .alerta {
        background: #fff3cd;
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.9em;
    }
    h1 { color: #1a2b4a; }
    .section-title {
        font-size: 1.1em;
        font-weight: 600;
        color: #1a2b4a;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "chat_historia" not in st.session_state:
    st.session_state.chat_historia = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
TIPO_CONTACTO_OPS = ["Presencial", "Telefónico", "Email", "Videollamada", "Feria/Evento"]
OPORTUNIDAD_OPS   = ["Ninguna", "Baja", "Media", "Alta"]
TEMAS_OPS = [
    "Precios", "Stock / disponibilidad", "Garantía", "Soporte técnico",
    "Nuevo producto", "Oferta específica", "Reclamación",
    "Pago / facturación", "Formación", "Otro"
]
COLOR_OPO = {"Ninguna": "#94a3b8", "Baja": "#60a5fa", "Media": "#f59e0b", "Alta": "#22c55e"}

def _api_key():
    """Obtiene la API key: primero secrets de Streamlit, luego session_state."""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return st.session_state.get("api_key", "")


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("LOGO-viamar.jpg", use_container_width=True)
    except Exception:
        st.markdown("## ⚓ Viamar CRM")

    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        ["📊 Dashboard", "➕ Nueva Visita", "📋 Visitas", "👥 Clientes", "📈 Informes IA"],
        label_visibility="collapsed"
    )

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

    comercial_sel_nombre = st.selectbox("Comercial", nombres_com)
    comercial_sel = next(c for c in comerciales if c["nombre"] == comercial_sel_nombre)

    # API Key (solo si no está en secrets)
    try:
        st.secrets["ANTHROPIC_API_KEY"]
        st.success("API IA configurada", icon="🤖")
    except Exception:
        api_key_input = st.text_input("API Key Anthropic", type="password",
                                       value=st.session_state.api_key,
                                       help="Pega aquí tu API Key de Anthropic")
        if api_key_input:
            st.session_state.api_key = api_key_input

    st.markdown("---")
    with st.expander("+ Añadir comercial"):
        nuevo_com = st.text_input("Nombre", key="input_nuevo_com")
        if st.button("Añadir"):
            if nuevo_com.strip():
                try:
                    db.add_comercial(nuevo_com)
                    st.success("Añadido")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ══════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════
if pagina == "📊 Dashboard":
    st.title("📊 Dashboard Comercial")

    # ── KPIs globales ──
    try:
        resumen = db.stats_resumen_global()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

    anyo_actual = date.today().year
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total visitas", resumen["total_visitas"])
    k2.metric("Visitas este mes", resumen["visitas_mes"])
    k3.metric("Visitas este año", resumen["visitas_anyo"])
    k4.metric("Clientes", resumen["total_clientes"])
    k5.metric("Pipeline €", f"{resumen['pipeline_euros']:,.0f} €")

    st.markdown("---")

    # ── Gráficos ──
    col_g1, col_g2, col_g3 = st.columns([2, 1, 1])

    with col_g1:
        st.markdown('<div class="section-title">Visitas por mes</div>', unsafe_allow_html=True)
        anyo_sel = st.selectbox("Año", list(range(anyo_actual, anyo_actual - 4, -1)),
                                 key="anyo_dash", label_visibility="collapsed")
        stats_mes = db.stats_visitas_por_mes(anyo=anyo_sel)
        if stats_mes:
            df_mes = pd.DataFrame(stats_mes)
            # Rellenar meses sin visitas
            todos_meses = [f"{anyo_sel}-{m:02d}" for m in range(1, 13)]
            df_mes = (pd.DataFrame({"mes": todos_meses})
                      .merge(df_mes, on="mes", how="left")
                      .fillna(0))
            df_mes["mes_label"] = df_mes["mes"].str[5:]
            fig = px.bar(df_mes, x="mes_label", y="total",
                         color_discrete_sequence=["#1a73e8"],
                         labels={"mes_label": "", "total": "Visitas"})
            fig.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=240,
                               plot_bgcolor="white", paper_bgcolor="white")
            fig.update_yaxes(gridcolor="#f0f0f0")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos para este año")

    with col_g2:
        st.markdown('<div class="section-title">Tipo de contacto</div>', unsafe_allow_html=True)
        stats_tipo = db.stats_visitas_por_tipo()
        if stats_tipo:
            df_tipo = pd.DataFrame(stats_tipo)
            fig = px.pie(df_tipo, values="total", names="tipo_contacto",
                         color_discrete_sequence=px.colors.qualitative.Set2,
                         hole=0.4)
            fig.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=240,
                               showlegend=True, legend=dict(font=dict(size=11)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")

    with col_g3:
        st.markdown('<div class="section-title">Oportunidades</div>', unsafe_allow_html=True)
        stats_opo = db.stats_oportunidades()
        if stats_opo:
            df_opo = pd.DataFrame(stats_opo)
            fig = px.bar(df_opo, x="oportunidad", y="total",
                         color="oportunidad", color_discrete_map=COLOR_OPO,
                         labels={"oportunidad": "", "total": "Nº visitas"})
            fig.update_layout(margin=dict(t=10, b=10, l=0, r=0), height=240,
                               showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
            fig.update_yaxes(gridcolor="#f0f0f0")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")

    st.markdown("---")

    # ── Alertas + Chat IA en columnas ──
    col_al, col_chat = st.columns([1, 2])

    with col_al:
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
            st.markdown('<div class="section-title" style="margin-top:12px">🕐 Sin visita (60d)</div>',
                        unsafe_allow_html=True)
            for c in sin_visita[:5]:
                ultima = c.get("ultima_visita") or "Nunca"
                st.markdown(
                    f'<div class="alerta" style="border-color:#94a3b8">'
                    f'👤 <b>{c["nombre"]}</b> ({c.get("zona","-")})<br>'
                    f'<small>Última visita: {ultima}</small></div>',
                    unsafe_allow_html=True
                )

    with col_chat:
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


# ══════════════════════════════════════════════
# PÁGINA: NUEVA VISITA
# ══════════════════════════════════════════════
elif pagina == "➕ Nueva Visita":
    st.title("➕ Registrar Nueva Visita")

    st.subheader("1. Cliente")
    modo = st.radio("", ["Buscar cliente existente", "Crear cliente nuevo"], horizontal=True)

    cliente_id = None

    if modo == "Buscar cliente existente":
        busq = st.text_input("Buscar por nombre o teléfono")
        clientes = db.get_clientes(busqueda=busq if busq else None)
        if clientes:
            opciones = {f"{c['nombre']} · {c.get('zona','-')} · {c.get('telefono','-')}": c["id"]
                        for c in clientes}
            sel = st.selectbox("Selecciona cliente", list(opciones.keys()))
            cliente_id = opciones[sel]
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
                    cliente_id = db.add_cliente(r_nombre, r_tel, r_zona)
                    st.success(f"Cliente '{r_nombre}' creado.")
                else:
                    st.error("El nombre es obligatorio.")

    st.markdown("---")
    st.subheader("2. Datos de la visita")

    with st.form("form_visita", clear_on_submit=True):
        v1, v2, v3 = st.columns(3)
        fecha_v      = v1.date_input("Fecha *", value=date.today())
        tipo_v       = v2.selectbox("Tipo de contacto", TIPO_CONTACTO_OPS)
        oportunidad_v = v3.selectbox("Oportunidad", OPORTUNIDAD_OPS)

        temas_v       = st.multiselect("Temas tratados", TEMAS_OPS)
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
                    fecha=fecha_v,
                    tipo_contacto=tipo_v,
                    comentarios=comentarios_v,
                    temas=", ".join(temas_v),
                    seguimiento=seguimiento_v,
                    fecha_seguimiento=fecha_seg_v if seguimiento_v else None,
                    oportunidad=oportunidad_v,
                    importe_estimado=importe_v
                )
                st.success("✅ Visita guardada correctamente.")
                st.balloons()


# ══════════════════════════════════════════════
# PÁGINA: VISITAS
# ══════════════════════════════════════════════
elif pagina == "📋 Visitas":
    st.title("📋 Historial de Visitas")

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
        df = pd.DataFrame(visitas)
        cols = ["fecha", "cliente_nombre", "zona", "tipo_contacto",
                "oportunidad", "temas", "comentarios", "seguimiento",
                "fecha_seguimiento", "importe_estimado"]
        df_show = df[cols].copy()
        df_show.columns = ["Fecha", "Cliente", "Zona", "Tipo", "Oportunidad",
                            "Temas", "Comentarios", "Seguimiento", "Seg. fecha", "Importe €"]

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Comentarios": st.column_config.TextColumn(width="large"),
                "Importe €":   st.column_config.NumberColumn(format="%.0f €"),
            }
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
    st.title("👥 Clientes")

    tab_lista, tab_nuevo, tab_editar = st.tabs(["Lista de clientes", "Nuevo cliente", "Editar cliente"])

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

            sel_hist = st.selectbox("Ver historial de visitas",
                                     [c["id"] for c in clientes],
                                     format_func=lambda i: next(c["nombre"] for c in clientes if c["id"] == i))
            vis_cl = db.get_visitas(cliente_id=sel_hist)
            if vis_cl:
                df_vis = pd.DataFrame(vis_cl)[["fecha", "tipo_contacto", "oportunidad", "comentarios", "seguimiento"]]
                df_vis.columns = ["Fecha", "Tipo", "Oportunidad", "Comentarios", "Seguimiento"]
                st.dataframe(df_vis, use_container_width=True, hide_index=True)
            else:
                st.info("Sin visitas registradas para este cliente")
        else:
            st.info("No se encontraron clientes")

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
# PÁGINA: INFORMES IA
# ══════════════════════════════════════════════
elif pagina == "📈 Informes IA":
    st.title("📈 Informes con Inteligencia Artificial")

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
