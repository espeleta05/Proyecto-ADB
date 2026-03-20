from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from sqlalchemy import or_
import bcrypt
import os
from urllib.parse import quote_plus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cambia_esto_en_produccion_12345")

# DATABASE CONFIG
db_user     = os.getenv("db_user", "postgres")
db_password = os.getenv("db_password", "")
db_host     = os.getenv("db_host", "localhost")
db_port     = os.getenv("db_port", "5432")
db_name     = os.getenv("db_name", "vacunas")
database_url = os.getenv("DATABASE_URL")

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql+psycopg://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
    )

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


def _age_in_months(birth_date):
    today = date.today()
    months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
    if today.day < birth_date.day:
        months -= 1
    return max(months, 0)


def ensure_default_admin():
    admin = Worker.query.filter(
        or_(Worker.mail == "admin", Worker.name == "admin")
    ).first()

    # Si ya existe, no tocar nada (no sobreescribir el password)
    if admin:
        return

    # Solo crear si no existe
    admin_user = Worker(
        name="admin",
        lastname="system",
        role="Administrador",
        mail="admin",
        password_hash=bcrypt.hashpw("123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
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
    last_name  = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    blood_type = db.Column(db.String(3), nullable=False)
    gender     = db.Column(db.String(10), nullable=False)
    nfc_token  = db.Column(db.String(50), unique=True)
    allergies  = db.Column(db.Text)
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def birth_date_fmt(self):
        return self.birth_date.strftime('%d/%m/%Y') if self.birth_date else "N/A"


class Guardian(db.Model):
    __tablename__ = 'guardians'

    guardian_id  = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(50))
    lastname     = db.Column(db.String(50))
    birth_date   = db.Column(db.Date)
    number       = db.Column(db.BigInteger)
    mail         = db.Column(db.String(100))
    address      = db.Column(db.String(200))
    curp         = db.Column(db.String(18), unique=True)
    estado_civil = db.Column(db.String(50))
    notes        = db.Column(db.Text)


class Relations(db.Model):
    __tablename__ = 'relations'

    relation_id = db.Column(db.Integer, primary_key=True)
    patient_id  = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.guardian_id'))


class Worker(db.Model):
    __tablename__ = 'workers'

    worker_id     = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(50))
    lastname      = db.Column(db.String(100))
    role          = db.Column(db.String(20))
    mail          = db.Column(db.String(100), unique=True)
    curp          = db.Column(db.String(18))
    address       = db.Column(db.String(250))
    birth_date    = db.Column(db.Date)
    password_hash = db.Column(db.String(255))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

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


class Beacon(db.Model):
    __tablename__ = 'beacons'

    id_beacon  = db.Column(db.Integer, primary_key=True)
    uuid       = db.Column(db.String(36))
    major      = db.Column(db.Integer)
    minor      = db.Column(db.Integer)
    lugar      = db.Column(db.String(100))
    estado     = db.Column(db.String(10))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))


class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    log_id        = db.Column(db.Integer, primary_key=True)
    patient_id    = db.Column(db.Integer, db.ForeignKey("patients.patient_id"))
    uuid          = db.Column(db.String(36))
    major         = db.Column(db.Integer)
    minor         = db.Column(db.Integer)
    rssi          = db.Column(db.Integer)
    scanned_at    = db.Column(db.DateTime)
    source_device = db.Column(db.String(30))


class Vaccine(db.Model):
    __tablename__ = 'vaccines'

    id_vaccine      = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100))
    inventory       = db.Column(db.Integer)
    manufacturer    = db.Column(db.String(100))
    description     = db.Column(db.Text)
    min_age_months  = db.Column(db.Integer)
    max_age_months  = db.Column(db.Integer)


class VaccinationScheme(db.Model):
    __tablename__ = 'vaccination_scheme'

    id_scheme        = db.Column(db.Integer, primary_key=True)
    vaccine_id       = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    dose_number      = db.Column(db.String(50), nullable=False)
    ideal_age_months = db.Column(db.Integer, nullable=False)
    min_interval_days = db.Column(db.Integer)


class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_records'

    record_id       = db.Column(db.Integer, primary_key=True)
    patient_id      = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))
    vaccine_id      = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    worker_id       = db.Column(db.Integer, db.ForeignKey('workers.worker_id'))
    applied_date    = db.Column(db.Date, nullable=False, default=date.today)
    dose_applied    = db.Column(db.String(20))
    lot_number      = db.Column(db.String(50))
    clinic_location = db.Column(db.String(100))

    vaccine = db.relationship('Vaccine')
    worker  = db.relationship('Worker')


