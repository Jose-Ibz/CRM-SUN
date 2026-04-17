"""
enviar_backup.py — Genera Excel con datos del CRM y lo envía por email
Se ejecuta automáticamente cada lunes via GitHub Actions
"""

import os
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
import pandas as pd

# ── Conexión a Supabase ──
DATABASE_URL = os.environ["DATABASE_URL"]
GMAIL_USER   = os.environ["GMAIL_USER"]
GMAIL_PASS   = os.environ["GMAIL_PASSWORD"]
EMAIL_DEST   = os.environ["EMAIL_DESTINO"]

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def exportar_visitas():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT v.id, v.fecha, c.nombre AS cliente, c.zona, c.telefono,
               co.nombre AS comercial, v.tipo_contacto, v.temas,
               v.comentarios, v.seguimiento, v.fecha_seguimiento,
               v.oportunidad, v.importe_estimado,
               v.tarea_estado, v.tarea_resultado, v.tarea_fecha_cierre
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        ORDER BY v.fecha DESC
    """, conn)
    conn.close()
    return df

def exportar_clientes():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM clientes ORDER BY nombre", conn)
    conn.close()
    return df

def exportar_tareas_pendientes():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT c.nombre AS cliente, c.telefono, co.nombre AS comercial,
               v.fecha, v.seguimiento, v.fecha_seguimiento, v.oportunidad,
               v.comentarios
        FROM visitas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN comerciales co ON v.comercial_id = co.id
        WHERE v.seguimiento IS NOT NULL AND v.seguimiento != ''
          AND (v.tarea_estado IS NULL OR v.tarea_estado = 'pendiente')
        ORDER BY v.fecha_seguimiento ASC NULLS LAST
    """, conn)
    conn.close()
    return df

# ── Generar Excel con tres hojas ──
def generar_excel():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        exportar_visitas().to_excel(writer, index=False, sheet_name="Visitas")
        exportar_clientes().to_excel(writer, index=False, sheet_name="Clientes")
        exportar_tareas_pendientes().to_excel(writer, index=False, sheet_name="Tareas pendientes")
    return buf.getvalue()

# ── Enviar email ──
def enviar_email(excel_bytes):
    hoy        = date.today()
    semana_ant = hoy - timedelta(days=7)

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = EMAIL_DEST
    msg["Subject"] = f"📊 Backup CRM Sun Ibiza — semana {semana_ant.strftime('%d/%m')} al {hoy.strftime('%d/%m/%Y')}"

    cuerpo = f"""
Hola Jose,

Adjunto el backup semanal del CRM Sun Ibiza con fecha {hoy.strftime('%d/%m/%Y')}.

El archivo Excel contiene tres hojas:
  • Visitas — historial completo de visitas comerciales
  • Clientes — lista de todos los clientes
  • Tareas pendientes — seguimientos por cerrar

Un saludo,
CRM Sun Ibiza (envío automático)
"""
    msg.attach(MIMEText(cuerpo, "plain"))

    # Adjuntar Excel
    parte = MIMEBase("application", "octet-stream")
    parte.set_payload(excel_bytes)
    encoders.encode_base64(parte)
    parte.add_header(
        "Content-Disposition",
        f"attachment; filename=backup_crm_sun_{hoy.isoformat()}.xlsx"
    )
    msg.attach(parte)

    # Enviar via Gmail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, EMAIL_DEST, msg.as_string())

    print(f"✅ Backup enviado a {EMAIL_DEST}")

if __name__ == "__main__":
    print("Generando Excel...")
    excel = generar_excel()
    print("Enviando email...")
    enviar_email(excel)
