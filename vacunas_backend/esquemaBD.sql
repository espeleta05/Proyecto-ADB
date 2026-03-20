--base de datos: vacunas

-- Tabla de Vacunas
CREATE TABLE vaccines (
    id_vaccine INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    inventory INT DEFAULT 0,
    manufacturer VARCHAR(100),
    description TEXT
) 

-- Tabla de Tutores
CREATE TABLE guardians (
    guardian_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    lastname VARCHAR(50),
    curp VARCHAR(18) UNIQUE,
    number BIGINT,
    mail VARCHAR(100),
    address VARCHAR(200),
    estado_civil VARCHAR(50),
    notes TEXT
) 

-- Tabla de Trabajadores
CREATE TABLE workers (
    worker_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    lastname VARCHAR(100),
    role ENUM('Administrador', 'Almacen', 'Enfermero'),
    mail VARCHAR(100) UNIQUE,
    curp VARCHAR(18),
    address VARCHAR(250),
    birth_date DATE,
    password_hash VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) 

-- Tabla de Pacientes
CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    blood_type ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-'),
    gender ENUM('Masculino','Femenino'),
    nfc_token VARCHAR(50) UNIQUE,
    allergies TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) 

-- Relacion Paciente-Tutor (Muchos a Muchos)
CREATE TABLE relations (
    relation_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    guardian_id INT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (guardian_id) REFERENCES guardians(guardian_id) ON DELETE CASCADE
) 

-- Esquema Oficial de Vacunacion
CREATE TABLE vaccination_scheme (
    id_scheme INT AUTO_INCREMENT PRIMARY KEY,
    vaccine_id INT,
    dose_number VARCHAR(50) NOT NULL,
    ideal_age_months INT NOT NULL,
    min_interval_days INT DEFAULT 0,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine) ON DELETE CASCADE
) 

-- Registro de Aplicaciones (Lo que sucede en la clinica)
CREATE TABLE vaccination_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    vaccine_id INT,
    worker_id INT,
    applied_date DATE NOT NULL,
    dose_applied VARCHAR(50),
    lot_number VARCHAR(50),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine),
    FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
) 


DELIMITER $$

DROP PROCEDURE IF EXISTS pacientes $$
CREATE PROCEDURE pacientes(IN p_patient_id INT)
BEGIN
    SELECT
        p.patient_id AS id_paciente,
        CONCAT(p.first_name, ' ', p.last_name) AS nombre_paciente,
        p.birth_date AS fecha_nacimiento,
        GROUP_CONCAT(DISTINCT v.name ORDER BY v.name SEPARATOR ', ') AS vacunas_aplicadas,
        p.blood_type AS tipo_sangre,
        p.allergies AS alergias
    FROM patients p
    LEFT JOIN vaccination_records vr ON vr.patient_id = p.patient_id
    LEFT JOIN vaccines v ON v.id_vaccine = vr.vaccine_id
    WHERE p.patient_id = p_patient_id
    GROUP BY p.patient_id, p.first_name, p.last_name, p.birth_date, p.blood_type, p.allergies;
END $$

DELIMITER ;


DELIMITER $$

