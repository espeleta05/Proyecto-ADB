from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from dotenv import load_dotenv
from sqlalchemy import or_
import bcrypt
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = "super_secret_key"

# DATABASE CONFIG
db_user = os.getenv("db_user", "root")
db_password = os.getenv("db_password", "")
db_host = os.getenv("db_host", "localhost")
db_name = os.getenv("db_name", "vacunas")
db_driver = os.getenv("db_driver", "mysqlconnector")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+{db_driver}://{db_user}:{db_password}@{db_host}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, hashed):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )


def _age_in_years(birth_date):
    today = date.today()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(years, 0)


def ensure_default_admin():
    admin = Worker.query.filter(
        or_(Worker.mail == "admin", Worker.name == "admin")
    ).first()

    password_hash = bcrypt.hashpw("123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    if admin:
        admin.name = "admin"
        admin.mail = "admin"
        admin.role = "Administrador"
        admin.password_hash = password_hash
        db.session.commit()
        return

    admin_user = Worker(
        name="admin",
        lastname="system",
        role="Administrador",
        mail="admin",
        password_hash=password_hash,
        birth_date=date(2000, 1, 1)
    )

    db.session.add(admin_user)
    db.session.commit()

# =========================
# MODELOS
# =========================

class Patient(db.Model):
    __tablename__ = 'patients'

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
    __tablename__ = 'guardians'

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

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.guardian_id'))


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

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )


class Vaccine(db.Model):
    __tablename__ = 'vaccines'
    id_vaccine = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    inventory = db.Column(db.Integer)
    manufacturer = db.Column(db.String(100))
    description = db.Column(db.Text)

class VaccinationScheme(db.Model):
    __tablename__ = 'vaccination_scheme'
    id_scheme = db.Column(db.Integer, primary_key=True)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    dose_number = db.Column(db.String(50), nullable=False)
    ideal_age_months = db.Column(db.Integer, nullable=False)
    min_interval_days = db.Column(db.Integer)


class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_records'
    record_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.worker_id')) 
    applied_date = db.Column(db.Date, nullable=False, default=date.today)
    dose_applied = db.Column(db.String(20))
    lot_number = db.Column(db.String(50))
    clinic_location = db.Column(db.String(100))

# =========================
# RUTA PRINCIPAL
# =========================

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        identifier = request.form.get("mail", "").strip()
        password = request.form.get("password")

        worker = Worker.query.filter(
            or_(Worker.mail == identifier, Worker.name == identifier)
        ).first()

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

    total_patients = Patient.query.count()
    total_vaccines = Vaccine.query.count()
    applications_today = VaccinationRecord.query.filter_by(applied_date=date.today()).count()

    top_patients = []
    patient_rows = db.session.query(Patient, Guardian).outerjoin(
        Relations, Relations.patient_id == Patient.patient_id
    ).outerjoin(
        Guardian, Guardian.guardian_id == Relations.guardian_id
    ).order_by(Patient.created_at.desc()).limit(5).all()

    for patient, guardian in patient_rows:
        top_patients.append({
            "patient_id": patient.patient_id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "guardian": f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor",
            "age": _age_in_years(patient.birth_date),
            "blood_type": patient.blood_type,
            "allergies": patient.allergies or "Ninguna"
        })

    dashboard_vaccines = Vaccine.query.order_by(Vaccine.inventory.asc()).limit(4).all()

    return render_template(
        "index.html",
        name=session["user_name"],
        lastname=session["user_lastname"],
        role=session["role"],
        today=today,
        total_patients=total_patients,
        total_vaccines=total_vaccines,
        applications_today=applications_today,
        top_patients=top_patients,
        dashboard_vaccines=dashboard_vaccines
    )

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))

