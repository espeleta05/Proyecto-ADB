-- ---- patient ----
INSERT INTO patient (first_name, last_name, birth_date, blood_type, gender, nfc_token, allergies, notes) VALUES
('Juan',      'García Torres',     '2020-03-15', 'O+',  'Masculino', 1001, NULL,                      NULL),
('María',     'López Hernández',   '2021-06-20', 'A+',  'Femenino',  1002, 'Penicilina',              NULL),
('Carlos',    'Martínez Ruiz',     '2019-11-05', 'B+',  'Masculino', 1003, NULL,                      'Prematuro'),
('Sofía',     'Ramírez Díaz',      '2022-01-10', 'AB+', 'Femenino',  NULL, NULL,                      NULL),
('Luis',      'Sánchez Morales',   '2020-08-22', 'O-',  'Masculino', 1004, 'Látex',                   NULL),
('Valentina', 'Pérez Jiménez',     '2021-12-01', 'A-',  'Femenino',  1005, NULL,                      NULL),
('Diego',     'González Cruz',     '2019-04-18', 'B-',  'Masculino', NULL, 'Amoxicilina',             'Alergia documentada'),
('Isabella',  'Flores Vargas',     '2022-07-30', 'AB-', 'Femenino',  1006, NULL,                      NULL),
('Emilio',    'Chavez Mendoza',    '2020-10-14', 'O+',  'Masculino', 1007, NULL,                      NULL),
('Camila',    'Torres Reyes',      '2021-02-28', 'A+',  'Femenino',  1008, 'Polen',                   'Asma leve'),
('Andrés',    'Morales Castillo',  '2023-03-05', 'O+',  'Masculino', 1009, NULL,                      NULL),
('Lucía',     'Jiménez Núñez',     '2022-09-19', 'B+',  'Femenino',  NULL, NULL,                      NULL),
('Miguel',    'Rojas Alvarado',    '2020-05-07', 'A-',  'Masculino', 1010, 'Sulfa',                   NULL),
('Daniela',   'Vargas Espinoza',   '2021-11-23', 'O-',  'Femenino',  1011, NULL,                      'Cardiopatía congénita'),
('Sebastián', 'Mendoza Ríos',      '2023-06-11', 'AB+', 'Masculino', 1012, NULL,                      NULL);

