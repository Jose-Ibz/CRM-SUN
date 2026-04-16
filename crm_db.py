"""
crm_db.py — Capa de acceso a datos para el CRM de Visitas Comerciales
Base de datos: PostgreSQL en Supabase (cloud)
"""

import os
import psycopg2
import psycopg2.extras
from datetime import date, datetime
import streamlit as st


def get_conn():
    """Retorna una conexión a PostgreSQL usando secrets de Streamlit o variable de entorno."""
    try:
        # Streamlit Cloud: secrets configurados en el dashboard
        db_url = st.secrets["DATABASE_URL"]
    except Exception:
        # Fallback: variable de entorno local
        db_url = os.environ.get("DATABASE_URL", "")

    if not db_url:
        raise RuntimeError(
            "No se ha configurado DATABASE_URL. "
            "Configúrala en .streamlit/secrets.toml o en los Secrets de Streamlit Cloud."
        )

    conn = psycopg2.connect(db_url)
    return conn


def _execute(sql, params=None, fetch=None):
    """Ejecuta una query y devuelve resultados como lista de dicts."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params or ())
                if fetch == "all":
                    return [dict(r) for r in cur.fetchall()]
                if fetch == "one":
                    row = cur.fetchone()
                    return dict(row) if row else None
                if fetch == "scalar":
                    row = cur.fetchone()
                    return row[0] if row else None
                if fetch == "lastrowid":
                    row = cur.fetchone()
                    return list(row.values())[0] if row else None
    finally:
        conn.close()


def inicializar_db():
    """Crea las tablas si no existen."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS comerciales (
                        id      SERIAL PRIMARY KEY,
                        nombre  TEXT NOT NULL UNIQUE,
                        activo  INTEGER NOT NULL DEFAULT 1
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clientes (
                        id          SERIAL PRIMARY KEY,
                        nombre      TEXT NOT NULL,
                        telefono    TEXT,
                        zona        TEXT,
                        notas       TEXT,
                        fecha_alta  TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS visitas (
                        id                  SERIAL PRIMARY KEY,
                        cliente_id          INTEGER NOT NULL REFERENCES clientes(id),
                        comercial_id        INTEGER NOT NULL REFERENCES comerciales(id),
                        fecha               TEXT NOT NULL,
                        tipo_contacto       TEXT NOT NULL DEFAULT 'Presencial',
                        comentarios         TEXT,
                        temas               TEXT,
                        seguimiento         TEXT,
                        fecha_seguimiento   TEXT,
                        oportunidad         TEXT DEFAULT 'Ninguna',
                        importe_estimado    REAL DEFAULT 0,
                        fecha_registro      TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS temas_config (
                        id     SERIAL PRIMARY KEY,
                        nombre TEXT NOT NULL UNIQUE,
                        orden  INTEGER NOT NULL DEFAULT 0
                    )
                """)
                # Migración: añadir columnas de tareas si no existen
                cur.execute("""
                    ALTER TABLE visitas
                    ADD COLUMN IF NOT EXISTS tarea_estado TEXT DEFAULT 'pendiente'
                """)
                cur.execute("""
                    ALTER TABLE visitas
                    ADD COLUMN IF NOT EXISTS tarea_resultado TEXT
                """)
                cur.execute("""
                    ALTER TABLE visitas
                    ADD COLUMN IF NOT EXISTS tarea_fecha_cierre TEXT
                """)
                # Comercial por defecto
                cur.execute("SELECT COUNT(*) FROM comerciales")
                if cur.fetchone()[0] == 0:
                    cur.execute("INSERT INTO comerciales (nombre) VALUES ('Comercial Principal')")
                # Temas por defecto
                cur.execute("SELECT COUNT(*) FROM temas_config")
                if cur.fetchone()[0] == 0:
                    temas_default = [
                        "Precios", "Stock / disponibilidad", "Garantía", "Soporte técnico",
                        "Nuevo producto", "Oferta específica", "Reclamación",
                        "Pago / facturación", "Formación", "Otro"
                    ]
                    for i, t in enumerate(temas_default):
                        cur.execute("INSERT INTO temas_config (nombre, orden) VALUES (%s, %s)", (t, i))
    finally:
        conn.close()


# ─────────────────────────────────────────────
# COMERCIALES
# ─────────────────────────────────────────────

def get_comerciales(solo_activos=True):
    if solo_activos:
        return _execute("SELECT * FROM comerciales WHERE activo=1 ORDER BY nombre", fetch="all")
    return _execute("SELECT * FROM comerciales ORDER BY nombre", fetch="all")


def add_comercial(nombre):
    _execute("INSERT INTO comerciales (nombre) VALUES (%s)", (nombre.strip(),))


# ─────────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────────

def get_clientes(zona=None, busqueda=None):
    sql = "SELECT * FROM clientes WHERE 1=1"
    params = []
    if zona:
        sql += " AND zona = %s"
        params.append(zona)
    if busqueda:
        sql += " AND (nombre ILIKE %s OR telefono ILIKE %s)"
        params += [f"%{busqueda}%", f"%{busqueda}%"]
    sql += " ORDER BY nombre"
    return _execute(sql, params, fetch="all")


def get_cliente(cliente_id):
    return _execute("SELECT * FROM clientes WHERE id=%s", (cliente_id,), fetch="one")


def add_cliente(nombre, telefono="", zona="", notas=""):
    return _execute(
        "INSERT INTO clientes (nombre, telefono, zona, notas, fecha_alta) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (nombre.strip(), telefono.strip(), zona.strip(), notas.strip(), date.today().isoformat()),
        fetch="lastrowid"
    )


def update_cliente(cliente_id, nombre, telefono, zona, notas):
    _execute(
        "UPDATE clientes SET nombre=%s, telefono=%s, zona=%s, notas=%s WHERE id=%s",
        (nombre.strip(), telefono.strip(), zona.strip(), notas.strip(), cliente_id)
    )


def get_zonas():
    rows = _execute("SELECT DISTINCT zona FROM clientes WHERE zona != '' AND zona IS NOT NULL ORDER BY zona", fetch="all")
    return [r["zona"] for r in rows]


# ─────────────────────────────────────────────
# VISITAS
# ─────────────────────────────────────────────

def _fmt_date(d):
    return d.isoformat() if d and hasattr(d, "isoformat") else d


def add_visita(cliente_id, comercial_id, fecha, tipo_contacto, comentarios,
               temas, seguimiento, fecha_seguimiento, oportunidad, importe_estimado):
    _execute("""
        INSERT INTO visitas
            (cliente_id, comercial_id, fecha, tipo_contacto, comentarios,
             temas, seguimiento, fecha_seguimiento, oportunidad, importe_estimado, fecha_registro)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        cliente_id, comercial_id, _fmt_date(fecha), tipo_contacto, comentarios,
        temas, seguimiento, _fmt_date(fecha_seguimiento),
        oportunidad, importe_estimado or 0, datetime.now().isoformat()
    ))


