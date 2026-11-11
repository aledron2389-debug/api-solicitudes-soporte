"""
Siembra de datos — Sistema de gestión de solicitudes de soporte técnico.

Inserta las mismas 12 solicitudes realistas de seed.sql usando la capa
de datos (db.py), por lo que funciona tanto con SQLite local como con
PostgreSQL/Neon (DATABASE_URL). Los folios se generan automáticamente
en orden (SOL-2026-0001 … SOL-2026-0012) si la tabla está vacía.

Uso:
    python seed.py            # siembra solo si la tabla está vacía
    python seed.py --reset    # borra todo y vuelve a sembrar

Autor: Alejandro Sánchez Melchor — 2021330281
"""

import argparse
import sys

import db

SOLICITUDES_SEMILLA = [
    {"nombre_solicitante": "María Fernanda López García",
     "email": "maria.lopez@ejemplo.com", "categoria": "Hardware",
     "prioridad": "Alta",
     "descripcion": "La computadora del laboratorio 3 no enciende; al presionar el botón solo parpadea el LED.",
     "estado": "Recibida"},
    {"nombre_solicitante": "Carlos Eduardo Ramírez Torres",
     "email": "carlos.ramirez@ejemplo.com", "categoria": "Software",
     "prioridad": "Media",
     "descripcion": "El programa de contabilidad se cierra solo al generar el reporte mensual.",
     "estado": "En proceso"},
    {"nombre_solicitante": "Ana Paola Hernández Ruiz",
     "email": "ana.hernandez@ejemplo.com", "categoria": "Red e Internet",
     "prioridad": "Crítica",
     "descripcion": "No hay internet en todo el edificio B desde las 8:00; ningún equipo obtiene dirección IP.",
     "estado": "Recibida"},
    {"nombre_solicitante": "Luis Miguel Torres Sánchez",
     "email": "luis.torres@ejemplo.com", "categoria": "Impresoras",
     "prioridad": "Baja",
     "descripcion": "La impresora del área administrativa imprime con líneas blancas; probablemente falta tóner.",
     "estado": "Resuelta"},
    {"nombre_solicitante": "Fernanda Castillo Morales",
     "email": "fernanda.castillo@ejemplo.com", "categoria": "Cuentas y accesos",
     "prioridad": "Alta",
     "descripcion": "Olvidé mi contraseña del correo institucional y el enlace de recuperación no llega.",
     "estado": "En revisión"},
    {"nombre_solicitante": "Diego Alejandro Vargas León",
     "email": "diego.vargas@ejemplo.com", "categoria": "Software",
     "prioridad": "Media",
     "descripcion": "Necesito instalar el paquete de ofimática actualizado en las 10 computadoras del salón 5.",
     "estado": "Recibida"},
    {"nombre_solicitante": "Valeria Mendoza Ortiz",
     "email": "valeria.mendoza@ejemplo.com", "categoria": "Hardware",
     "prioridad": "Crítica",
     "descripcion": "El disco duro del servidor de archivos hace ruidos extraños y varios archivos ya no abren.",
     "estado": "En proceso"},
    {"nombre_solicitante": "Jorge Alberto Salinas Cruz",
     "email": "jorge.salinas@ejemplo.com", "categoria": "Red e Internet",
     "prioridad": "Alta",
     "descripcion": "La red Wi-Fi de la biblioteca se desconecta cada 10 minutos en los equipos de los alumnos.",
     "estado": "Resuelta"},
    {"nombre_solicitante": "Camila Reyes Duarte",
     "email": "camila.reyes@ejemplo.com", "categoria": "Impresoras",
     "prioridad": "Media",
     "descripcion": "La impresora de la sala de cómputo atasca el papel en cada impresión a doble cara.",
     "estado": "Cerrada"},
    {"nombre_solicitante": "Andrés Felipe Navarro Peña",
     "email": "andres.navarro@ejemplo.com", "categoria": "Cuentas y accesos",
     "prioridad": "Baja",
     "descripcion": "Solicito acceso a la carpeta compartida del departamento de control escolar.",
     "estado": "Recibida"},
    {"nombre_solicitante": "Sofía Isabel Delgado Ramos",
     "email": "sofia.delgado@ejemplo.com", "categoria": "Otro",
     "prioridad": "Media",
     "descripcion": "Solicito capacitación básica sobre el uso del proyector del auditorio para el personal nuevo.",
     "estado": "En proceso"},
    {"nombre_solicitante": "Miguel Ángel Fuentes Herrera",
     "email": "miguel.fuentes@ejemplo.com", "categoria": "Hardware",
     "prioridad": "Alta",
     "descripcion": "El teclado de la computadora de recepción tiene varias teclas que no responden.",
     "estado": "Resuelta"},
]


def main():
    parser = argparse.ArgumentParser(description="Siembra 12 solicitudes de ejemplo.")
    parser.add_argument("--reset", action="store_true",
                        help="Borra todas las solicitudes antes de sembrar.")
    args = parser.parse_args()

    db.inicializar_bd()
    stats = db.estadisticas()

    if args.reset and stats["total"] > 0:
        conn, pg = db.conectar()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM solicitudes")
            conn.commit()
        finally:
            conn.close()
        print("Tabla vaciada (%d registros eliminados)." % stats["total"])
    elif stats["total"] > 0:
        print("La tabla ya tiene %d solicitudes; no se sembró nada." % stats["total"])
        print("Usa --reset para borrar y volver a sembrar.")
        return 0

    for item in SOLICITUDES_SEMILLA:
        estado = item.pop("estado")
        registro = db.crear_solicitud(dict(item, origen="seed"))
        if estado != "Recibida":
            db.actualizar_estado(registro["folio"], estado)
        print("%s | %-40s | %-18s | %-8s | %s" % (
            registro["folio"], registro["nombre_solicitante"],
            registro["categoria"], registro["prioridad"], estado))

    stats = db.estadisticas()
    print("\nTotal sembrado: %d" % stats["total"])
    print("Por categoría: %s" % stats["por_categoria"])
    print("Por prioridad: %s" % stats["por_prioridad"])
    print("Por estado: %s" % stats["por_estado"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
