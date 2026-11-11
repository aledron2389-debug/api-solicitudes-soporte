# Workflow n8n — Solicitudes de soporte técnico

Automatiza el flujo completo: **Google Forms → Google Sheets → API (Render/Neon) → Gmail → Google Sheets**.

## Flujo (5 nodos)

| # | Nodo | Qué hace |
|---|------|----------|
| 1 | Google Sheets Trigger | Se dispara con cada fila nueva en la hoja `Respuestas` (vinculada a Google Forms). |
| 2 | HTTP Request — Registrar en API | `POST https://<render-url>/api/solicitudes` con los datos de la fila. La API valida y devuelve el folio (`SOL-2026-…`). |
| 3 | IF — ¿Registro exitoso? | Continúa solo si la API responde **201**. Si falla, la ejecución se detiene y se revisa el error en n8n (no se envía correo con un folio inexistente). |
| 4 | Gmail — Notificar al solicitante | Correo de confirmación con el folio al email del solicitante. |
| 5 | Google Sheets — Escribir folio y estado | Escribe el folio y el estado `Recibida` en la misma fila que disparó el flujo (columnas `Folio` y `Estado`). |

## Importar el workflow

1. En n8n: **Workflows → ⋯ → Import from File** y elige `n8n-workflow.json`.
2. Conecta las credenciales (ver abajo) en los nodos que las piden.
3. Reemplaza los valores marcados en **Variables a configurar**.
4. **Execute Workflow** con una fila de prueba, verifica el folio en la API y el correo recibido, y luego activa el workflow (interruptor **Active**).

## Variables a configurar

| Variable / campo | Dónde | Valor |
|---|---|---|
| `<render-url>` | Nodo HTTP Request, campo URL | URL real de Render, sin `https://` inicial duplicado. Ejemplo: `api-solicitudes-soporte.onrender.com`. La URL final queda `https://api-solicitudes-soporte.onrender.com/api/solicitudes`. |
| `ID_DE_TU_HOJA_DE_GOOGLE_SHEETS` | Nodos Google Sheets Trigger y Google Sheets (campo Document) | Ya configurado en el workflow: `1JO8IqTb_x9qIuJWmczViM3pEWd9V0-2HhA9cQFOSypk` (hoja "Solicitudes de soporte técnico - Respuestas y Dashboard"). Si se usa otra hoja, reemplazar ese ID. |
| Hoja `Respuestas` | Nodos Google Sheets | Nombre exacto de la pestaña vinculada a Google Forms. |
| Credencial Google Sheets (OAuth2) | Nodos Google Sheets Trigger y Google Sheets | Cuenta de Google con acceso de edición a la hoja. Se crea en n8n: **Credentials → Google Sheets OAuth2**. |
| Credencial Gmail (OAuth2) | Nodo Gmail | Cuenta de Gmail lista y conectada (2026-11-11) para las notificaciones con folio. En n8n se crea la credencial con esa cuenta: **Credentials → Gmail OAuth2**. |

## Formato de la hoja `Respuestas`

La hoja ya existe: **"Solicitudes de soporte técnico - Respuestas y Dashboard"**, ID `1JO8IqTb_x9qIuJWmczViM3pEWd9V0-2HhA9cQFOSypk`, con pestañas `Respuestas` y `Dashboard`. El formulario también existe: **"Solicitud de soporte técnico"**, ID `1pXdV_doHLG_9azAX_bRc3H0ckMEBp_tF3SKdHceOZnw`, publicado en https://docs.google.com/forms/d/e/1FAIpQLSexH3Tg4eKpLxxOdLH9NV06EsgZyZkBO727Fe0IqsMuBDwBVA/viewform, con las 5 preguntas obligatorias (Nombre completo, Correo electrónico, Categoría, Prioridad, Descripción del problema). El formulario no está vinculado automáticamente a la hoja: este workflow es el puente (cada respuesta que llega a `Respuestas` se registra en la API y se notifica por Gmail).

| Fecha | Folio | Nombre | Email | Categoría | Prioridad | Descripción | Estado | Origen |
|---|---|---|---|---|---|---|---|---|
| (la pone Forms) | *(lo escribe n8n)* | María López | maria@ejemplo.com | Hardware | Alta | La computadora no enciende. | *(lo escribe n8n)* | google_forms |

- **Categoría** debe ser una de: `Hardware`, `Software`, `Red e Internet`, `Impresoras`, `Cuentas y accesos`, `Otro`.
- **Prioridad** debe ser una de: `Baja`, `Media`, `Alta`, `Crítica`.
- En Google Forms conviene usar preguntas de **opción múltiple** con exactamente esos valores, para que la API nunca rechace la fila por un valor distinto.
- Las columnas `Folio`, `Estado` y `Origen` ya existen en la hoja; n8n llena `Folio` y `Estado` (y `Origen` queda como `google_forms` en la API).

## Formato exacto del correo

- **Para:** el email de la fila (campo `Email`).
- **Asunto:** `Solicitud de soporte registrada — Folio SOL-2026-0001` (con el folio real).
- **Cuerpo (texto plano):**

```text
Hola María Fernanda López García,

Tu solicitud de soporte técnico fue registrada correctamente.

Folio: SOL-2026-0001
Categoría: Hardware
Prioridad: Alta
Estado: Recibida
Descripción: La computadora del laboratorio 3 no enciende; al presionar el botón solo parpadea el LED.

El equipo de soporte técnico revisará tu solicitud y te contactará por este correo. Puedes consultar el estado de tu solicitud con tu folio.

Saludos,
Equipo de Soporte Técnico
```

## Prueba del flujo (recomendada antes de activar)

1. Envía una respuesta de prueba en Google Forms.
2. En n8n, abre la ejecución y verifica: HTTP Request responde **201** con un `folio`, Gmail aparece como enviado y la fila en Sheets tiene folio y estado.
3. Comprueba en la API: `GET https://<render-url>/api/solicitudes/<folio>`.
4. Si el nodo IF cae en la rama FALSE, abre el nodo HTTP Request en esa ejecución: ahí se ve el error de la API (`detalles` indica qué campo falló, normalmente una categoría o prioridad con otro texto).

## Qué NO hace este workflow

- No crea la base de datos ni despliega la API (eso es Neon + Render, ver `README.md`).
- No actualiza el dashboard: el dashboard vive en otra pestaña de la misma hoja y se alimenta de la pestaña `Respuestas` con fórmulas (ver `README.md`).