-- ---- guardian ----
INSERT INTO guardian (name, lastname, birth_date, number, mail, address, curp, estado_civil, notes) VALUES
('Roberto',   'García Soto',      '1988-04-12', 5512345678, 'roberto.garcia@mail.com',   'Av. Insurgentes 120, CDMX',        'GASR880412HDFRTB01', 'Casado',         NULL),
('Ana',       'López Castro',     '1990-07-25', 5523456789, 'ana.lopez@mail.com',        'Calle Morelos 45, CDMX',           'LOCA900725MDFPSN02', 'Casada',         NULL),
('Fernando',  'Martínez Vega',    '1985-01-30', 5534567890, 'f.martinez@mail.com',       'Blvd. Juárez 890, Guadalajara',    'MAVF850130HJCRGR03', 'Divorciado',     NULL),
('Patricia',  'Ramírez León',     '1992-09-14', 5545678901, 'patricia.ramirez@mail.com', 'Col. Roma Norte, CDMX',            'RALP920914MDFMNT04', 'Soltera',        NULL),
('Jorge',     'Sánchez Peña',     '1983-06-08', 5556789012, 'jorge.sanchez@mail.com',    'Privada del Sol 33, Monterrey',    'SAPJ830608HNLNCR05', 'Casado',         NULL),
('Laura',     'Pérez Iglesias',   '1991-03-22', 5567890123, 'laura.perez@mail.com',      'Calle Hidalgo 78, Puebla',         'PEIL910322MPLRGL06', 'Casada',         NULL),
('Eduardo',   'González Bernal',  '1987-11-17', 5578901234, 'e.gonzalez@mail.com',       'Eje Central 200, CDMX',            'GOBE871117HDFNRD07', 'Soltero',        'Padre único'),
('Carmen',    'Flores Medina',    '1993-08-03', 5589012345, 'carmen.flores@mail.com',    'Av. Universidad 560, CDMX',        'FOMC930803MDFLLR08', 'Casada',         NULL),
('Hector',    'Chavez Lira',      '1986-05-29', 5590123456, 'hector.chavez@mail.com',    'Calle Reforma 99, Querétaro',      'CALH860529HQTNLR09', 'Casado',         NULL),
('Mónica',    'Torres Salinas',   '1989-12-11', 5501234567, 'monica.torres@mail.com',    'Fracc. Las Flores 14, Toluca',     'TOSM891211MMCRRN10', 'Casada',         'Madre soltera'),
('Ricardo',   'Morales Campos',   '1984-02-19', 5511223344, 'r.morales@mail.com',        'Av. Chapultepec 340, CDMX',        'MOCR840219HDFRLC11', 'Casado',         NULL),
('Elena',     'Jiménez Soto',     '1994-10-07', 5522334455, 'elena.jimenez@mail.com',    'Col. Narvarte 88, CDMX',           'JOSE941007MDFMTL12', 'Soltera',        NULL),
('Pablo',     'Rojas Fuentes',    '1981-07-16', 5533445566, 'pablo.rojas@mail.com',      'Calle 5 de Mayo 17, Veracruz',     'ROFP810716HVZJBL13', 'Casado',         NULL),
('Silvia',    'Vargas Ortega',    '1990-04-01', 5544556677, 'silvia.vargas@mail.com',    'Calle Allende 250, León',          'VAOS900401MGTRRG14', 'Casada',         NULL),
('Arturo',    'Mendoza Reina',    '1988-08-25', 5555667788, 'arturo.mendoza@mail.com',   'Av. Lázaro Cárdenas 77, Mérida',   'MERA880825HYNNRT15', 'Casado',         NULL);

-- ---- relations ----
INSERT INTO relations (patient_id, guardian_id) VALUES
(1,  1),
(2,  2),
(3,  3),
(4,  4),
(5,  4),
(6,  6),
(7,  7),
(8,  8),
(9,  9),
(10, 3),
(11, 11),
(12, 12),
(13, 13),
(14, 14),
(15, 4);

-- ---- beacons ----
INSERT INTO beacons (uuid, major, minor, lugar, estado) VALUES
('a3c2b1d0-e4f5-6789-abcd-ef0123456780', 100, 1,  'Recepción',              'Online'),
('b4d3c2e1-f5a6-7890-bcde-f01234567891', 100, 2,  'Sala de espera',         'Online'),
('c5e4d3f2-a6b7-8901-cdef-012345678902', 100, 3,  'Consultorio 1',          'Online'),
('d6f5e4a3-b7c8-9012-def0-123456789013', 100, 4,  'Consultorio 2',          'Online'),
('e7a6f5b4-c8d9-0123-ef01-234567890124', 100, 5,  'Sala de vacunación',     'Online'),
('f8b7a6c5-d9e0-1234-f012-345678901235', 100, 6,  'Farmacia',               'Offline'),
('a9c8b7d6-e0f1-2345-0123-456789012346', 200, 1,  'Pasillo principal',      'Online'),
('b0d9c8e7-f1a2-3456-1234-567890123457', 200, 2,  'Área de urgencias',      'Online'),
('c1e0d9f8-a2b3-4567-2345-678901234568', 200, 3,  'Estacionamiento',        'Offline'),
('d2f1e0a9-b3c4-5678-3456-789012345679', 200, 4,  'Entrada principal',      'Online'),
('e3a2f1b0-c4d5-6789-4567-890123456780', 300, 1,  'Laboratorio',            'Online'),
('f4b3a2c1-d5e6-7890-5678-901234567891', 300, 2,  'Cuarto de enfermería',   'Online');

