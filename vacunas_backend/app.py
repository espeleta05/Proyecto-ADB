from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from dotenv import load_dotenv
import bcrypt
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key"

# DATABASE CONFIG
db_user = os.getenv("db_user", "root")
db_password = os.getenv("db_password", "")
db_host = os.getenv("db_host", "localhost")
db_name = os.getenv("db_name", "vacunas")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MODELOS
# =========================

class Patient(db.Model):
    __tablename__ = 'patient'

    patient_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)

    blood_type = db.Column(db.Enum('A+','A-','B+','B-','AB+','AB-','O+','O-'), nullable=False)
    gender = db.Column(db.Enum('Masculino','Femenino'), nullable=False)

    nfc_token = db.Column(db.Integer, unique=True)

    allergies = db.Column(db.Text)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Guardian(db.Model):
    __tablename__ = 'guardian'

    guardian_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    lastname = db.Column(db.String(50))

    birth_date = db.Column(db.Date)

    number = db.Column(db.BigInteger)
    mail = db.Column(db.String(100))

    address = db.Column(db.String(200))

    curp = db.Column(db.String(18), unique=True)

    estado_civil = db.Column(db.String(50))

    notes = db.Column(db.Text)


class Relations(db.Model):
    __tablename__ = 'relations'

    relation_id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'))
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardian.guardian_id'))


class Beacon(db.Model):
    __tablename__ = 'beacons'

    id_beacon = db.Column(db.Integer, primary_key=True)

    uuid = db.Column(db.String(36))
    major = db.Column(db.Integer)
    minor = db.Column(db.Integer)

    lugar = db.Column(db.String(100))
    estado = db.Column(db.Enum('Online','Offline'))

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'))


class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    log_id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(db.Integer, db.ForeignKey("patient.patient_id"))

    uuid = db.Column(db.String(36))
    major = db.Column(db.Integer)
    minor = db.Column(db.Integer)

    rssi = db.Column(db.Integer)

    scanned_at = db.Column(db.DateTime)

    source_device = db.Column(db.String(30))


class Vaccine(db.Model):
    __tablename__ = 'vaccines'

    id_vaccine = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    inventory = db.Column(db.Integer)

    manufacturer = db.Column(db.String(100))

    description = db.Column(db.Text)

    min_age_months = db.Column(db.Integer)
    max_age_months = db.Column(db.Integer)


class VaccinationSchedule(db.Model):
    __tablename__ = 'vaccination_schedule'

    id_schedule = db.Column(db.Integer, primary_key=True)

    scheduled_day = db.Column(db.Date)

    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))

    dose_number = db.Column(db.Integer)

    recommended_age_months = db.Column(db.Integer)

    min_interval_days = db.Column(db.Integer)


class Worker(db.Model):
    __tablename__ = 'workers'

    worker_id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50))
    lastname = db.Column(db.String(100))
    role = db.Column(db.Enum('Administrador','Almacen','Enfermero'))
    mail = db.Column(db.String(100), unique=True)
    curp = db.Column(db.String(18))
    address = db.Column(db.String(250))
    birth_date = db.Column(db.Date)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Vaccination(db.Model):
    __tablename__ = "vaccinations"

    vaccination_id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'))

    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))

    dose_number = db.Column(db.Integer)

    applied_date = db.Column(db.Date)

    worker_id = db.Column(db.Integer, db.ForeignKey("workers.worker_id"))

# =========================
# RUTA PRINCIPAL
# =========================

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        mail = request.form.get("mail")
        password = request.form.get("password")

        worker = Worker.query.filter_by(mail=mail).first()

        if worker:

            if bcrypt.checkpw(
                password.encode("utf-8"),
                worker.password_hash.encode("utf-8")
            ):

                session["user_id"] = worker.worker_id
                session["user_name"] = worker.name
                session["user_lastname"] = worker.lastname
                session["user_mail"] = worker.mail
                session["role"] = worker.role
                

                return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Credenciales incorrectas"
        )

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    today = datetime.now().strftime("%A, %d de %B, %Y")

    if "user_mail" not in session:
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        name=session["user_name"],
        lastname=session["user_lastname"],
        role=session["role"],
        today = today
    )