# =========================
# RUTA PRINCIPAL
# =========================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("mail", "").strip()
        password   = request.form.get("password")

        worker = Worker.query.filter(
            or_(Worker.mail == identifier, Worker.name == identifier)
        ).first()

        if worker and worker.check_password(password):
            session["user_id"]       = worker.worker_id
            session["user_name"]     = worker.name
            session["user_lastname"] = worker.lastname
            session["user_mail"]     = worker.mail
            session["role"]          = worker.role
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_mail" not in session:
        return redirect(url_for("login"))

    today = datetime.now().strftime("%A, %d de %B, %Y")

    total_patients      = Patient.query.count()
    total_vaccines      = Vaccine.query.count()
    applications_today  = VaccinationRecord.query.filter_by(applied_date=date.today()).count()

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
            "last_name":  patient.last_name,
            "guardian":   f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor",
            "age":        _age_in_years(patient.birth_date),
            "blood_type": patient.blood_type,
            "allergies":  patient.allergies or "Ninguna"
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
            "full_name":  f"{patient.first_name} {patient.last_name}",
            "birth_date": patient.birth_date.strftime("%d/%m/%Y"),
            "guardian":   f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor",
            "contact":    str(guardian.number) if guardian and guardian.number else "Sin teléfono",
            "blood_type": patient.blood_type,
            "allergies":  patient.allergies or "Ninguna",
            "risk":       "bajo"
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
    if 'user_id' not in session:
        return redirect(url_for('login'))

    esquema_data = db.session.query(VaccinationScheme, Vaccine).join(
        Vaccine, VaccinationScheme.vaccine_id == Vaccine.id_vaccine
    ).order_by(VaccinationScheme.ideal_age_months).all()

    return render_template(
        'esquemaVacunacion.html',
        esquema=esquema_data,
        name=session.get('user_name', 'Usuario'),
        lastname=session.get('user_lastname', ''),
        role=session.get('role', 'Personal')
    )


@app.route('/historial')
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    patients = Patient.query.all()

    return render_template(
        'historial.html',
        patients=patients,
        patient=None,
        applications=[],
        next_vaccines=[]
    )

def _load_patient_data(id):
    """Carga datos del paciente, historial y proximas citas usando funciones SQL."""
    from flask import abort
    from sqlalchemy import text
 
    patient = db.session.get(Patient, id)
    if patient is None:
        abort(404)
 
    relation = Relations.query.filter_by(patient_id=id).first()
    guardian = None
    if relation:
        guardian = db.session.get(Guardian, relation.guardian_id)
 
    patient.full_name = f"{patient.first_name} {patient.last_name}"
    patient.guardian  = f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor"
    patient.contact   = str(guardian.number) if guardian and guardian.number else "Sin teléfono"
    patient.allergies = patient.allergies or "Ninguna"
    patient.age       = _age_in_years(patient.birth_date)
    patient.risk      = "bajo"
 
    # ── Historial usando vacunas_aplicadas_por_paciente() ──
    rows = db.session.execute(
        text("SELECT * FROM vacunas_aplicadas_por_paciente(CAST(:pid AS INT))"),
        {"pid": id}
    ).fetchall()
 
    applications = []
    for r in rows:
        applications.append({
            "name":      r.nombre_vacuna,
            "id":        r.id_vacuna,
            "dose":      r.fecha_aplicacion.strftime('%d/%m/%Y') if r.fecha_aplicacion else "N/A",
            "date":      r.fecha_aplicacion.strftime('%d/%m/%Y') if r.fecha_aplicacion else "N/A",
            "doctor":    r.nombre_aplicador or "N/A",
            "next_date": r.fecha_proxima_dosis.strftime('%d/%m/%Y') if r.fecha_proxima_dosis else None,
            "notes":     r.observaciones or "Aplicación registrada"
        })
 
    # ── Próximas citas usando proximas_citas_vacunacion() ──
    citas = db.session.execute(
        text("SELECT * FROM proximas_citas_vacunacion(CAST(:pid AS INT))"),
        {"pid": id}
    ).fetchall()
 
    next_vaccines = []
    for c in citas:
        next_vaccines.append({
            "name":   c.nombre_vacuna,
            "dose":   c.proxima_dosis,
            "date":   c.fecha_cita.strftime('%d/%m/%Y') if c.fecha_cita else "N/A",
            "estado": c.estado_cita
        })
 
    return patient, applications, next_vaccines

