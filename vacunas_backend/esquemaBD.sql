-- nombre de base de datos: vacunas

CREATE TABLE children (
    id CHAR(36) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE beacons (
    id_beacon INT AUTO_INCREMENT PRIMARY KEY,
    uuid CHAR(36) NOT NULL,
    major INT NOT NULL,
    minor INT NOT NULL,
    child_id CHAR(36) UNIQUE,
    FOREIGN KEY (child_id) REFERENCES children(id)
);
-- Un beacon pertenece a un niño
-- Un niño tiene un beacon

CREATE TABLE vaccines (
    id_vaccine INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    description TEXT,
    min_age_months INT,
    max_age_months INT
);

CREATE TABLE vaccination_schedule (
    id_schedule INT AUTO_INCREMENT PRIMARY KEY,
    vaccine_id INT,
    dose_number INT,
    recommended_age_months INT,
    min_interval_days INT,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine)
);

CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id CHAR(36),
    vaccine_id INT,
    worker_id INT,
    dose_number INT,
    application_date DATE,
    responsible_user VARCHAR(100),
    FOREIGN KEY (child_id) REFERENCES children(id),
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine),
    FOREIGN KEY (worker_id) REFERENCES healthcare_workers(worker_id)
);

CREATE TABLE healthcare_workers (
  worker_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  full_name VARCHAR(120) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scan_logs (
  log_id INT AUTO_INCREMENT PRIMARY KEY,
  child_id CHAR(36) NOT NULL,
  uuid VARCHAR(36) NOT NULL,
  major INT NOT NULL,
  minor INT NOT NULL,
  rssi INT NULL,
  scanned_at DATETIME NOT NULL,
  source_device VARCHAR(30) NULL,
  FOREIGN KEY (child_id) REFERENCES children(id)
);

-- resumen 
CREATE OR REPLACE VIEW v_child_vaccination_summary AS
SELECT
  c.id AS child_id,
  c.first_name,
  c.last_name,
  v.id_vaccine AS vaccine_id,
  v.name AS vaccine_name,
  COUNT(vc.vaccination_id) AS applied_doses,
  MAX(vc.applied_date) AS last_applied_date
FROM children c
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