-- ---- radar/gps ----
-- Estas tablas no existen en el modelo actual de SQLAlchemy.

-- ---- vaccines ----
INSERT INTO vaccines (name, inventory, manufacturer, description, min_age_months, max_age_months) VALUES
('BCG',                   150, 'Laboratorios Biológicos',  'Tuberculosis, dosis única al nacer',                0,   1),
('Hepatitis B',           200, 'MSD México',               'Previene hepatitis B, 3 dosis',                     0,   18),
('Pentavalente acelular', 180, 'Sanofi Pasteur',           'DPT + Hib + Polio inactivada, 5 dosis',             2,   18),
('Rotavirus',             120, 'GlaxoSmithKline',          'Previene gastroenteritis por rotavirus',             2,   8),
('Neumococo conjugada',   160, 'Pfizer',                   'Previene enfermedades neumocócicas',                 2,   24),
('Influenza',             300, 'Abbott Laboratorios',      'Vacuna anual contra la influenza estacional',        6,   NULL),
('SRP',                   140, 'Merck Sharp & Dohme',      'Sarampión, rubéola y parotiditis',                  12,  NULL),
('Varicela',              110, 'Sanofi Pasteur',           'Previene varicela, 2 dosis',                        12,  NULL),
('Meningococo',           90,  'Pfizer',                   'Previene meningitis bacteriana',                    9,   NULL),
('Hepatitis A',           130, 'GlaxoSmithKline',          'Previene hepatitis A, 2 dosis',                     12,  NULL),
('VPH',                   80,  'MSD México',               'Virus del papiloma humano, 2-3 dosis',              108, 204),
('COVID-19',              250, 'Pfizer-BioNTech',          'Vacuna ARNm contra COVID-19',                       6,   NULL);

-- ---- vaccination_schedule ----
INSERT INTO vaccination_schedule (scheduled_day, vaccine_id, dose_number, recommended_age_months, min_interval_days) VALUES
('2024-01-15', 1,  1, 0,   0),
('2024-01-15', 2,  1, 0,   0),
('2024-02-10', 3,  1, 2,   56),
('2024-02-10', 4,  1, 2,   28),
('2024-02-10', 5,  1, 2,   56),
('2024-04-12', 3,  2, 4,   56),
('2024-04-12', 4,  2, 4,   28),
('2024-04-12', 5,  2, 4,   56),
('2024-06-14', 3,  3, 6,   56),
('2024-06-14', 6,  1, 6,   0),
('2024-08-20', 2,  2, 8,   56),
('2024-10-05', 5,  3, 12,  56),
('2024-10-05', 7,  1, 12,  0),
('2024-10-05', 8,  1, 12,  0),
('2025-01-18', 6,  1, 18,  365),
('2025-01-18', 3,  4, 18,  365),
('2025-06-22', 8,  2, 24,  90),
('2025-06-22', 2,  3, 24,  56);