@app.route('/historial/<int:id>')
def historial_paciente(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    patients = Patient.query.all()
    patient, applications, next_vaccines = _load_patient_data(id)

    return render_template(
        'historial.html',
        patients=patients,
        patient=patient,
        applications=applications,
        next_vaccines=next_vaccines
    )

@app.route('/aplicaciones')
def aplicaciones():
    if 'user_id' not in session:
        return redirect(url_for('login'))
 
    # Todos los registros de vacunación con joins a vacuna, worker y paciente
    records = db.session.query(VaccinationRecord, Vaccine, Worker, Patient).join(
        Vaccine, VaccinationRecord.vaccine_id == Vaccine.id_vaccine
    ).outerjoin(
        Worker, VaccinationRecord.worker_id == Worker.worker_id
    ).join(
        Patient, VaccinationRecord.patient_id == Patient.patient_id
    ).order_by(
        VaccinationRecord.applied_date.desc(),
        VaccinationRecord.record_id.desc()
    ).all()
 
    applications = []
    for record, vaccine, worker, patient in records:
        # Calcular próxima dosis según el esquema
        next_scheme = VaccinationScheme.query.filter_by(
            vaccine_id=record.vaccine_id
        ).order_by(
            VaccinationScheme.ideal_age_months.asc(),
            VaccinationScheme.id_scheme.asc()
        ).all()
 
        applied_count = VaccinationRecord.query.filter_by(
            patient_id=record.patient_id,
            vaccine_id=record.vaccine_id
        ).count()
 
        next_date = None
        if applied_count < len(next_scheme):
            next_scheme_entry = next_scheme[applied_count]
            if next_scheme_entry.min_interval_days:
                next_date = (record.applied_date + timedelta(days=next_scheme_entry.min_interval_days)).strftime('%d/%m/%Y')
 
        doctor_name = f"Dr. {worker.name} {worker.lastname}" if worker else "N/A"
 
        applications.append({
            "id":           record.record_id,
            "name":         vaccine.name,
            "id_vaccine":   record.vaccine_id,
            "dose":         record.dose_applied or "N/A",
            "date":         record.applied_date.strftime('%d/%m/%Y') if record.applied_date else "N/A",
            "doctor":       doctor_name,
            "next_date":    next_date,
            "notes":        record.lot_number or None,
            "patient_id":   record.patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "N/A",
        })
 
    # Stats
    today_count        = VaccinationRecord.query.filter_by(applied_date=date.today()).count()
    unique_patients    = db.session.query(VaccinationRecord.patient_id).distinct().count()
    unique_vaccines    = db.session.query(VaccinationRecord.vaccine_id).distinct().count()
 
    return render_template(
        'aplicaciones.html',
        applications=applications,
        total_applications=len(applications),
        total_patients_attended=unique_patients,
        total_unique_vaccines=unique_vaccines,
        applications_today=today_count,
        name=session.get('user_name', ''),
        lastname=session.get('user_lastname', ''),
        role=session.get('role', '')
    )

@app.route('/mapa-riesgo')
def mapa_riesgo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
 
    from sqlalchemy import func
 
    zone_rows = db.session.query(
        VaccinationRecord.clinic_location,
        func.count(VaccinationRecord.record_id).label('cases')
    ).filter(
        VaccinationRecord.clinic_location.isnot(None)
    ).group_by(
        VaccinationRecord.clinic_location
    ).order_by(
        func.count(VaccinationRecord.record_id).desc()
    ).all()
 
    zones = []
    high_risk_count   = 0
    medium_risk_count = 0
    low_risk_count    = 0
 
    for row in zone_rows:
        cases = row.cases
        if cases >= 10:
            risk = 'high'
            high_risk_count += 1
        elif cases >= 4:
            risk = 'medium'
            medium_risk_count += 1
        else:
            risk = 'low'
            low_risk_count += 1
 
        zones.append({
            'name':  row.clinic_location,
            'cases': cases,
            'risk':  risk
        })
 
    return render_template(
        'mapaRiesgo.html',
        zones=zones,
        high_risk_count=high_risk_count,
        medium_risk_count=medium_risk_count,
        low_risk_count=low_risk_count,
        name=session.get('user_name', ''),
        lastname=session.get('user_lastname', ''),
        role=session.get('role', '')
    )
 
@app.route('/personal')
def personal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
 
    workers = Worker.query.order_by(Worker.role.asc(), Worker.name.asc()).all()
 
    workers_data = []
    for w in workers:
        workers_data.append({
            'worker_id': w.worker_id,
            'name':      w.name,
            'lastname':  w.lastname or '',
            'role':      w.role or 'Sin rol',
            'mail':      w.mail,
        })
 
    return render_template(
        'personal.html',
        workers=workers_data,
        total_workers=len(workers_data),
        name=session.get('user_name', ''),
        lastname=session.get('user_lastname', ''),
        role=session.get('role', '')
    )

# =========================
# REGISTRAR PACIENTE
# =========================

@app.route("/register_patient", methods=["POST"])
def register_patient():
    data = request.json or {}

    required = ["first_name", "last_name", "birth_date", "gender"]
    missing  = [f for f in required if not data.get(f)]
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

    return jsonify({"message": "Paciente registrado", "patient_id": new_patient.patient_id})


# =========================
# REGISTRAR VACUNA
# =========================

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
        name=(data["name"].strip()),
        inventory=inventory,
        manufacturer=(data.get("manufacturer") or "").strip() or None,
        description=(data.get("description") or "").strip() or None,
        min_age_months=min_age_months,
        max_age_months=max_age_months
    )

    db.session.add(vaccine)
    db.session.commit()

    return jsonify({"message": "Vacuna registrada", "vaccine_id": vaccine.id_vaccine})


