"""
API REST — Sistema automatizado de gestión de solicitudes de soporte técnico.

Flask + PostgreSQL (Neon, vía DATABASE_URL) con fallback a SQLite local
para pruebas (ver db.py). Despliegue en Render con gunicorn (ver Procfile).

Endpoints:
    GET    /health                          Salud del servicio
    GET    /api/solicitudes                 Lista (filtros ?categoria=&prioridad=&estado=)
    GET    /api/solicitudes/<folio>         Una solicitud por folio
    POST   /api/solicitudes                 Crea una solicitud (folio SOL-2026-0001…)
    PUT    /api/solicitudes/<folio>         Cambia el estado
    GET    /api/estadisticas                total, por_categoria, por_prioridad, por_estado

Autor: Alejandro Sánchez Melchor — 2021330281
Materia: Programación en ambiente cliente servidor — 2do parcial
Docente: Ing. Alex Ramírez Galindo
"""

import os

from flask import Flask, jsonify, request
from flask_cors import CORS

import db

app = Flask(__name__)
# CORS habilitado para que Google Apps Script / n8n / el dashboard
# y cualquier cliente web puedan consumir la API.
CORS(app)

# Crear la tabla local al arrancar (solo tiene efecto en SQLite;
# en Neon el esquema se aplica con schema.sql).
db.inicializar_bd()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def error(mensaje, codigo):
    """Respuesta de error uniforme en JSON."""
    return jsonify({"ok": False, "error": mensaje}), codigo


@app.errorhandler(404)
def no_encontrado(_e):
    return error("Ruta no encontrada.", 404)


@app.errorhandler(405)
def metodo_no_permitido(_e):
    return error("Método no permitido en esta ruta.", 405)


@app.errorhandler(500)
def error_interno(_e):
    return error("Error interno del servidor.", 500)


# ---------------------------------------------------------------------------
# Salud
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """GET /health — comprobación rápida de que la API responde."""
    return jsonify({
        "ok": True,
        "status": "ok",
        "servicio": "api-solicitudes-soporte",
        "base_datos": "postgres" if db.es_postgres() else "sqlite (local)",
    }), 200


# ---------------------------------------------------------------------------
# Solicitudes
# ---------------------------------------------------------------------------
@app.route("/api/solicitudes", methods=["GET"])
def listar():
    """GET /api/solicitudes?categoria=&prioridad=&estado=

    Los filtros que no correspondan a los catálogos devuelven 400.
    """
    categoria = request.args.get("categoria")
    prioridad = request.args.get("prioridad")
    estado = request.args.get("estado")

    if categoria and categoria not in db.CATEGORIAS:
        return error("categoria debe ser una de: " + ", ".join(db.CATEGORIAS) + ".", 400)
    if prioridad and prioridad not in db.PRIORIDADES:
        return error("prioridad debe ser una de: " + ", ".join(db.PRIORIDADES) + ".", 400)
    if estado and estado not in db.ESTADOS:
        return error("estado debe ser uno de: " + ", ".join(db.ESTADOS) + ".", 400)

    solicitudes = db.listar_solicitudes(categoria, prioridad, estado)
    return jsonify({"ok": True, "total": len(solicitudes),
                    "solicitudes": solicitudes}), 200


@app.route("/api/solicitudes/<folio>", methods=["GET"])
def obtener(folio):
    """GET /api/solicitudes/SOL-2026-0001 — una solicitud por folio."""
    solicitud = db.obtener_por_folio(folio)
    if solicitud is None:
        return error("No existe una solicitud con el folio %s." % folio, 404)
    return jsonify({"ok": True, "solicitud": solicitud}), 200


@app.route("/api/solicitudes", methods=["POST"])
def crear():
    """POST /api/solicitudes — registra una solicitud y genera su folio.

    Cuerpo JSON:
        {
          "nombre_solicitante": "María López",
          "email": "maria@ejemplo.com",
          "categoria": "Hardware",
          "prioridad": "Alta",
          "descripcion": "La computadora no enciende.",
          "origen": "google_forms"   (opcional, por defecto "api")
        }
    Respuesta 201 con la solicitud creada, incluido su folio.
    """
    if not request.is_json:
        return error("El cuerpo debe ser JSON (Content-Type: application/json).", 400)
    datos = request.get_json(silent=True)
    if datos is None:
        return error("El cuerpo JSON no es válido.", 400)

    errores = db.validar_datos(datos)
    if errores:
        return jsonify({"ok": False, "error": "Datos inválidos.",
                        "detalles": errores}), 400

    solicitud = db.crear_solicitud(datos)
    return jsonify({"ok": True, "mensaje": "Solicitud registrada.",
                    "folio": solicitud["folio"],
                    "solicitud": solicitud}), 201


@app.route("/api/solicitudes/<folio>", methods=["PUT"])
def cambiar_estado(folio):
    """PUT /api/solicitudes/<folio> — cambia el estado.

    Cuerpo JSON: { "estado": "En proceso" }
    Estados permitidos: Recibida, En revisión, En proceso, Resuelta, Cerrada.
    """
    if not request.is_json:
        return error("El cuerpo debe ser JSON (Content-Type: application/json).", 400)
    datos = request.get_json(silent=True) or {}
    nuevo_estado = datos.get("estado")

    if nuevo_estado not in db.ESTADOS:
        return error("estado debe ser uno de: " + ", ".join(db.ESTADOS) + ".", 400)

    solicitud = db.actualizar_estado(folio, nuevo_estado)
    if solicitud is None:
        return error("No existe una solicitud con el folio %s." % folio, 404)
    return jsonify({"ok": True, "mensaje": "Estado actualizado.",
                    "solicitud": solicitud}), 200


# ---------------------------------------------------------------------------
# Estadísticas (alimentan el dashboard de Google Sheets)
# ---------------------------------------------------------------------------
@app.route("/api/estadisticas", methods=["GET"])
def estadisticas():
    """GET /api/estadisticas — total, por_categoria, por_prioridad, por_estado."""
    stats = db.estadisticas()
    return jsonify({"ok": True, "estadisticas": stats}), 200


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
