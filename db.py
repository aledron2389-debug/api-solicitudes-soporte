"""
Capa de acceso a datos — Sistema de gestión de solicitudes de soporte técnico.

- Si existe la variable de entorno DATABASE_URL (PostgreSQL en Neon),
  se conecta con psycopg2.
- Si NO existe, usa SQLite local (archivo solicitudes.db junto a este
  módulo) como fallback SOLO para pruebas locales. SQLite NO es Neon:
  el esquema de producción es schema.sql (PostgreSQL).
- La misma lógica de negocio (folios, validación de catálogos) se usa
  en ambos motores; solo cambia el marcador de parámetros (%s vs ?)
  y algunas funciones SQL.

Autor: Alejandro Sánchez Melchor — 2021330281
Materia: Programación en ambiente cliente servidor — 2do parcial
Docente: Ing. Alex Ramírez Galindo
"""

import os
import re
import sqlite3
from datetime import datetime

# ---------------------------------------------------------------------------
# Catálogos (deben coincidir con la consigna y con app.py)
# ---------------------------------------------------------------------------
CATEGORIAS = [
    "Hardware",
    "Software",
    "Red e Internet",
    "Impresoras",
    "Cuentas y accesos",
    "Otro",
]

PRIORIDADES = ["Baja", "Media", "Alta", "Crítica"]

ESTADOS = ["Recibida", "En revisión", "En proceso", "Resuelta", "Cerrada"]

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# Esquema SQLite (equivalente al schema.sql de PostgreSQL).
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio VARCHAR(20) UNIQUE NOT NULL,
    nombre_solicitante VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    prioridad VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'Recibida',
    origen VARCHAR(30) NOT NULL DEFAULT 'api',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_solicitudes_folio ON solicitudes (folio);
