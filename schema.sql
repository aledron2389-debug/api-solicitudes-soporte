-- ===========================================================================
-- Esquema PostgreSQL — Sistema de gestión de solicitudes de soporte técnico
-- Base de datos: Neon (PostgreSQL). Aplicar con psql:
--   psql "$DATABASE_URL" -f schema.sql
-- Autor: Alejandro Sánchez Melchor — 2021330281
-- Materia: Programación en ambiente cliente servidor — 2do parcial
-- Docente: Ing. Alex Ramírez Galindo
-- ===========================================================================

CREATE TABLE IF NOT EXISTS solicitudes (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) UNIQUE NOT NULL,
    nombre_solicitante VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL
        CHECK (categoria IN ('Hardware', 'Software', 'Red e Internet',
                             'Impresoras', 'Cuentas y accesos', 'Otro')),
    prioridad VARCHAR(20) NOT NULL
        CHECK (prioridad IN ('Baja', 'Media', 'Alta', 'Crítica')),
    descripcion TEXT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'Recibida'
        CHECK (estado IN ('Recibida', 'En revisión', 'En proceso',
                          'Resuelta', 'Cerrada')),
    origen VARCHAR(30) NOT NULL DEFAULT 'api',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices para las consultas habituales de la API y el dashboard.
CREATE INDEX IF NOT EXISTS idx_solicitudes_folio
    ON solicitudes (folio);
CREATE INDEX IF NOT EXISTS idx_solicitudes_categoria
    ON solicitudes (categoria);
CREATE INDEX IF NOT EXISTS idx_solicitudes_prioridad
    ON solicitudes (prioridad);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado
    ON solicitudes (estado);
CREATE INDEX IF NOT EXISTS idx_solicitudes_fecha_creacion
    ON solicitudes (fecha_creacion DESC);

-- Mantener fecha_actualizacion al día en cada UPDATE.
CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizar_fecha ON solicitudes;
CREATE TRIGGER trg_actualizar_fecha
    BEFORE UPDATE ON solicitudes
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_actualizacion();
