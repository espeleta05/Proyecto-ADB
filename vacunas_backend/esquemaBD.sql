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

-- Relación Paciente-Tutor (Muchos a Muchos)
CREATE TABLE relations (
    relation_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    guardian_id INT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (guardian_id) REFERENCES guardians(guardian_id) ON DELETE CASCADE
) 

-- Esquema Oficial de Vacunación
CREATE TABLE vaccination_scheme (
    id_scheme INT AUTO_INCREMENT PRIMARY KEY,
    vaccine_id INT,
    dose_number VARCHAR(50) NOT NULL,
    ideal_age_months INT NOT NULL,
    min_interval_days INT DEFAULT 0,
    FOREIGN KEY (vaccine_id) REFERENCES vaccines(id_vaccine) ON DELETE CASCADE
) 

-- Registro de Aplicaciones (Lo que sucede en la clínica)
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
