-- pacientes
INSERT INTO patients (patient_id, first_name, last_name, birth_date, blood_type, gender, nfc_token, allergies, notes, created_at) VALUES
(1,'Juan','Perez','2010-05-12','O+','Masculino','NFC001','Ninguna','Paciente sano',NOW()),
(2,'Maria','Lopez','2012-07-22','A+','Femenino','NFC002','Penicilina','Asma leve',NOW()),
(3,'Carlos','Ramirez','2008-03-15','B+','Masculino','NFC003','Ninguna','',NOW()),
(4,'Ana','Torres','2015-11-01','AB+','Femenino','NFC004','Polen','',NOW()),
(5,'Luis','Gomez','2009-01-30','O-','Masculino','NFC005','Ninguna','',NOW()),
(6,'Sofia','Diaz','2011-09-18','A-','Femenino','NFC006','Lactosa','',NOW()),
(7,'Pedro','Morales','2013-04-10','B-','Masculino','NFC007','Ninguna','',NOW()),
(8,'Lucia','Hernandez','2014-12-05','AB-','Femenino','NFC008','Gluten','',NOW()),
(9,'Miguel','Castro','2007-06-25','O+','Masculino','NFC009','Ninguna','',NOW()),
(10,'Elena','Vargas','2016-08-14','A+','Femenino','NFC010','Ninguna','',NOW());

-- guardianes
INSERT INTO guardians (guardian_id, name, lastname, curp, number, mail, address) VALUES
(1,'Jose','Perez','CURP001',8110000001,'jose@mail.com','Monterrey'),
(2,'Laura','Lopez','CURP002',8110000002,'laura@mail.com','Apodaca'),
(3,'Rosa','Ramirez','CURP003',8110000003,'rosa@mail.com','Guadalupe'),
(4,'Miguel','Torres','CURP004',8110000004,'miguel@mail.com','San Nicolas'),
(5,'Carmen','Gomez','CURP005',8110000005,'carmen@mail.com','Escobedo'),
(6,'Pedro','Diaz','CURP006',8110000006,'pedro@mail.com','Santa Catarina'),
(7,'Luisa','Morales','CURP007',8110000007,'luisa@mail.com','Monterrey'),
(8,'Jorge','Hernandez','CURP008',8110000008,'jorge@mail.com','Apodaca'),
(9,'Patricia','Castro','CURP009',8110000009,'patricia@mail.com','Guadalupe'),
(10,'Ricardo','Vargas','CURP010',8110000010,'ricardo@mail.com','San Nicolas');

INSERT INTO relations (relation_id, patient_id, guardian_id) VALUES
(1,1,1),(2,2,2),(3,3,3),(4,4,4),(5,5,5),
(6,6,6),(7,7,7),(8,8,8),(9,9,9),(10,10,10);


-- workers
INSERT INTO workers (worker_id, name, lastname, role, mail, curp, address, birth_date, password_hash, created_at) VALUES
(3,'Luis','Gonzalez','Enfermero','luizgonzalez@mail.com','CURPW2','MTY','1993-03-03','$2b$12$nn7Z.39pV05CqflJfmHZQ.A6qwQz1lfDFrB/XVsw9xcGaD8kD9szK',NOW());
(2,'Ana','Lopez','Enfermero','analopez@mail.com','CURPW2','MTY','1994-02-02','$2b$12$nn7Z.39pV05CqflJfmHZQ.A6qwQz1lfDFrB/XVsw9xcGaD8kD9szK',NOW());
(1,'Admin','Uno','Administrador','admin1@mail.com','CURPW1','MTY','1990-01-01','$2b$12$f4jJCWwqo7Wv1qXiCFBUsOYz5tHT09pffJS9UMy44NZ1hJ5.HnSay',NOW());


-- vacunas
INSERT INTO vaccines (id_vaccine, name, inventory, manufacturer, description) VALUES
(1,'BCG',100,'Pfizer','Tuberculosis'),
(2,'Hepatitis B',200,'Moderna','Hepatitis'),
(3,'Pentavalente',150,'GSK','5 enfermedades'),
(4,'Rotavirus',120,'Sanofi','Rotavirus'),
(5,'Neumococo',130,'Pfizer','Neumonia'),
(6,'Influenza',300,'Moderna','Gripe'),
(7,'SRP',180,'GSK','Sarampion'),
(8,'DPT',90,'Sanofi','Difteria, tos ferina y tétanos (refuerzo)'),
(9,'OPV (Sabin)',90,'Sanofi','Poliomielitis'),
(10,'Varicela',90,'Sanofi','Varicela'),
(11,'COVID-19',500,'Pfizer','Coronavirus'),
(12,'VPH',110,'Merck','Virus del Papiloma Humano');

-- esquema de vacunacion oficial
INSERT INTO vaccination_scheme (vaccine_id, dose_number, ideal_age_months, min_interval_days) VALUES
-- BCG
(1, 'Única', 0, 0),

-- Hepatitis B
(2, 'Primera Dosis', 0, 0),
(2, 'Segunda Dosis', 2, 56),
(2, 'Tercera Dosis', 6, 112),

-- Pentavalente Acelular (DPaT+VPI+Hib)
(3, 'Primera Dosis', 2, 0),
(3, 'Seguna Dosis', 4, 56),
(3, 'Tercera Dosis', 6, 56),
(3, 'Cuarta Dosis', 18, 365),

-- Rotavirus
(4, 'Primera Dosis', 2, 0),
(4, 'Seguna Dosis', 4, 28),
(4, 'Tercera Dosis', 6, 28),

-- Neumocócica Conjugada
(5, 'Primera Dosis', 2, 0),
(5, 'Seguna Dosis', 4, 56),
(5, 'Refuerzo', 12, 180),

-- Influenza
(6, 'Primera Dosis', 6, 0),
(6, 'Seguna Dosis', 7, 28),
(6, 'Refuerzo Anual (24m)', 24, 330),
(6, 'Refuerzo Anual (36m)', 36, 330),
(6, 'Refuerzo Anual (48m)', 48, 330),
(6, 'Refuerzo Anual (59m)', 59, 330),

-- SRP (Sarampión, Rubéola, Parotiditis)
(7, 'Primera Dosis', 12, 0),
(7, 'Seguna Dosis', 72, 365), -- 6 años

-- DPT
(8, 'Refuerzo', 48, 0), -- 4 años

-- OPV
(9, 'Unica', 59, 0),-- 5 años

-- VPH
(12, 'Unica', 112, 0); -- 11 años


--records para cada paciente
INSERT INTO vaccination_records (record_id, patient_id, vaccine_id, worker_id, applied_date, dose_applied, lot_number) VALUES
(1,1,1,2,'2024-01-01','Primera','LOT001'),
(2,2,2,2,'2024-01-02','Primera','LOT002'),
(3,3,3,2,'2024-01-03','Primera','LOT003'),
(4,4,4,2,'2024-01-04','Primera','LOT004'),
(5,5,5,2,'2024-01-05','Primera','LOT005'),
(6,6,6,3,'2024-01-06','Primera','LOT006'),
(7,7,7,3,'2024-01-07','Primera','LOT007'),
(8,8,8,3,'2024-01-08','Primera','LOT008'),
(9,9,9,3,'2024-01-09','Primera','LOT009'),
(10,10,10,3,'2024-01-10','Primera','LOT010');