CREATE INDEX IF NOT EXISTS idx_solicitudes_categoria ON solicitudes (categoria);
CREATE INDEX IF NOT EXISTS idx_solicitudes_prioridad ON solicitudes (prioridad);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes (estado);
"""


def es_postgres():
    """True si hay DATABASE_URL configurada (Neon / PostgreSQL)."""
    return bool(os.environ.get("DATABASE_URL"))


def _conectar_sqlite():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "solicitudes.db")
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    return conn


def conectar():
    """Devuelve (conexion, es_postgres). La conexión se abre por operación."""
    if es_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        return conn, True
    conn = _conectar_sqlite()
    return conn, False


def inicializar_bd():
    """Crea la tabla si no existe (solo SQLite local; en Neon se usa schema.sql)."""
    conn, pg = conectar()
    try:
        if pg:
            # En producción el esquema se aplica con schema.sql (psql).
            return
        cur = conn.cursor()
        cur.executescript(SQLITE_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _fila_a_dict(fila):
    """Convierte una fila (psycopg2 DictCursor o sqlite3.Row) a dict JSON."""
    d = dict(fila)
    for clave in ("fecha_creacion", "fecha_actualizacion"):
        valor = d.get(clave)
        if isinstance(valor, datetime):
            d[clave] = valor.isoformat()
        elif valor is not None:
            d[clave] = str(valor)
    return d


def validar_datos(datos):
    """Valida el cuerpo de una solicitud. Devuelve lista de errores (vacía = OK)."""
    errores = []
    if not datos or not isinstance(datos, dict):
        return ["El cuerpo debe ser un objeto JSON."]
    nombre = str(datos.get("nombre_solicitante") or "").strip()
    email = str(datos.get("email") or "").strip()
    categoria = datos.get("categoria")
    prioridad = datos.get("prioridad")
    descripcion = str(datos.get("descripcion") or "").strip()

    if not nombre:
        errores.append("nombre_solicitante es obligatorio.")
    if not email or not EMAIL_RE.match(email):
        errores.append("email no es válido (ejemplo: usuario@ejemplo.com).")
    if categoria not in CATEGORIAS:
        errores.append(
            "categoria debe ser una de: " + ", ".join(CATEGORIAS) + "."
        )
    if prioridad not in PRIORIDADES:
        errores.append(
            "prioridad debe ser una de: " + ", ".join(PRIORIDADES) + "."
        )
    if not descripcion:
        errores.append("descripcion es obligatoria.")
    return errores


def _generar_folio(cursor, pg):
    """Genera el siguiente folio secuencial SOL-2026-0001, SOL-2026-0002, ...

    Busca el número mayor ya usado (folio con prefijo SOL-2026-) y suma 1.
    """
    cursor.execute("SELECT folio FROM solicitudes WHERE folio LIKE 'SOL-2026-%'")
    maximo = 0
    for (folio,) in cursor.fetchall():
        try:
            numero = int(folio.rsplit("-", 1)[1])
            maximo = max(maximo, numero)
        except (ValueError, IndexError):
            continue
    return "SOL-2026-%04d" % (maximo + 1)


def crear_solicitud(datos):
    """Inserta una solicitud y devuelve su dict (con folio generado)."""
    conn, pg = conectar()
    try:
        cur = conn.cursor()
        folio = _generar_folio(cur, pg)
        origen = str(datos.get("origen") or "api").strip() or "api"
        if pg:
            cur.execute(
                """INSERT INTO solicitudes
                   (folio, nombre_solicitante, email, categoria, prioridad,
                    descripcion, estado, origen)
                   VALUES (%s, %s, %s, %s, %s, %s, 'Recibida', %s)
                   RETURNING *""",
                (folio,
                 str(datos["nombre_solicitante"]).strip(),
                 str(datos["email"]).strip(),
                 datos["categoria"], datos["prioridad"],
                 str(datos["descripcion"]).strip(), origen),
            )
            import psycopg2.extras
            fila = cur.fetchone()
            # RETURNING con cursor normal devuelve tupla; re-consultar por folio.
            cur.execute("SELECT * FROM solicitudes WHERE folio = %s", (folio,))
            fila = cur.fetchone()
            columnas = [d[0] for d in cur.description]
            registro = dict(zip(columnas, fila))
        else:
            cur.execute(
                """INSERT INTO solicitudes
                   (folio, nombre_solicitante, email, categoria, prioridad,
                    descripcion, estado, origen)
                   VALUES (?, ?, ?, ?, ?, ?, 'Recibida', ?)""",
                (folio,
                 str(datos["nombre_solicitante"]).strip(),
                 str(datos["email"]).strip(),
                 datos["categoria"], datos["prioridad"],
                 str(datos["descripcion"]).strip(), origen),
            )
            conn.commit()
            cur.execute("SELECT * FROM solicitudes WHERE folio = ?", (folio,))
            registro = _fila_a_dict(cur.fetchone())
        conn.commit()
        return _fila_a_dict(registro) if pg else registro
    finally:
        conn.close()


def listar_solicitudes(categoria=None, prioridad=None, estado=None):
    """Lista solicitudes con filtros opcionales, más recientes primero."""
    conn, pg = conectar()
    try:
        cur = conn.cursor()
        marcador = "%s" if pg else "?"
        sql = "SELECT * FROM solicitudes WHERE 1=1"
        params = []
        if categoria:
            sql += " AND categoria = " + marcador
            params.append(categoria)
        if prioridad:
            sql += " AND prioridad = " + marcador
            params.append(prioridad)
        if estado:
            sql += " AND estado = " + marcador
            params.append(estado)
        sql += " ORDER BY fecha_creacion DESC, id DESC"
        cur.execute(sql, params)
        if pg:
            columnas = [d[0] for d in cur.description]
            return [_fila_a_dict(dict(zip(columnas, f)))
                    for f in cur.fetchall()]
        return [_fila_a_dict(f) for f in cur.fetchall()]
    finally:
        conn.close()


def obtener_por_folio(folio):
    """Devuelve una solicitud por folio, o None si no existe."""
    conn, pg = conectar()
    try:
        cur = conn.cursor()
        marcador = "%s" if pg else "?"
        cur.execute("SELECT * FROM solicitudes WHERE folio = " + marcador,
                    (folio,))
        fila = cur.fetchone()
        if fila is None:
            return None
        if pg:
            columnas = [d[0] for d in cur.description]
            return _fila_a_dict(dict(zip(columnas, fila)))
        return _fila_a_dict(fila)
    finally:
        conn.close()


def actualizar_estado(folio, nuevo_estado):
    """Cambia el estado de una solicitud. Devuelve el registro o None."""
    conn, pg = conectar()
    try:
        cur = conn.cursor()
        marcador = "%s" if pg else "?"
        if pg:
            cur.execute(
                """UPDATE solicitudes
                   SET estado = %s, fecha_actualizacion = NOW()
                   WHERE folio = %s""",
                (nuevo_estado, folio),
            )
        else:
            cur.execute(
                """UPDATE solicitudes
                   SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                   WHERE folio = ?""",
                (nuevo_estado, folio),
            )
        if cur.rowcount == 0:
            conn.rollback()
            return None
        conn.commit()
        return obtener_por_folio(folio)
    finally:
        conn.close()


def estadisticas():
    """Totales: total, por_categoria, por_prioridad, por_estado."""
    conn, pg = conectar()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM solicitudes")
        total = cur.fetchone()[0]

        def conteo(columna):
            cur.execute(
                "SELECT %s, COUNT(*) FROM solicitudes GROUP BY %s "
                "ORDER BY COUNT(*) DESC" % (columna, columna)
            )
            return {str(k): int(v) for k, v in cur.fetchall()}

        return {
            "total": int(total),
            "por_categoria": conteo("categoria"),
            "por_prioridad": conteo("prioridad"),
            "por_estado": conteo("estado"),
        }
    finally:
        conn.close()