@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/pacientes")
def pacientes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "pacientes.html",
        name=session["user_name"],
        lastname=session["user_lastname"],
        role=session["role"]
    )

# =========================
# REGISTRAR PACIENTE
# =========================

@app.route("/register_patient", methods=["POST"])
def register_patient():

    data = request.json

    birth = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()

    new_patient = Patient(
        first_name=data["first_name"],
        last_name=data["last_name"],
        birth_date=birth,
        blood_type=data.get("blood_type", "O+"),
        gender=data["gender"],
        nfc_token=data.get("nfc_token"),
        allergies=data.get("allergies"),
        notes=data.get("notes")
    )

    db.session.add(new_patient)
    db.session.commit()

    return jsonify({
        "message": "Paciente registrado",
        "patient_id": new_patient.patient_id
    })


# =========================
# REGISTRAR BEACON
# =========================

@app.route("/register_beacon", methods=["POST"])
def register_beacon():

    data = request.json

    beacon = Beacon(
        uuid=data["uuid"],
        major=data["major"],
        minor=data["minor"],
        lugar=data.get("lugar"),
        estado=data.get("estado","Online"),
        patient_id=data["patient_id"]
    )

    db.session.add(beacon)
    db.session.commit()

    return jsonify({"message":"Beacon registrado"})


# =========================
# ESCANEO DE BEACON
# =========================

@app.route("/scan", methods=["POST"])
def scan():

    data = request.json

    beacon = Beacon.query.filter_by(
        uuid=data["uuid"],
        major=data["major"],
        minor=data["minor"]
    ).first()

    if not beacon:
        return jsonify({"error":"Beacon no encontrado"}),404

    patient = db.session.get(Patient, beacon.patient_id)

    if not patient:
        return jsonify({"error":"Paciente no encontrado"}),404

    log = ScanLog(
        patient_id=patient.patient_id,
        uuid=data["uuid"],
        major=data["major"],
        minor=data["minor"],
        rssi=data.get("rssi"),
        scanned_at=datetime.now(),
        source_device=data.get("source_device","unknown")
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({
        "patient_id": patient.patient_id,
        "name": patient.first_name,
        "last_name": patient.last_name
    })


# =========================
# LOGIN WORKER
# =========================

@app.route("/worker_login", methods=["POST"])
def worker_login():

    data = request.json

    worker = Worker.query.filter_by(mail=data["mail"]).first()

    if not worker:
        return jsonify({"error":"Credenciales incorrectas"}),401

    ok = bcrypt.checkpw(
        data["password"].encode("utf-8"),
        worker.password_hash.encode("utf-8")
    )

    if not ok:
        return jsonify({"error":"Credenciales incorrectas"}),401

    return jsonify({
        "message":"Login exitoso",
        "worker_id": worker.worker_id,
        "name": worker.name,
        "lastname": worker.lastname,
        "role": worker.role
    })


# =========================
# OBTENER VACUNAS
# =========================

@app.route("/vaccines", methods=["GET"])
def get_vaccines():

    vaccines = Vaccine.query.all()

    result = []

    for v in vaccines:

        result.append({
            "id": v.id_vaccine,
            "name": v.name,
            "inventory": v.inventory,
            "manufacturer": v.manufacturer,
            "description": v.description
        })

    return jsonify(result)


# =========================
# HISTORIAL DE VACUNAS
# =========================

@app.route("/patient_history/<int:patient_id>")
def patient_history(patient_id):

    vaccinations = Vaccination.query.filter_by(
        patient_id=patient_id
    ).order_by(
        Vaccination.applied_date.desc()
    ).all()

    result = []

    for v in vaccinations:

        vaccine = db.session.get(Vaccine, v.vaccine_id)

        result.append({
            "vaccine": vaccine.name,
            "dose": v.dose_number,
            "date": str(v.applied_date)
        })

    return jsonify(result)


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
