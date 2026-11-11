# Sistema automatizado de gestión de solicitudes de soporte técnico

API REST en **Python (Flask)** + **PostgreSQL en Neon**, ejecutada **localmente**
(por instrucción del docente no se despliega en Render),
con **Google Forms → Google Sheets**, automatización en **n8n** y notificaciones
por **Gmail**. Dashboard en Google Sheets con total, por categoría y por prioridad.

- **Materia:** Programación en ambiente cliente servidor — 2do parcial
- **Docente:** Ing. Alex Ramírez Galindo
- **Alumno:** Alejandro Sánchez Melchor — Matrícula 2021330281
- **Carrera:** Ingeniería Informática
- **Fecha de entrega:** 2026-11-11

## Arquitectura

```text
Google Forms ──► Google Sheets (Respuestas)
                     │  Google Sheets Trigger (nueva fila)
                     ▼
                   n8n ──► POST /api/solicitudes ──► API Flask (local, http://localhost:5000)
                     │                                  │  psycopg2
                     │                                  ▼
                     │                              PostgreSQL (Neon)
                     │                                  tabla solicitudes
                     ▼
                   Gmail (confirmación con folio al solicitante)
                     │
                     └──► Google Sheets: escribe Folio y Estado en la fila

Dashboard: pestaña adicional en la misma hoja, con fórmulas sobre Respuestas.
```

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `app.py` | API Flask: endpoints, validación y manejo de errores JSON. |
| `db.py` | Capa de datos: PostgreSQL (Neon) si existe `DATABASE_URL`, SQLite local como fallback solo para pruebas. |
| `schema.sql` | Esquema PostgreSQL (tabla `solicitudes`, índices, trigger de `fecha_actualizacion`). |
| `seed.sql` | 12 solicitudes semilla para Neon (`psql "$DATABASE_URL" -f seed.sql`). |
| `seed.py` | Misma siembra usando la capa de datos (`python seed.py`, `--reset` para repetir). |
| `requirements.txt` | Flask, psycopg2-binary, Flask-CORS, python-dotenv, gunicorn. |
| `.env.example` | Plantilla de variables de entorno (sin credenciales reales). |
| `render.yaml` | Blueprint de Render; sin uso en esta entrega (no hay despliegue en Render). |
| `Procfile` | `web: gunicorn app:app` (solo comprobación local; sin despliegue). |
| `n8n-workflow.json` | Workflow n8n exportable (importar en n8n). |
| `README_N8N.md` | Configuración paso a paso de n8n, variables y formato del correo. |
| `RESULTADOS_PRUEBAS.md` | Salidas reales de la prueba local. |

## API — Endpoints

Base local: `http://localhost:5000` (única base; no hay URL de Render).

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Salud del servicio. |
| GET | `/api/solicitudes` | Lista todas. Filtros: `?categoria=`, `?prioridad=`, `?estado=`. |
| GET | `/api/solicitudes/<folio>` | Una solicitud por folio (ej. `SOL-2026-0001`). |
| POST | `/api/solicitudes` | Crea una solicitud; genera el folio secuencial. Responde **201**. |
| PUT | `/api/solicitudes/<folio>` | Cambia el estado. Cuerpo: `{"estado": "En proceso"}`. |
| GET | `/api/estadisticas` | `total`, `por_categoria`, `por_prioridad`, `por_estado`. |

### POST /api/solicitudes — cuerpo

```json
{
  "nombre_solicitante": "María Fernanda López García",
  "email": "maria.lopez@ejemplo.com",
  "categoria": "Hardware",
  "prioridad": "Alta",
  "descripcion": "La computadora del laboratorio 3 no enciende.",
  "origen": "api"
}
```

- **Categorías:** `Hardware`, `Software`, `Red e Internet`, `Impresoras`, `Cuentas y accesos`, `Otro`.
- **Prioridades:** `Baja`, `Media`, `Alta`, `Crítica`.
- **Estados:** `Recibida` (inicial), `En revisión`, `En proceso`, `Resuelta`, `Cerrada`.
- **Validación:** nombre y descripción obligatorios, email con formato válido, categoría y prioridad dentro de los catálogos. Si algo falla, la API responde **400** con `{"ok": false, "error": ..., "detalles": [...]}`. Un folio inexistente responde **404**.
- **Folios:** secuenciales `SOL-2026-0001`, `SOL-2026-0002`, … (el siguiente es el mayor existente + 1).

