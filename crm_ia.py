"""
crm_ia.py — Módulo de informes y análisis con Claude (Anthropic API)
"""

import os
import anthropic

# Usar la API key de entorno o de secrets de Streamlit
def _get_client(api_key: str = None):
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("No se ha configurado la API key de Anthropic.")
    return anthropic.Anthropic(api_key=key)


def _llamar_claude(prompt: str, api_key: str = None, max_tokens: int = 2048) -> str:
    client = _get_client(api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=(
            "Eres un asistente especializado en análisis comercial para una empresa de náutica "
            "(Náutica Viamar, distribuidora de repuestos Volvo Penta). "
            "Tu tarea es analizar notas de visitas comerciales y extraer información útil, "
            "detectar oportunidades, alertas y tendencias. "
            "Responde siempre en español, de forma clara y estructurada."
        ),
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


# ─────────────────────────────────────────────
# INFORMES DISPONIBLES
# ─────────────────────────────────────────────

def informe_cliente(cliente: dict, visitas: list, api_key: str = None) -> str:
    """Resumen completo del historial de un cliente."""
    if not visitas:
        return "No hay visitas registradas para este cliente."

    visitas_texto = "\n\n".join([
        f"- Fecha: {v['fecha']} | Tipo: {v['tipo_contacto']} | Oportunidad: {v['oportunidad']}\n"
        f"  Temas: {v.get('temas', '-')}\n"
        f"  Comentarios: {v.get('comentarios', '-')}\n"
        f"  Seguimiento: {v.get('seguimiento', '-')}"
        for v in visitas
    ])

    prompt = f"""
Analiza el historial comercial del siguiente cliente y genera un informe detallado.

CLIENTE: {cliente['nombre']} | Zona: {cliente.get('zona', '-')} | Tel: {cliente.get('telefono', '-')}
Notas del cliente: {cliente.get('notas', '-')}

HISTORIAL DE VISITAS ({len(visitas)} visitas):
{visitas_texto}

Por favor, genera un informe que incluya:
1. **Resumen ejecutivo** del cliente (2-3 frases)
2. **Temas recurrentes** tratados en las visitas
3. **Oportunidades detectadas** y su estado
4. **Puntos de atención** o alertas (quejas, problemas, compromisos pendientes)
5. **Recomendación para la próxima visita**
"""
    return _llamar_claude(prompt, api_key)


def informe_periodico(visitas: list, periodo: str, comercial: str, api_key: str = None) -> str:
    """Resumen de actividad comercial de un periodo."""
    if not visitas:
        return "No hay visitas registradas en el periodo seleccionado."

    visitas_texto = "\n\n".join([
        f"- {v['fecha']} | Cliente: {v['cliente_nombre']} (Zona: {v.get('zona', '-')}) | "
        f"Tipo: {v['tipo_contacto']} | Oportunidad: {v['oportunidad']}\n"
        f"  Temas: {v.get('temas', '-')}\n"
        f"  Comentarios: {v.get('comentarios', '-')}"
        for v in visitas
    ])

    prompt = f"""
Analiza la actividad comercial del periodo indicado y genera un informe de gestión.

COMERCIAL: {comercial}
PERIODO: {periodo}
TOTAL VISITAS: {len(visitas)}

DETALLE DE VISITAS:
{visitas_texto}

Por favor, genera un informe que incluya:
1. **Resumen de actividad** (visitas realizadas, clientes contactados, zonas cubiertas)
2. **Temas más tratados** en las visitas de este periodo
3. **Oportunidades de venta** identificadas y su valoración
4. **Clientes que requieren atención** urgente o seguimiento
5. **Logros y puntos positivos** del periodo
6. **Áreas de mejora** o aspectos a reforzar
7. **Recomendaciones** para el próximo periodo
"""
    return _llamar_claude(prompt, api_key, max_tokens=3000)


def analisis_oportunidades(visitas: list, api_key: str = None) -> str:
    """Extrae y prioriza las oportunidades de venta del pipeline."""
    oportunidades = [v for v in visitas if v.get("oportunidad") in ("Media", "Alta")]
    if not oportunidades:
        return "No hay oportunidades de nivel Medio o Alto registradas actualmente."

    texto = "\n\n".join([
        f"- Cliente: {v['cliente_nombre']} | Fecha última visita: {v['fecha']}\n"
        f"  Nivel: {v['oportunidad']} | Importe estimado: {v.get('importe_estimado', 0):.0f} €\n"
        f"  Comentarios: {v.get('comentarios', '-')}\n"
        f"  Seguimiento previsto: {v.get('seguimiento', '-')} ({v.get('fecha_seguimiento', '-')})"
        for v in oportunidades
    ])

    prompt = f"""
Analiza el pipeline de oportunidades comerciales y genera un informe de priorización.

OPORTUNIDADES ACTIVAS ({len(oportunidades)}):
{texto}

Por favor:
1. **Clasifica las oportunidades** de mayor a menor prioridad con justificación
2. **Estima el potencial total** del pipeline
3. **Identifica acciones concretas** para cerrar cada oportunidad
4. **Señala riesgos** que puedan hacer perder alguna oportunidad
5. **Recomendación de próximos pasos** por orden de prioridad
"""
    return _llamar_claude(prompt, api_key, max_tokens=2500)


def pregunta_libre(pregunta: str, visitas: list, api_key: str = None) -> str:
    """Responde una pregunta libre sobre las visitas proporcionadas."""
    if not visitas:
        return "No hay visitas sobre las que consultar."

    visitas_texto = "\n\n".join([
        f"- {v['fecha']} | {v['cliente_nombre']} | {v['tipo_contacto']} | {v['oportunidad']}\n"
        f"  {v.get('comentarios', '-')}"
        for v in visitas[:100]  # Limitar para no exceder el contexto
    ])

    prompt = f"""
Contexto: tienes acceso al historial de visitas comerciales de Náutica Viamar.

VISITAS ({len(visitas)} registros):
{visitas_texto}

PREGUNTA DEL USUARIO: {pregunta}

Responde de forma concisa y práctica basándote únicamente en los datos proporcionados.
Si la información no es suficiente para responder, indícalo claramente.
"""
    return _llamar_claude(prompt, api_key, max_tokens=1500)


def resumen_seguimientos(pendientes: list, api_key: str = None) -> str:
    """Genera un briefing de los seguimientos pendientes."""
    if not pendientes:
        return "No hay seguimientos pendientes para hoy."

    texto = "\n".join([
        f"- {v['cliente_nombre']} | Visita: {v['fecha']} | "
        f"Acción pendiente: {v.get('seguimiento', '-')} | Fecha límite: {v.get('fecha_seguimiento', '-')}"
        for v in pendientes
    ])

    prompt = f"""
Genera un briefing ejecutivo de los seguimientos comerciales pendientes para hoy.

SEGUIMIENTOS PENDIENTES ({len(pendientes)}):
{texto}

Organiza el briefing por urgencia y proporciona:
1. Lista priorizada de llamadas/visitas a realizar hoy
2. Para cada cliente, el contexto mínimo necesario antes de contactarle
3. Tiempo estimado para gestionar todos los seguimientos
"""
    return _llamar_claude(prompt, api_key, max_tokens=1500)