# =========================
# REGISTRAR WORKER
# =========================

@app.route("/register_worker", methods=["POST"])
def register_worker():
    data = request.json or {}

    new_worker = Worker(
        name=data["name"],
        lastname=data["lastname"],
        role=data["role"],
        mail=data["mail"],
        curp=data.get("curp"),
        address=data.get("address"),
        birth_date=datetime.strptime(data["birth_date"], "%Y-%m-%d").date(),
        password_hash=hash_password(data["password"])
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
        estado=data.get("estado", "Online"),
        patient_id=data["patient_id"]
    )

    db.session.add(beacon)
    db.session.commit()

    return jsonify({"message": "Beacon registrado"})


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
        return jsonify({"error": "Beacon no encontrado"}), 404

    patient = db.session.get(Patient, beacon.patient_id)
    if not patient:
        return jsonify({"error": "Paciente no encontrado"}), 404

    log = ScanLog(
        patient_id=patient.patient_id,
        uuid=data["uuid"],
        major=data["major"],
        minor=data["minor"],
        rssi=data.get("rssi"),
        scanned_at=datetime.now(),
        source_device=data.get("source_device", "unknown")
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({
        "patient_id": patient.patient_id,
        "first_name": patient.first_name,
        "name":       patient.first_name,
        "last_name":  patient.last_name,
        "birth_date": str(patient.birth_date)
    })


# =========================
# APLICAR VACUNA
# =========================

@app.route("/apply_vaccine", methods=["POST"])
def apply_vaccine():
    data       = request.json or {}
    patient_id = data.get("patient_id")
    vaccine_id = data.get("vaccine_id")
    worker_id  = data.get("worker_id") or session.get("user_id")

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

    applied = VaccinationRecord.query.filter_by(
        patient_id=patient_id,
        vaccine_id=vaccine_id
    ).order_by(
        VaccinationRecord.applied_date.asc(),
        VaccinationRecord.record_id.asc()
    ).all()

    schedules = VaccinationScheme.query.filter_by(vaccine_id=vaccine_id).order_by(
        VaccinationScheme.ideal_age_months.asc(),
        VaccinationScheme.id_scheme.asc()
    ).all()

    next_index = len(applied)
    if next_index >= len(schedules):
        return jsonify({"error": "No hay dosis pendiente para esta vacuna"}), 400

    schedule   = schedules[next_index]
    age_months = _age_in_months(patient.birth_date)

    if vaccine.min_age_months is not None and age_months < vaccine.min_age_months:
        return jsonify({"error": "Paciente fuera del rango mínimo de edad"}), 400
    if vaccine.max_age_months is not None and age_months > vaccine.max_age_months:
        return jsonify({"error": "Paciente fuera del rango máximo de edad"}), 400

    if applied and schedule.min_interval_days:
        days_since_last = (date.today() - applied[-1].applied_date).days
        if days_since_last < schedule.min_interval_days:
            return jsonify({
                "error": f"Aún no se cumple el intervalo mínimo de {schedule.min_interval_days} días"
            }), 400

    if vaccine.inventory is not None:
        vaccine.inventory -= 1

    new_vaccination = VaccinationRecord(
        patient_id=patient_id,
        vaccine_id=vaccine_id,
        dose_applied=schedule.dose_number,
        applied_date=date.today(),
        worker_id=worker_id
    )

    db.session.add(new_vaccination)
    db.session.commit()

    return jsonify({
        "message":        "Vacuna aplicada correctamente",
        "vaccination_id": new_vaccination.record_id,
        "dose_number":    schedule.dose_number,
        "inventory_left": vaccine.inventory
    })


# =========================
# VERIFICAR ESQUEMA
# =========================

@app.route("/check_schedule/<int:patient_id>", methods=["GET"])
def check_schedule(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"error": "Paciente no encontrado"}), 404

    schedules = VaccinationScheme.query.order_by(
        VaccinationScheme.vaccine_id.asc(),
        VaccinationScheme.ideal_age_months.asc(),
        VaccinationScheme.id_scheme.asc()
    ).all()

    schedule_by_vaccine = {}
    for sch in schedules:
        schedule_by_vaccine.setdefault(sch.vaccine_id, []).append(sch)

    alerts = []
    for vaccine_id, vaccine_schedule in schedule_by_vaccine.items():
        vaccine = db.session.get(Vaccine, vaccine_id)
        if not vaccine:
            continue

        applied = VaccinationRecord.query.filter_by(
            patient_id=patient_id,
            vaccine_id=vaccine_id
        ).order_by(
            VaccinationRecord.applied_date.asc(),
            VaccinationRecord.record_id.asc()
        ).all()

        applied_numbers  = {v.dose_applied for v in applied}
        required_numbers = [s.dose_number for s in vaccine_schedule]
        missing_numbers  = [n for n in required_numbers if n not in applied_numbers]

        if missing_numbers:
            alerts.append({
                "vaccine_id":          vaccine_id,
                "vaccine":             vaccine.name,
                "required_doses":      len(required_numbers),
                "applied_doses":       len(applied),
                "missing_doses":       len(missing_numbers),
                "missing_dose_numbers": missing_numbers
            })

    return jsonify({"patient_id": patient_id, "alerts": alerts})