-- ---- workers ----
INSERT INTO workers (name, lastname, role, mail, curp, address, birth_date, password_hash) VALUES
('Elena',    'Ruiz Mendoza',     'Enfermero',     'elena.ruiz@vacunas.mx',     'RUME870315MDFZND01', 'Av. Doctor Vertiz 120, CDMX',   '1987-03-15', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaJOhFbG1KQ3pZv8uAE6Wz.lW'),
('Carlos',   'Perez Olvera',     'Administrador', 'c.perez@vacunas.mx',        'PEOC820720HDFRLR02', 'Calle Independencia 55, CDMX',  '1982-07-20', '$2b$12$XKv4d2zrCXWIyle1MIBbDPaz7UuyNBKQiGcH2LR4qAw9vBF7Xb.mX'),
('Patricia', 'Gomez Salazar',    'Enfermero',     'patricia.gomez@vacunas.mx', 'GOSP900505MDFMLR03', 'Col. Del Valle 300, CDMX',      '1990-05-05', '$2b$12$YLw5e3asDAXJzmf2NJCcEQba8VvzOCLRjHdI3MS5rBw0wCG8Yc.nY'),
('Miguel',   'Torres Bravo',     'Almacen',       'm.torres@vacunas.mx',       'TOBM850912HDFRRG04', 'Privada Olivos 7, CDMX',        '1985-09-12', '$2b$12$ZMx6f4btEBYKano3OKDdFRcb9WwaPDMSkIeJ4NT6sCx1xDH9Zd.oZ'),
('Fernanda', 'Lozano Vega',      'Enfermero',     'f.lozano@vacunas.mx',       'LOVF930128MDFZGN05', 'Calle Ninos Heroes 88, CDMX',   '1993-01-28', '$2b$12$ANy7g5cuFCZLbop4PLEeFSdc0XxbQENTlJfK5OU7tDy2yEI0Ae.pA'),
('Rodrigo',  'Ibarra Santana',   'Administrador', 'r.ibarra@vacunas.mx',       'ISAR780603HDFBRG06', 'Av. Taxquena 430, CDMX',        '1978-06-03', '$2b$12$BOz8h6dvGDAMcpq5QMFfGTed1YycRFOUmKgL6PV8uEz3zFJ1Bf.qB'),
('Alejandra','Fuentes Mora',     'Enfermero',     'a.fuentes@vacunas.mx',      'FUMA880414MDFNRL07', 'Col. Portales 22, CDMX',        '1988-04-14', '$2b$12$CPa9i7ewHEBNdqr6RNGgHUfe2ZzdSGPVnLhM7QW9vFa4aGK2Cg.rC'),
('Jose',     'Medina Arroyo',    'Almacen',       'j.medina@vacunas.mx',       'MEAJ911101HDFDRJ08', 'Rio Consulado 85, CDMX',        '1991-11-01', '$2b$12$DQb0j8fxIFCOers7SOHhIVgf3AAeTHQWoMiN8RX0wGb5bHL3Dh.sD'),
('Lucia',    'Castillo Herrera', 'Enfermero',     'l.castillo@vacunas.mx',     'CAHL860717MDFSTR09', 'Av. Revolucion 510, CDMX',      '1986-07-17', '$2b$12$ERc1k9gyJGDPfts8TPIiJWhg4BBfUIPXpJoO9SY1xHc6cIM4Ei.tE'),
('Alberto',  'Soria Dominguez',  'Administrador', 'a.soria@vacunas.mx',        'SODA800225HDFRBL10', 'Calle Cuauhtemoc 140, CDMX',    '1980-02-25', '$2b$12$FSd2l0hzKHEQgut9UQJjKXih5CCgVJQYqKpP0TZ2yId7dJN5Fj.uF');

-- ---- vaccinations ----
INSERT INTO vaccinations (patient_id, vaccine_id, worker_id, dose_number, applied_date) VALUES
(1,  1,  1, 1, '2020-03-16'),
(1,  2,  1, 1, '2020-03-16'),
(2,  1,  3, 1, '2021-06-21'),
(3,  3,  1, 1, '2020-01-10'),
(3,  3,  5, 2, '2020-03-12'),
(4,  5,  3, 1, '2022-03-12'),
(5,  2,  7, 1, '2020-08-23'),
(5,  3,  7, 1, '2020-10-25'),
(6,  4,  9, 1, '2022-02-05'),
(6,  5,  9, 1, '2022-02-05'),
(7,  7,  1, 1, '2020-04-20'),
(8,  1,  3, 1, '2022-07-31'),
(9,  3,  5, 1, '2020-12-16'),
(10, 6,  7, 1, '2021-08-30'),
(11, 1,  9, 1, '2023-03-06'),
(12, 5,  1, 1, '2022-11-22'),
(13, 2,  3, 1, '2020-05-08'),
(14, 8,  5, 1, '2022-05-25'),
(15, 3,  7, 1, '2023-06-12'),
(1,  3,  9, 1, '2020-05-17');