@app.route("/pacientes")
def pacientes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    patient_rows = db.session.query(Patient, Guardian).outerjoin(
        Relations, Relations.patient_id == Patient.patient_id
    ).outerjoin(
        Guardian, Guardian.guardian_id == Relations.guardian_id
    ).order_by(Patient.created_at.desc()).all()

    patients_data = []
    for patient, guardian in patient_rows:
        patients_data.append({
            "patient_id": patient.patient_id,
            "full_name": f"{patient.first_name} {patient.last_name}",
            "birth_date": patient.birth_date.strftime("%d/%m/%Y"),
            "guardian": f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor",
            "contact": str(guardian.number) if guardian and guardian.number else "Sin teléfono",
            "blood_type": patient.blood_type,
            "allergies": patient.allergies or "Ninguna",
            "risk": "bajo"
        })

    return render_template(
        "pacientes.html",
        name=session["user_name"],
        lastname=session["user_lastname"],
        role=session["role"],
        patients=patients_data,
        total_patients=len(patients_data)
    )


@app.route("/vacunas")
def vacunas_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    vaccines = Vaccine.query.order_by(Vaccine.name.asc()).all()

    return render_template(
        "vacunas.html",
        name=session["user_name"],
        lastname=session["user_lastname"],
        role=session["role"],
        vaccines=vaccines,
        total_vaccines=len(vaccines)
    )

@app.route('/esquema')
def esquema_vacunacion():
    # Verificamos si hay sesión (opcional, según tu sistema)
    if 'user_id' not in session:
        return redirect(url_for('login'))

    esquema_data = db.session.query(VaccinationScheme, Vaccine).join(
        Vaccine, VaccinationScheme.vaccine_id == Vaccine.id_vaccine
    ).order_by(VaccinationScheme.ideal_age_months).all()

    return render_template(
        'esquemaVacunacion.html', 
        esquema=esquema_data,
        name=session.get('name', 'Usuario'),
        lastname=session.get('lastname', ''),
        role=session.get('role', 'Personal')
    )

# =========================
# REGISTRAR PACIENTE
# =========================

@app.route("/register_patient", methods=["POST"])
def register_patient():

    data = request.json or {}

    required = ["first_name", "last_name", "birth_date", "gender"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Faltan campos obligatorios: {', '.join(missing)}"}), 400

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


@app.route("/register_vaccine", methods=["POST"])
def register_vaccine():

    data = request.json or {}

    if not data.get("name"):
        return jsonify({"error": "El nombre de la vacuna es obligatorio"}), 400

    try:
        inventory = int(data.get("inventory", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "El inventario debe ser un numero entero"}), 400

    min_age_months = data.get("min_age_months")
    max_age_months = data.get("max_age_months")

    if min_age_months in ("", None):
        min_age_months = None
    else:
        try:
            min_age_months = int(min_age_months)
        except (TypeError, ValueError):
            return jsonify({"error": "Edad minima invalida"}), 400

    if max_age_months in ("", None):
        max_age_months = None
    else:
        try:
            max_age_months = int(max_age_months)
        except (TypeError, ValueError):
            return jsonify({"error": "Edad maxima invalida"}), 400

    vaccine = Vaccine(
        name=data["name"].strip(),
        inventory=inventory,
        manufacturer=(data.get("manufacturer") or "").strip() or None,
        description=(data.get("description") or "").strip() or None,
        min_age_months=min_age_months,
        max_age_months=max_age_months
    )

    db.session.add(vaccine)
    db.session.commit()

    return jsonify({
        "message": "Vacuna registrada",
        "vaccine_id": vaccine.id_vaccine
    })

@app.route("/register_worker", methods=["POST"])
def register_worker():

    data = request.json

    hashed_password = hash_password(data["password"])

    new_worker = Worker(
        name=data["name"],
        lastname=data["lastname"],
        role=data["role"],
        mail=data["mail"],
        curp=data.get("curp"),
        address=data.get("address"),
        birth_date=datetime.strptime(data["birth_date"], "%Y-%m-%d"),
        password_hash=hashed_password
    )

    db.session.add(new_worker)
    db.session.commit()

    return jsonify({"message": "Usuario creado"})


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
        "first_name": patient.first_name,
        "name": patient.first_name,
        "last_name": patient.last_name,
        "birth_date": str(patient.birth_date)
    })


def _age_in_months(birth_date):
    today = date.today()
    months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
    if today.day < birth_date.day:
        months -= 1
    return max(months, 0)