# =========================
# LOGIN WORKER (API)
# =========================

@app.route("/worker_login", methods=["POST"])
def worker_login():
    data = request.json

    worker = Worker.query.filter(
        or_(Worker.mail == data["mail"], Worker.name == data["mail"])
    ).first()

    if not worker or not worker.check_password(data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify({
        "message":   "Login exitoso",
        "worker_id": worker.worker_id,
        "name":      worker.name,
        "lastname":  worker.lastname,
        "role":      worker.role
    })


# =========================
# OBTENER VACUNAS
# =========================

@app.route("/vaccines", methods=["GET"])
def get_vaccines():
    vaccines = Vaccine.query.all()
    return jsonify([{
        "id":           v.id_vaccine,
        "name":         v.name,
        "inventory":    v.inventory,
        "manufacturer": v.manufacturer,
        "description":  v.description
    } for v in vaccines])


# =========================
# HISTORIAL DE VACUNAS (API)
# =========================

@app.route("/patient_history/<int:patient_id>")
def patient_history(patient_id):
    vaccinations = VaccinationRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(
        VaccinationRecord.applied_date.desc(),
        VaccinationRecord.record_id.desc()
    ).all()

    result = []
    for v in vaccinations:
        vaccine = db.session.get(Vaccine, v.vaccine_id)
        result.append({
            "vaccine": vaccine.name if vaccine else "Desconocida",
            "dose":    v.dose_applied,
            "date":    str(v.applied_date)
        })

    return jsonify(result)




@app.route('/esquema_paciente/<int:id>')
def esquema_paciente(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    patients = Patient.query.all()
    patient, applications, next_vaccines = _load_patient_data(id)

    return render_template(
        'esquemaPaciente.html',
        patient=patient,
        patients=patients,
        applications=applications,
        next_vaccines=next_vaccines,
        name=session.get('user_name', ''),
        lastname=session.get('user_lastname', ''),
        role=session.get('role', '')
    )

# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_default_admin()

    app.run(host="0.0.0.0", port=5000, debug=True)