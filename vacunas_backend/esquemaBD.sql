-- nombre de base de datos: vacunas

CREATE TABLE patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    blood_tipe ENUM ('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    gender ENUM ('Masculino','Femenino') NOT NULL,
    nfc_token INT UNIQUE NULL,
    allergies TEXT NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE guardian(
    guardian_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCAHR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    birth_date DATE NOT NULL,
    number INT NOT NULL,
    mail VARCHAR(100) NULL,
    address VARCHAR(200) NOT NULL,
    curp VARCHAR(18) UNIQUE,
    estado_civil VARCHAR(50),
    notes TEXT NULL
);

CREATE TABLE relations(
    relation_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT UNIQUE,
    guardian_id INT,
    FOREIGN KEY(patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY(guardian_id) REFERENCES guardian(guardian_id)
);

CREATE TABLE beacons (
    id_beacon INT AUTO_INCREMENT PRIMARY KEY,
    uuid CHAR(36) NOT NULL,
    major INT NOT NULL,
    minor INT NOT NULL,
    lugar VARCHAR(100),
    estado ENUM('Online','Offline') NOT NULL
);

CREATE TABLE radar(
    id_beacon INT,
    rssi INT, 
    latitude INT,
    longitud INT,
    FOREIGN KEY (id_beacon) REFERENCES beacons(id_becon)
);

CREATE TABLE gps(
    gps_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    patient_id INT NOT NULL,
    latitude INT UNIQUE,
    longitude INT UNIQUE,
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE vaccines (
    id_vaccine INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    inventory INT NOT NULL,
    manufacturer VARCHAR(100),
    description TEXT,
    min_age_months INT,
    max_age_months INT
);

CREATE TABLE vaccination_schedule (
    id_schedule INT AUTO_INCREMENT PRIMARY KEY,
    scheduled_day DATE NOT NULL,
    vaccine_id INT NOT NULL,
    dose_number INT NOT NULL,
    recommended_age_months INT,
    min_interval_days INT,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine)
);

CREATE TABLE workers (
  worker_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50),
  lastname VARCHAR(100),
  role ENUM('Administrador','Almacen','Enfermero'),
  mail VARCHAR(100) NOT NULL UNIQUE,
  curp VARCHAR(18),
  address VAARCHAR(250),
  birth_date DATE NOT NULL
  password_hash VARCHAR(255) NOT NULL,
  nfc_token INT UNIQUE NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    vaccine_id INT,
    worker_id INT,
    dose_number INT,
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patient(id),
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine),
    FOREIGN KEY (worker_id) REFERENCES healthcare_workers(worker_id)
);


-----------SP Dashboard

DELIMITER $$

CREATE PROCEDURE Gestion_pacientes()
BEGIN
    SELECT
        p.patient_id,
        p.first_name AS nombre_paciente,
        p.last_name AS apellido_paciente,
        g.name AS nombre_guardian,
        g.lastname AS apellido_guardian,
        TIMESTAMPDIFF(YEAR, p.birth_date, CURDATE()) AS edad,
        p.blood_tipe AS tipo_sangre,
        p.allergies AS alergias
    FROM patient p
    LEFT JOIN relations r ON r.patient_id = p.patient_id
    LEFT JOIN guardian g ON g.guardian_id = r.guardian_id;
END $$

DELIMITER ;


DELIMITER $$

CREATE PROCEDURE Inventario_vacunas()
BEGIN
    SELECT
        name AS nombre_vacuna,
        inventory AS cantidad_restante
    FROM vaccines;
END $$

DELIMITER ;


---------- SP Pacientes

