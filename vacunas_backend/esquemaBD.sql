-- nombre de base de datos: vacunas

CREATE TABLE patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    blood_tipe ENUM ('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    gender ENUM ('Masculino','Femenino') NOT NULL,
    nfc_token INT UNIQUE NULL,
    notes TEXT NULL
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
  name VARCHAR(50) NOT NULL,
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


-- resumen 
CREATE OR REPLACE VIEW v_child_vaccination_summary AS
SELECT
  c.id AS patient_id,
  c.first_name,
  c.last_name,
  v.id_vaccine AS vaccine_id,
  v.name AS vaccine_name,
  COUNT(vc.vaccination_id) AS applied_doses,
  MAX(vc.applied_date) AS last_applied_date
FROM patient c
CROSS JOIN vaccines v
LEFT JOIN vaccinations vc
  ON vc.child_id = c.id AND vc.vaccine_id = v.id_vaccine
GROUP BY
  c.id, c.first_name, c.last_name,
  v.id_vaccine, v.name;

-- SP para validaciones clínicas 
DELIMITER //

CREATE PROCEDURE validate_vaccine(
    IN p_child CHAR(36),
    IN p_vaccine INT,
    IN p_dose INT
)
BEGIN
    DECLARE last_date DATE;
    DECLARE min_interval INT;

    SELECT application_date INTO last_date
    FROM applications
    WHERE child_id = p_child
    AND vaccine_id = p_vaccine
    AND dose_number = p_dose - 1;

    SELECT min_interval_days INTO min_interval
    FROM official_schedule
    WHERE vaccine_id = p_vaccine
    AND dose_number = p_dose;

    IF last_date IS NOT NULL THEN
        IF DATEDIFF(CURDATE(), last_date) < min_interval THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Intervalo insuficiente';
        END IF;
    END IF;
END //

DELIMITER ;