DROP PROCEDURE IF EXISTS vacunas_aplicadas_por_paciente $$
CREATE PROCEDURE vacunas_aplicadas_por_paciente(IN p_patient_id INT)
BEGIN
    WITH esquema_ordenado AS (
        SELECT
            vs.vaccine_id,
            vs.dose_number,
            vs.min_interval_days,
            ROW_NUMBER() OVER (
                PARTITION BY vs.vaccine_id
                ORDER BY vs.ideal_age_months, vs.id_scheme
            ) AS orden_dosis
        FROM vaccination_scheme vs
    ),
    resumen_vacuna AS (
        SELECT
            vr.patient_id,
            vr.vaccine_id,
            COUNT(*) AS dosis_aplicadas,
            MAX(vr.applied_date) AS fecha_ultima_aplicacion,
            SUBSTRING_INDEX(
                GROUP_CONCAT(
                    CONCAT(w.name, ' ', w.lastname)
                    ORDER BY vr.applied_date DESC
                    SEPARATOR '||'
                ),
                '||',
                1
            ) AS aplicador_ultimo,
            GROUP_CONCAT(DISTINCT CONCAT('Lote: ', COALESCE(vr.lot_number, 'N/A')) SEPARATOR '; ') AS observaciones
        FROM vaccination_records vr
        LEFT JOIN workers w ON w.worker_id = vr.worker_id
        WHERE vr.patient_id = p_patient_id
        GROUP BY vr.patient_id, vr.vaccine_id
    )
    SELECT
        rv.vaccine_id AS id_vacuna,
        v.name AS nombre_vacuna,
        rv.fecha_ultima_aplicacion AS fecha_aplicacion,
        rv.aplicador_ultimo AS nombre_aplicador,
        CASE
            WHEN eo_siguiente.vaccine_id IS NULL THEN NULL
            ELSE DATE_ADD(rv.fecha_ultima_aplicacion, INTERVAL COALESCE(eo_siguiente.min_interval_days, 0) DAY)
        END AS fecha_proxima_dosis,
        rv.observaciones
    FROM resumen_vacuna rv
    INNER JOIN vaccines v ON v.id_vaccine = rv.vaccine_id
    LEFT JOIN esquema_ordenado eo_siguiente
        ON eo_siguiente.vaccine_id = rv.vaccine_id
       AND eo_siguiente.orden_dosis = rv.dosis_aplicadas + 1
    ORDER BY v.name;
END $$

DELIMITER ;


DELIMITER $$

DROP PROCEDURE IF EXISTS proximas_citas_vacunacion $$
CREATE PROCEDURE proximas_citas_vacunacion(IN p_patient_id INT)
BEGIN
    WITH esquema_ordenado AS (
        SELECT
            vs.vaccine_id,
            vs.dose_number,
            vs.min_interval_days,
            ROW_NUMBER() OVER (
                PARTITION BY vs.vaccine_id
                ORDER BY vs.ideal_age_months, vs.id_scheme
            ) AS orden_dosis
        FROM vaccination_scheme vs
    ),
    resumen_vacuna AS (
        SELECT
            vr.patient_id,
            vr.vaccine_id,
            COUNT(*) AS dosis_aplicadas,
            MAX(vr.applied_date) AS fecha_ultima_aplicacion
        FROM vaccination_records vr
        WHERE vr.patient_id = p_patient_id
        GROUP BY vr.patient_id, vr.vaccine_id
    )
    SELECT
        p.patient_id AS id_paciente,
        CONCAT(p.first_name, ' ', p.last_name) AS nombre_paciente,
        v.id_vaccine AS id_vacuna,
        v.name AS nombre_vacuna,
        eo_siguiente.dose_number AS proxima_dosis,
        DATE_ADD(rv.fecha_ultima_aplicacion, INTERVAL COALESCE(eo_siguiente.min_interval_days, 0) DAY) AS fecha_cita,
        CASE
            WHEN DATE_ADD(rv.fecha_ultima_aplicacion, INTERVAL COALESCE(eo_siguiente.min_interval_days, 0) DAY) >= CURDATE()
                THEN 'Cita programable/existente'
            ELSE 'Sin cita vigente'
        END AS estado_cita
    FROM patients p
    INNER JOIN resumen_vacuna rv ON rv.patient_id = p.patient_id
    INNER JOIN vaccines v ON v.id_vaccine = rv.vaccine_id
    LEFT JOIN esquema_ordenado eo_siguiente
        ON eo_siguiente.vaccine_id = rv.vaccine_id
       AND eo_siguiente.orden_dosis = rv.dosis_aplicadas + 1
    WHERE p.patient_id = p_patient_id
      AND eo_siguiente.vaccine_id IS NOT NULL
      AND DATE_ADD(rv.fecha_ultima_aplicacion, INTERVAL COALESCE(eo_siguiente.min_interval_days, 0) DAY) >= CURDATE()
    ORDER BY fecha_cita;
END $$

DELIMITER ;