@app.route("/patient_history/<int:patient_id>")
def patient_history(patient_id):

    vaccinations = VaccinationRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(
        VaccinationRecord.applied_date.desc()
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


@app.route("/check_schedule/<int:patient_id>", methods=["GET"])
def check_schedule(patient_id):

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"error": "Paciente no encontrado"}), 404

    schedules = VaccinationSchedule.query.order_by(
        VaccinationSchedule.vaccine_id.asc(),
        VaccinationSchedule.dose_number.asc()
    ).all()

    schedule_by_vaccine = {}
    for sch in schedules:
        schedule_by_vaccine.setdefault(sch.vaccine_id, []).append(sch)

    alerts = []
    for vaccine_id, vaccine_schedule in schedule_by_vaccine.items():
        vaccine = db.session.get(Vaccine, vaccine_id)
        if not vaccine:
            continue

        applied = Vaccination.query.filter_by(
            patient_id=patient_id,
            vaccine_id=vaccine_id
        ).order_by(Vaccination.dose_number.asc()).all()

        applied_numbers = {v.dose_number for v in applied}
        required_numbers = [s.dose_number for s in vaccine_schedule]
        missing_numbers = [n for n in required_numbers if n not in applied_numbers]

        if missing_numbers:
            alerts.append({
                "vaccine_id": vaccine_id,
                "vaccine": vaccine.name,
                "required_doses": len(required_numbers),
                "applied_doses": len(applied),
                "missing_doses": len(missing_numbers),
                "missing_dose_numbers": missing_numbers
            })

    return jsonify({
        "patient_id": patient_id,
        "alerts": alerts
    })


@app.route("/apply_vaccine", methods=["POST"])
def apply_vaccine():

    data = request.json or {}
    patient_id = data.get("patient_id")
    vaccine_id = data.get("vaccine_id")
    worker_id = data.get("worker_id") or session.get("user_id")

    if not patient_id or not vaccine_id:
        return jsonify({"error": "patient_id y vaccine_id son obligatorios"}), 400

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"error": "Paciente no encontrado"}), 404

    vaccine = db.session.get(Vaccine, vaccine_id)
    if not vaccine:
        return jsonify({"error": "Vacuna no encontrada"}), 404

    if vaccine.inventory is not None and vaccine.inventory <= 0:
        return jsonify({"error": "No hay inventario disponible"}), 400

    applied = Vaccination.query.filter_by(
        patient_id=patient_id,
        vaccine_id=vaccine_id
    ).order_by(Vaccination.dose_number.asc()).all()

    next_dose = len(applied) + 1

    schedule = VaccinationSchedule.query.filter_by(
        vaccine_id=vaccine_id,
        dose_number=next_dose
    ).first()

    if not schedule:
        return jsonify({"error": "No hay dosis pendiente para esta vacuna"}), 400

    age_months = _age_in_months(patient.birth_date)
    if vaccine.min_age_months is not None and age_months < vaccine.min_age_months:
        return jsonify({"error": "Paciente fuera del rango mínimo de edad"}), 400

    if vaccine.max_age_months is not None and age_months > vaccine.max_age_months:
        return jsonify({"error": "Paciente fuera del rango máximo de edad"}), 400

    if applied:
        last_dose = applied[-1]
        if schedule.min_interval_days:
            days_since_last = (date.today() - last_dose.applied_date).days
            if days_since_last < schedule.min_interval_days:
                return jsonify({
                    "error": f"Aún no se cumple el intervalo mínimo de {schedule.min_interval_days} días"
                }), 400

    if vaccine.inventory is not None:
        vaccine.inventory -= 1

    new_vaccination = Vaccination(
        patient_id=patient_id,
        vaccine_id=vaccine_id,
        dose_number=next_dose,
        applied_date=date.today(),
        worker_id=worker_id
    )

    db.session.add(new_vaccination)
    db.session.commit()

    return jsonify({
        "message": "Vacuna aplicada correctamente",
        "vaccination_id": new_vaccination.vaccination_id,
        "dose_number": next_dose,
        "inventory_left": vaccine.inventory
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
        ensure_default_admin()

    app.run(host="0.0.0.0", port=5000, debug=True)
