-- ===========================================================================
-- Datos semilla — Sistema de gestión de solicitudes de soporte técnico
-- 12 solicitudes realistas para poblar el dashboard (Neon / PostgreSQL).
-- Aplicar DESPUÉS de schema.sql:
--   psql "$DATABASE_URL" -f seed.sql
-- Totales esperados tras la siembra:
--   total = 12
--   por categoría: Hardware 3, Software 2, Red e Internet 2, Impresoras 2,
--                  Cuentas y accesos 2, Otro 1
--   por prioridad: Alta 4, Media 4, Crítica 2, Baja 2
--   por estado: Recibida 4, En proceso 3, Resuelta 3, En revisión 1, Cerrada 1
-- ===========================================================================

INSERT INTO solicitudes (folio, nombre_solicitante, email, categoria, prioridad, descripcion, estado, origen) VALUES
('SOL-2026-0001', 'María Fernanda López García', 'maria.lopez@ejemplo.com', 'Hardware', 'Alta', 'La computadora del laboratorio 3 no enciende; al presionar el botón solo parpadea el LED.', 'Recibida', 'seed'),
('SOL-2026-0002', 'Carlos Eduardo Ramírez Torres', 'carlos.ramirez@ejemplo.com', 'Software', 'Media', 'El programa de contabilidad se cierra solo al generar el reporte mensual.', 'En proceso', 'seed'),
('SOL-2026-0003', 'Ana Paola Hernández Ruiz', 'ana.hernandez@ejemplo.com', 'Red e Internet', 'Crítica', 'No hay internet en todo el edificio B desde las 8:00; ningún equipo obtiene dirección IP.', 'Recibida', 'seed'),
('SOL-2026-0004', 'Luis Miguel Torres Sánchez', 'luis.torres@ejemplo.com', 'Impresoras', 'Baja', 'La impresora del área administrativa imprime con líneas blancas; probablemente falta tóner.', 'Resuelta', 'seed'),
('SOL-2026-0005', 'Fernanda Castillo Morales', 'fernanda.castillo@ejemplo.com', 'Cuentas y accesos', 'Alta', 'Olvidé mi contraseña del correo institucional y el enlace de recuperación no llega.', 'En revisión', 'seed'),
('SOL-2026-0006', 'Diego Alejandro Vargas León', 'diego.vargas@ejemplo.com', 'Software', 'Media', 'Necesito instalar el paquete de ofimática actualizado en las 10 computadoras del salón 5.', 'Recibida', 'seed'),
('SOL-2026-0007', 'Valeria Mendoza Ortiz', 'valeria.mendoza@ejemplo.com', 'Hardware', 'Crítica', 'El disco duro del servidor de archivos hace ruidos extraños y varios archivos ya no abren.', 'En proceso', 'seed'),
('SOL-2026-0008', 'Jorge Alberto Salinas Cruz', 'jorge.salinas@ejemplo.com', 'Red e Internet', 'Alta', 'La red Wi-Fi de la biblioteca se desconecta cada 10 minutos en los equipos de los alumnos.', 'Resuelta', 'seed'),
('SOL-2026-0009', 'Camila Reyes Duarte', 'camila.reyes@ejemplo.com', 'Impresoras', 'Media', 'La impresora de la sala de cómputo atasca el papel en cada impresión a doble cara.', 'Cerrada', 'seed'),
('SOL-2026-0010', 'Andrés Felipe Navarro Peña', 'andres.navarro@ejemplo.com', 'Cuentas y accesos', 'Baja', 'Solicito acceso a la carpeta compartida del departamento de control escolar.', 'Recibida', 'seed'),
('SOL-2026-0011', 'Sofía Isabel Delgado Ramos', 'sofia.delgado@ejemplo.com', 'Otro', 'Media', 'Solicito capacitación básica sobre el uso del proyector del auditorio para el personal nuevo.', 'En proceso', 'seed'),
('SOL-2026-0012', 'Miguel Ángel Fuentes Herrera', 'miguel.fuentes@ejemplo.com', 'Hardware', 'Alta', 'El teclado de la computadora de recepción tiene varias teclas que no responden.', 'Resuelta', 'seed')
ON CONFLICT (folio) DO NOTHING;