def get_visitas(comercial_id=None, cliente_id=None, fecha_desde=None, fecha_hasta=None,
                oportunidad=None, limite=500):
    sql = """
        SELECT v.*, c.nombre AS cliente_nombre, c.zona, co.nombre AS comercial_nombre
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        WHERE 1=1
    """
    params = []
    if comercial_id:
        sql += " AND v.comercial_id = %s"
        params.append(comercial_id)
    if cliente_id:
        sql += " AND v.cliente_id = %s"
        params.append(cliente_id)
    if fecha_desde:
        sql += " AND v.fecha >= %s"
        params.append(_fmt_date(fecha_desde))
    if fecha_hasta:
        sql += " AND v.fecha <= %s"
        params.append(_fmt_date(fecha_hasta))
    if oportunidad:
        sql += " AND v.oportunidad = %s"
        params.append(oportunidad)
    sql += " ORDER BY v.fecha DESC LIMIT %s"
    params.append(limite)
    return _execute(sql, params, fetch="all")


def get_visita(visita_id):
    return _execute("""
        SELECT v.*, c.nombre AS cliente_nombre, c.zona, co.nombre AS comercial_nombre
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        WHERE v.id = %s
    """, (visita_id,), fetch="one")


def update_visita(visita_id, tipo_contacto, comentarios, temas, seguimiento,
                  fecha_seguimiento, oportunidad, importe_estimado):
    _execute("""
        UPDATE visitas SET tipo_contacto=%s, comentarios=%s, temas=%s, seguimiento=%s,
            fecha_seguimiento=%s, oportunidad=%s, importe_estimado=%s
        WHERE id=%s
    """, (tipo_contacto, comentarios, temas, seguimiento,
          _fmt_date(fecha_seguimiento), oportunidad, importe_estimado or 0, visita_id))


