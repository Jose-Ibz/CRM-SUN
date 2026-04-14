# Guía de despliegue — CRM Visitas Viamar
**Stack:** Supabase (PostgreSQL) + Streamlit Community Cloud

---

## PASO 1 — Crear base de datos en Supabase (gratis)

1. Ve a **https://supabase.com** → Regístrate con Google o email
2. Crea un nuevo proyecto:
   - Name: `crm-viamar`
   - Database Password: elige una contraseña fuerte y **guárdala**
   - Region: `West EU (Ireland)` (la más cercana)
3. Espera ~2 minutos a que se cree el proyecto
4. Ve a **Settings → Database → Connection string → URI**
5. Copia la URI, tiene este formato:
   ```
   postgresql://postgres:[PASSWORD]@db.XXXXXXXX.supabase.co:5432/postgres
   ```
   Reemplaza `[PASSWORD]` con la contraseña que elegiste.
6. Guarda esta URL — la necesitarás en los pasos siguientes

---

## PASO 2 — Subir el código a GitHub

1. Ve a **https://github.com** → Crea una cuenta si no tienes
2. Crea un repositorio nuevo:
   - Name: `crm-viamar`
   - Visibility: **Private** (importante, contiene código de negocio)
3. En tu PC, abre una terminal en la carpeta `CRM\` y ejecuta:
   ```bash
   git init
   git add .
   git commit -m "CRM Visitas Viamar - versión inicial"
   git remote add origin https://github.com/TU_USUARIO/crm-viamar.git
   git push -u origin main
   ```
   > El `.gitignore` ya excluye `secrets.toml`, no se subirá tu contraseña

---

## PASO 3 — Desplegar en Streamlit Community Cloud (gratis)

1. Ve a **https://share.streamlit.io** → Inicia sesión con GitHub
2. Haz clic en **"New app"**
3. Rellena:
   - Repository: `TU_USUARIO/crm-viamar`
   - Branch: `main`
   - Main file path: `crm.py`
4. Haz clic en **"Advanced settings"** → **Secrets**
5. Pega esto (con tus datos reales):
   ```toml
   DATABASE_URL = "postgresql://postgres:TU_PASSWORD@db.XXXXXXXX.supabase.co:5432/postgres"
   ANTHROPIC_API_KEY = "sk-ant-XXXXXXXXXXXXXXXXXX"
   ```
6. Haz clic en **"Deploy!"**
7. En ~2 minutos tendrás una URL pública del tipo:
   ```
   https://crm-viamar-XXXXX.streamlit.app
   ```

---

## PASO 4 — Verificar que funciona

1. Abre la URL pública
2. En la primera carga se crearán las tablas automáticamente
3. Prueba a:
   - Crear un cliente
   - Registrar una visita
   - Ver el dashboard
   - Hacer una pregunta al chat IA

---

## Actualizar la app cuando cambies código

```bash
git add .
git commit -m "descripción del cambio"
git push
```
Streamlit Cloud detecta el push y redespliega automáticamente en ~1 minuto.

---

## Acceso desde móvil o tablet

La URL de Streamlit Cloud funciona en cualquier dispositivo con navegador.
No necesitas instalar nada. El comercial puede usar su móvil para registrar visitas.

---

## Costes

| Servicio | Plan gratuito |
|---|---|
| Supabase | 500 MB base de datos, ilimitado para este uso |
| Streamlit Cloud | 1 app privada gratis, sin límite de usuarios |
| Anthropic API | Pago por uso (~0.003€ por informe) |

**Total infraestructura: 0€/mes**

---

## Seguridad

- El repositorio GitHub es **privado**
- Las credenciales están en **Secrets** de Streamlit Cloud, no en el código
- Supabase cifra los datos en reposo
- La conexión es HTTPS