## Instalación y prueba local

```bash
cd codigo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Sin DATABASE_URL la API usa SQLite local (solicitudes.db) para pruebas.
python seed.py          # siembra 12 solicitudes de ejemplo
python app.py           # arranca en http://localhost:5000

curl http://localhost:5000/health
curl http://localhost:5000/api/estadisticas
curl "http://localhost:5000/api/solicitudes?categoria=Hardware"
```

Ver las salidas reales de esta prueba en [`RESULTADOS_PRUEBAS.md`](RESULTADOS_PRUEBAS.md).

## Base en Neon y ejecución local (por instrucción del docente, sin Render)

1. **Neon:** proyecto `solicitudes-soporte-tecnico` ya creado (PostgreSQL 18, base `neondb`); copiar la `DATABASE_URL` desde el panel de Neon.
2. Aplicar el esquema y la siembra:
   ```bash
   psql "$DATABASE_URL" -f schema.sql
   psql "$DATABASE_URL" -f seed.sql
   ```
3. **Ejecución local:** con la `DATABASE_URL` de Neon en `.env` (ver `.env.example`), arrancar la API en local:
   ```bash
   python app.py    # http://localhost:5000
   ```
   No se crea ningún servicio en Render y no se agrega tarjeta; `render.yaml` y `Procfile` quedan en el repo sin uso en esta entrega.
4. Verificar: `GET http://localhost:5000/health` (debe indicar `base_datos: "postgres"`) y `GET http://localhost:5000/api/estadisticas`.
5. **Google Forms + Sheets:** el formulario ya existe: **"Solicitud de soporte técnico"**, ID `1pXdV_doHLG_9azAX_bRc3H0ckMEBp_tF3SKdHceOZnw`, publicado y aceptando respuestas: https://docs.google.com/forms/d/e/1FAIpQLSexH3Tg4eKpLxxOdLH9NV06EsgZyZkBO727Fe0IqsMuBDwBVA/viewform — 5 preguntas obligatorias (Nombre completo, Correo electrónico, Categoría, Prioridad, Descripción del problema) con los valores exactos de los catálogos. La hoja también existe ("Solicitudes de soporte técnico - Respuestas y Dashboard", ID `1JO8IqTb_x9qIuJWmczViM3pEWd9V0-2HhA9cQFOSypk`, pestañas `Respuestas` y `Dashboard`). El formulario **no** está vinculado automáticamente a la hoja; la conexión la hace n8n (trigger de Sheets + HTTP Request a la API, ver `README_N8N.md`).
6. **n8n:** importar `n8n-workflow.json` y seguir [`README_N8N.md`](README_N8N.md).
7. **Dashboard en Sheets:** ya existe la pestaña `Dashboard` en la misma hoja, con fórmulas COUNTA/COUNTIF verificadas (total 0 por ahora, antes de registrar solicitudes). Columnas de `Respuestas`: Fecha (A), Folio (B), Nombre (C), Email (D), Categoría (E), Prioridad (F), Descripción (G), Estado (H), Origen (I), por lo que:
   - Total: `=COUNTA(Respuestas!A2:A)`.
   - Por categoría: `=COUNTIF(Respuestas!E:E; "Hardware")` por cada categoría, y gráfico de barras o circular.
   - Por prioridad: `=COUNTIF(Respuestas!F:F; "Alta")` por cada prioridad, y gráfico de barras.
   - Los datos se actualizan solos cada vez que n8n registra una solicitud.

## Notas

- Sin `DATABASE_URL` la API usa **SQLite local solo para pruebas**; no es Neon y no debe presentarse como tal.
- No hay credenciales reales en este repositorio: `.env` está en `.gitignore` y `.env.example` solo trae valores de ejemplo.
- Los resultados de la prueba local (conteos y folios) están en `RESULTADOS_PRUEBAS.md`; son los únicos folios y cifras verificados hasta ahora.