def delete_visita(visita_id):
    _execute("DELETE FROM visitas WHERE id=%s", (visita_id,))


# ─────────────────────────────────────────────
# ESTADÍSTICAS
# ─────────────────────────────────────────────

def stats_visitas_por_mes(comercial_id=None, anyo=None):
    sql = """
        SELECT TO_CHAR(fecha::date, 'YYYY-MM') AS mes, COUNT(*) AS total
        FROM visitas WHERE 1=1
    """
    params = []
    if comercial_id:
        sql += " AND comercial_id=%s"
        params.append(comercial_id)
    if anyo:
        sql += " AND fecha LIKE %s"
        params.append(f"{anyo}%")
    sql += " GROUP BY mes ORDER BY mes"
    return _execute(sql, params, fetch="all")


def stats_visitas_por_tipo(comercial_id=None):
    sql = "SELECT tipo_contacto, COUNT(*) AS total FROM visitas WHERE 1=1"
    params = []
    if comercial_id:
        sql += " AND comercial_id=%s"
        params.append(comercial_id)
    sql += " GROUP BY tipo_contacto"
    return _execute(sql, params, fetch="all")


def stats_oportunidades(comercial_id=None):
    sql = """
        SELECT oportunidad, COUNT(*) AS total, COALESCE(SUM(importe_estimado),0) AS importe
        FROM visitas WHERE 1=1
    """
    params = []
    if comercial_id:
        sql += " AND comercial_id=%s"
        params.append(comercial_id)
    sql += " GROUP BY oportunidad"
    return _execute(sql, params, fetch="all")


def get_seguimientos_pendientes(comercial_id=None):
    sql = """
        SELECT v.*, c.nombre AS cliente_nombre, co.nombre AS comercial_nombre
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        WHERE v.fecha_seguimiento IS NOT NULL
          AND v.fecha_seguimiento <= %s
          AND v.seguimiento IS NOT NULL
          AND v.seguimiento != ''
    """
    params = [date.today().isoformat()]
    if comercial_id:
        sql += " AND v.comercial_id=%s"
        params.append(comercial_id)
    sql += " ORDER BY v.fecha_seguimiento"
    return _execute(sql, params, fetch="all")


def clientes_sin_visita_reciente(dias=60):
    return _execute("""
        SELECT c.*, MAX(v.fecha) AS ultima_visita
        FROM clientes c
        LEFT JOIN visitas v ON v.cliente_id = c.id
        GROUP BY c.id, c.nombre, c.telefono, c.zona, c.notas, c.fecha_alta
        HAVING MAX(v.fecha) IS NULL OR MAX(v.fecha) < (CURRENT_DATE - INTERVAL '%s days')::text
        ORDER BY ultima_visita ASC NULLS FIRST
    """ % dias, fetch="all")


def stats_resumen_global():
    """KPIs globales para el dashboard."""
    hoy = date.today().isoformat()
    mes_inicio = date.today().replace(day=1).isoformat()
    anyo_inicio = date.today().replace(month=1, day=1).isoformat()

    total = _execute("SELECT COUNT(*) AS n FROM visitas", fetch="one")["n"]
    mes = _execute("SELECT COUNT(*) AS n FROM visitas WHERE fecha >= %s", (mes_inicio,), fetch="one")["n"]
    anyo = _execute("SELECT COUNT(*) AS n FROM visitas WHERE fecha >= %s", (anyo_inicio,), fetch="one")["n"]
    clientes_total = _execute("SELECT COUNT(*) AS n FROM clientes", fetch="one")["n"]
    pipeline = _execute(
        "SELECT COALESCE(SUM(importe_estimado),0) AS n FROM visitas WHERE importe_estimado > 0",
        fetch="one"
    )["n"]
    pipeline_alta = _execute(
        "SELECT COALESCE(SUM(importe_estimado),0) AS n FROM visitas WHERE oportunidad IN ('Media','Alta') AND importe_estimado > 0",
        fetch="one"
    )["n"]

    return {
        "total_visitas": total,
        "visitas_mes": mes,
        "visitas_anyo": anyo,
        "total_clientes": clientes_total,
        "pipeline_euros": pipeline,
        "pipeline_alta_euros": pipeline_alta,
    }


# ─────────────────────────────────────────────
# TEMAS CONFIGURABLES
# ─────────────────────────────────────────────

def get_temas():
    rows = _execute("SELECT * FROM temas_config ORDER BY orden, nombre", fetch="all")
    return [r["nombre"] for r in rows]


def add_tema(nombre):
    orden = _execute("SELECT COALESCE(MAX(orden),0)+1 AS n FROM temas_config", fetch="one")["n"]
    _execute("INSERT INTO temas_config (nombre, orden) VALUES (%s, %s)", (nombre.strip(), orden))


def delete_tema(nombre):
    _execute("DELETE FROM temas_config WHERE nombre=%s", (nombre,))


def reordenar_temas(lista_nombres):
    for i, nombre in enumerate(lista_nombres):
        _execute("UPDATE temas_config SET orden=%s WHERE nombre=%s", (i, nombre))


# ─────────────────────────────────────────────
# EXPORTACIÓN / BACKUP
# ─────────────────────────────────────────────

def exportar_visitas_csv():
    """Devuelve todas las visitas como DataFrame para exportar."""
    import pandas as pd
    rows = _execute("""
        SELECT v.id, v.fecha, c.nombre AS cliente, c.zona, c.telefono,
               co.nombre AS comercial, v.tipo_contacto, v.temas,
               v.comentarios, v.seguimiento, v.fecha_seguimiento,
               v.oportunidad, v.importe_estimado, v.fecha_registro
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        ORDER BY v.fecha DESC
    """, fetch="all")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def exportar_clientes_csv():
    import pandas as pd
    rows = _execute("SELECT * FROM clientes ORDER BY nombre", fetch="all")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─────────────────────────────────────────────
# TAREAS / SEGUIMIENTOS
# ─────────────────────────────────────────────

def get_tareas_pendientes(comercial_id=None):
    """Visitas con seguimiento definido y tarea aún pendiente."""
    sql = """
        SELECT v.*, c.nombre AS cliente_nombre, c.zona, c.telefono,
               co.nombre AS comercial_nombre
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        WHERE v.seguimiento IS NOT NULL
          AND v.seguimiento != ''
          AND (v.tarea_estado IS NULL OR v.tarea_estado = 'pendiente')
    """
    params = []
    if comercial_id:
        sql += " AND v.comercial_id = %s"
        params.append(comercial_id)
    sql += " ORDER BY v.fecha_seguimiento ASC NULLS LAST, v.fecha DESC"
    return _execute(sql, params, fetch="all")


def get_tareas_completadas(comercial_id=None, limite=50):
    """Historial de tareas ya completadas."""
    sql = """
        SELECT v.*, c.nombre AS cliente_nombre, c.zona,
               co.nombre AS comercial_nombre
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        WHERE v.tarea_estado = 'completada'
    """
    params = []
    if comercial_id:
        sql += " AND v.comercial_id = %s"
        params.append(comercial_id)
    sql += " ORDER BY v.tarea_fecha_cierre DESC LIMIT %s"
    params.append(limite)
    return _execute(sql, params, fetch="all")


def completar_tarea(visita_id, resultado):
    """Marca una tarea como completada con su resultado."""
    from datetime import datetime
    _execute("""
        UPDATE visitas
        SET tarea_estado = 'completada',
            tarea_resultado = %s,
            tarea_fecha_cierre = %s
        WHERE id = %s
    """, (resultado, datetime.now().strftime("%Y-%m-%d %H:%M"), visita_id))


def reabrir_tarea(visita_id):
    """Reactiva una tarea completada."""
    _execute("""
        UPDATE visitas
        SET tarea_estado = 'pendiente',
            tarea_resultado = NULL,
            tarea_fecha_cierre = NULL
        WHERE id = %s
    """, (visita_id,))
