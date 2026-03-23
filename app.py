from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from sqlalchemy import or_, func, case, text
import bcrypt
import os
from urllib.parse import quote_plus
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "bases avanzadas")

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
        f"postgresql+psycopg2://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
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

    if admin:
        return

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

    id_scheme         = db.Column(db.Integer, primary_key=True)
    vaccine_id        = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    dose_number       = db.Column(db.String(50), nullable=False)
    ideal_age_months  = db.Column(db.Integer, nullable=False)
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
# HELPERS
# =========================

def _session_vars():
    """Retorna variables de sesión comunes para todos los render_template."""
    worker_id = session.get("user_id")
    worker = db.session.get(Worker, worker_id) if worker_id else None

    if worker:
        first = (worker.name or "").strip()
        last = (worker.lastname or "").strip()
        role = (worker.role or "Sin rol").strip()

        # Mantener sesión sincronizada con la tabla workers.
        session["user_name"] = first
        session["user_lastname"] = last
        session["role"] = role
    else:
        first = (session.get("user_name") or "").strip()
        last = (session.get("user_lastname") or "").strip()
        role = (session.get("role") or "").strip()

    if first or last:
        initials = ((first[:1] if first else "") + (last[:1] if last else "")).upper()
    else:
        initials = "US"

    return {
        "name":     first,
        "lastname": last,
        "role":     role,
        "initials": initials,
    }


def _authenticate_worker(identifier, password):
    """Autentica contra la tabla workers usando mail o nombre de usuario."""
    identifier = (identifier or "").strip()
    password = password or ""
    if not identifier or not password:
        return None

    identifier_l = identifier.lower()

    candidates = Worker.query.filter(
        or_(
            func.lower(Worker.mail) == identifier_l,
            func.lower(Worker.name) == identifier_l,
        )
    ).order_by(
        # Prioriza coincidencia por mail, luego por nombre de usuario.
        case((func.lower(Worker.mail) == identifier_l, 0), else_=1),
        Worker.worker_id.asc()
    ).all()

    for worker in candidates:
        if worker.password_hash and worker.check_password(password):
            return worker

    return None


def _load_patient_data(id):
    """Carga paciente, historial de aplicaciones y próximas vacunas."""
    from flask import abort

    patient = db.session.get(Patient, id)
    if patient is None:
        abort(404)

    relation = Relations.query.filter_by(patient_id=id).first()
    guardian = db.session.get(Guardian, relation.guardian_id) if relation else None

    patient.full_name = f"{patient.first_name} {patient.last_name}"
    patient.guardian  = f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor"
    patient.contact   = str(guardian.number) if guardian and guardian.number else "Sin teléfono"
    patient.allergies = patient.allergies or "Ninguna"
    patient.age       = _age_in_years(patient.birth_date)
    patient.risk      = "bajo"

    records = VaccinationRecord.query.filter_by(patient_id=id).all()

    applications  = []
    next_vaccines = []

    for r in records:
        vaccine_name = r.vaccine.name if r.vaccine else "Vacuna desconocida"
        doctor_name  = f"{r.worker.name} {r.worker.lastname}" if r.worker else "N/A"
        applied_date = r.applied_date.strftime('%d/%m/%Y') if r.applied_date else "N/A"

        next_date = None
        scheme = VaccinationScheme.query.filter_by(
            vaccine_id=r.vaccine_id,
            dose_number=r.dose_applied
        ).first()

        if scheme and scheme.min_interval_days:
            next_dt   = r.applied_date + timedelta(days=scheme.min_interval_days)
            next_date = next_dt.strftime('%d/%m/%Y')

            if next_dt > date.today():
                next_vaccines.append({
                    "name": vaccine_name,
                    "dose": r.dose_applied,
                    "date": next_date
                })

        applications.append({
            "name":      vaccine_name,
            "id":        r.vaccine_id,
            "dose":      r.dose_applied,
            "date":      applied_date,
            "doctor":    doctor_name,
            "next_date": next_date,
            "notes":     "Aplicación registrada"
        })

    return patient, applications, next_vaccines


# =========================
# AUTH
# =========================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("mail", "").strip()
        password   = request.form.get("password") or ""

        if not identifier or not password:
            return render_template("login.html", error="Debes ingresar usuario/mail y contraseña")

        identifier_l = identifier.lower()
        worker_exists = Worker.query.filter(
            or_(
                func.lower(Worker.mail) == identifier_l,
                func.lower(Worker.name) == identifier_l,
            )
        ).first()

        worker = _authenticate_worker(identifier, password)

        if not worker_exists:
            return render_template("login.html", error="Usuario o correo no encontrado")

        if not worker:
            return render_template("login.html", error="Contraseña incorrecta")

        session["user_id"]       = worker.worker_id
        session["user_name"]     = worker.name
        session["user_lastname"] = worker.lastname or ""
        session["user_mail"]     = worker.mail
        session["role"]          = worker.role or "Sin rol"
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    if "user_mail" not in session:
        return redirect(url_for("login"))

    today = datetime.now().strftime("%A, %d de %B, %Y")

    total_patients     = Patient.query.count()
    total_vaccines     = Vaccine.query.count()
    applications_today = VaccinationRecord.query.filter_by(applied_date=date.today()).count()

    patient_rows = db.session.query(
        Patient,
        Guardian.guardian_id,
        Guardian.name,
        Guardian.lastname
    ).outerjoin(
        Relations, Relations.patient_id == Patient.patient_id
    ).outerjoin(
        Guardian, Guardian.guardian_id == Relations.guardian_id
    ).order_by(Patient.created_at.desc()).limit(5).all()

    top_patients = []
    for row in patient_rows:
        patient = row[0]
        guardian_name = f"{row[2]} {row[3]}" if row[1] else "Sin tutor"
        top_patients.append({
            "patient_id": patient.patient_id,
            "first_name": patient.first_name,
            "last_name":  patient.last_name,
            "guardian":   guardian_name,
            "age":        _age_in_years(patient.birth_date),
            "blood_type": patient.blood_type,
            "allergies":  patient.allergies or "Ninguna"
        })

    dashboard_vaccines = Vaccine.query.order_by(Vaccine.inventory.asc()).limit(4).all()

    return render_template(
        "index.html",
        today=today,
        total_patients=total_patients,
        total_vaccines=total_vaccines,
        applications_today=applications_today,
        top_patients=top_patients,
        dashboard_vaccines=dashboard_vaccines,
        **_session_vars()
    )


# =========================
# PACIENTES
# =========================

@app.route("/pacientes")
def pacientes():
    if "user_id" not in session:
        return redirect(url_for("login"))

    patient_rows = db.session.query(
        Patient,
        Guardian.guardian_id,
        Guardian.name,
        Guardian.lastname,
        Guardian.number
    ).outerjoin(
        Relations, Relations.patient_id == Patient.patient_id
    ).outerjoin(
        Guardian, Guardian.guardian_id == Relations.guardian_id
    ).order_by(Patient.created_at.desc()).all()

    patients_data = []
    for row in patient_rows:
        patient = row[0]
        guardian_name = f"{row[2]} {row[3]}" if row[1] else "Sin tutor"
        guardian_number = str(row[4]) if row[1] and row[4] else "Sin teléfono"
        patients_data.append({
            "patient_id": patient.patient_id,
            "full_name":  f"{patient.first_name} {patient.last_name}",
            "birth_date": patient.birth_date.strftime("%d/%m/%Y"),
            "guardian":   guardian_name,
            "contact":    guardian_number,
            "blood_type": patient.blood_type,
            "allergies":  patient.allergies or "Ninguna",
            "risk":       "bajo"
        })

    return render_template(
        "pacientes.html",
        patients=patients_data,
        total_patients=len(patients_data),
        **_session_vars()
    )


# =========================
# VACUNAS
# =========================

@app.route("/vacunas")
def vacunas_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    vaccines = Vaccine.query.order_by(Vaccine.name.asc()).all()

    return render_template(
        "vacunas.html",
        vaccines=vaccines,
        total_vaccines=len(vaccines),
        **_session_vars()
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
        **_session_vars()
    )


# =========================
# HISTORIAL
# =========================

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    patients = Patient.query.order_by(Patient.created_at.desc(), Patient.patient_id.desc()).all()

    patient = None
    applications = []
    next_vaccines = []

    if patients:
        patient, applications, next_vaccines = _load_patient_data(patients[0].patient_id)

    return render_template(
        'historial.html',
        patients=patients,
        patient=patient,
        applications=applications,
        next_vaccines=next_vaccines,
        **_session_vars()
    )


@app.route('/historial/<int:id>')
def historial_paciente(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    patients = Patient.query.order_by(Patient.created_at.desc(), Patient.patient_id.desc()).all()
    patient, applications, next_vaccines = _load_patient_data(id)

    return render_template(
        'historial.html',
        patients=patients,
        patient=patient,
        applications=applications,
        next_vaccines=next_vaccines,
        **_session_vars()
    )


# =========================
# ESQUEMA PACIENTE
# =========================

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
        **_session_vars()
    )


# =========================
# APLICACIONES
# =========================

@app.route('/aplicaciones')
def aplicaciones():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
            next_entry = next_scheme[applied_count]
            if next_entry.min_interval_days:
                next_date = (
                    record.applied_date + timedelta(days=next_entry.min_interval_days)
                ).strftime('%d/%m/%Y')

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

    from sqlalchemy import func
    today_count     = VaccinationRecord.query.filter_by(applied_date=date.today()).count()
    unique_patients = db.session.query(VaccinationRecord.patient_id).distinct().count()
    unique_vaccines = db.session.query(VaccinationRecord.vaccine_id).distinct().count()

    return render_template(
        'aplicaciones.html',
        applications=applications,
        total_applications=len(applications),
        total_patients_attended=unique_patients,
        total_unique_vaccines=unique_vaccines,
        applications_today=today_count,
        **_session_vars()
    )


# =========================
# MAPA DE RIESGO
# =========================

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

    zones             = []
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
        **_session_vars()
    )


# =========================
# REPORTES PUBLICOS
# =========================

def _parse_date_arg(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _json_ready(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_rows(rows):
    output = []
    for row in rows:
        output.append({k: _json_ready(v) for k, v in row.items()})
    return output


def _fallback_public_report_data(from_date, to_date, min_group):
    """Genera reporte agregado sin SP, usando queries SQLAlchemy como respaldo."""
    base_filter = [
        VaccinationRecord.applied_date >= from_date,
        VaccinationRecord.applied_date <= to_date,
    ]

    total_doses_applied = VaccinationRecord.query.filter(*base_filter).count()
    target_population = Patient.query.count()
    reached_population = db.session.query(
        func.count(func.distinct(VaccinationRecord.patient_id))
    ).filter(*base_filter).scalar() or 0

    coverage_percent = 0.0
    if target_population > 0:
        coverage_percent = round((reached_population / target_population) * 100, 2)

    monthly_raw = db.session.query(
        func.date_trunc('month', VaccinationRecord.applied_date).label('period_start'),
        func.count(VaccinationRecord.record_id).label('doses_applied'),
        func.count(func.distinct(VaccinationRecord.patient_id)).label('unique_patients'),
    ).filter(
        *base_filter
    ).group_by(
        func.date_trunc('month', VaccinationRecord.applied_date)
    ).order_by(
        func.date_trunc('month', VaccinationRecord.applied_date)
    ).all()

    monthly_rows = []
    for r in monthly_raw:
        period_start = r.period_start.date() if hasattr(r.period_start, 'date') else r.period_start
        monthly_rows.append({
            'period_start': period_start,
            'period_label': period_start.strftime('%Y-%m') if period_start else '',
            'doses_applied': int(r.doses_applied or 0),
            'unique_patients': int(r.unique_patients or 0),
        })

    vaccine_raw = db.session.query(
        Vaccine.name.label('vaccine_name'),
        func.count(VaccinationRecord.record_id).label('doses_applied'),
        func.count(func.distinct(VaccinationRecord.patient_id)).label('unique_patients'),
    ).join(
        Vaccine, Vaccine.id_vaccine == VaccinationRecord.vaccine_id
    ).filter(
        *base_filter
    ).group_by(
        Vaccine.name
    ).order_by(
        func.count(VaccinationRecord.record_id).desc()
    ).limit(8).all()

    vaccines_rows = []
    for r in vaccine_raw:
        doses = int(r.doses_applied or 0)
        share = round((doses / total_doses_applied) * 100, 2) if total_doses_applied else 0.0
        vaccines_rows.append({
            'vaccine_name': r.vaccine_name,
            'doses_applied': doses,
            'unique_patients': int(r.unique_patients or 0),
            'share_percent': share,
        })

    zone_raw = db.session.query(
        VaccinationRecord.clinic_location.label('zone_name'),
        func.count(VaccinationRecord.record_id).label('doses_applied'),
        func.count(func.distinct(VaccinationRecord.patient_id)).label('unique_patients'),
    ).filter(
        *base_filter,
        VaccinationRecord.clinic_location.isnot(None),
        VaccinationRecord.clinic_location != ''
    ).group_by(
        VaccinationRecord.clinic_location
    ).having(
        func.count(func.distinct(VaccinationRecord.patient_id)) >= min_group
    ).order_by(
        func.count(VaccinationRecord.record_id).desc()
    ).all()

    zones_rows = []
    for r in zone_raw:
        doses = int(r.doses_applied or 0)
        if doses >= 40:
            risk_level, risk_label = 'high', 'Alto'
        elif doses >= 20:
            risk_level, risk_label = 'medium', 'Medio'
        else:
            risk_level, risk_label = 'low', 'Bajo'

        zones_rows.append({
            'zone_name': r.zone_name,
            'doses_applied': doses,
            'unique_patients': int(r.unique_patients or 0),
            'risk_level': risk_level,
            'risk_label': risk_label,
        })

    kpis = {
        'total_doses_applied': int(total_doses_applied),
        'target_population': int(target_population),
        'reached_population': int(reached_population),
        'coverage_percent': coverage_percent,
        'avg_delay_days': 0.0,
        'active_zones': len(zones_rows),
    }

    return kpis, monthly_rows, vaccines_rows, zones_rows


@app.route('/reportes-publicos')
def reportes_publicos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('reportesPublicos.html', **_session_vars())


@app.route('/api/global-search', methods=['GET'])
def api_global_search():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    q = (request.args.get('q') or '').strip()
    if len(q) < 1:
        return jsonify({'results': []})

    q_lower = q.lower()
    pattern = f"%{q_lower}%"

    patient_rows = db.session.query(Patient).filter(
        or_(
            func.lower(Patient.first_name).like(pattern),
            func.lower(Patient.last_name).like(pattern),
            func.lower((Patient.first_name + ' ' + Patient.last_name)).like(pattern),
            func.cast(Patient.patient_id, db.String).like(f"%{q}%")
        )
    ).order_by(Patient.first_name.asc()).limit(5).all()

    vaccine_rows = db.session.query(Vaccine).filter(
        or_(
            func.lower(Vaccine.name).like(pattern),
            func.cast(Vaccine.id_vaccine, db.String).like(f"%{q}%")
        )
    ).order_by(Vaccine.name.asc()).limit(5).all()

    worker_rows = db.session.query(Worker).filter(
        or_(
            func.lower(Worker.name).like(pattern),
            func.lower(Worker.lastname).like(pattern),
            func.lower((Worker.name + ' ' + Worker.lastname)).like(pattern),
            func.lower(Worker.mail).like(pattern),
            func.cast(Worker.worker_id, db.String).like(f"%{q}%")
        )
    ).order_by(Worker.name.asc()).limit(5).all()

    results = []

    for p in patient_rows:
        full_name = f"{(p.first_name or '').strip()} {(p.last_name or '').strip()}".strip()
        results.append({
            'type': 'paciente',
            'title': full_name,
            'subtitle': f"ID {p.patient_id}",
            'url': f"/pacientes?q={quote_plus(full_name or str(p.patient_id))}"
        })

    for v in vaccine_rows:
        results.append({
            'type': 'vacuna',
            'title': (v.name or '').strip(),
            'subtitle': f"ID {v.id_vaccine}",
            'url': f"/vacunas?q={quote_plus((v.name or '').strip() or str(v.id_vaccine))}"
        })

    for w in worker_rows:
        full_name = f"{(w.name or '').strip()} {(w.lastname or '').strip()}".strip()
        results.append({
            'type': 'personal',
            'title': full_name,
            'subtitle': f"{w.role or 'Sin rol'} - {w.mail or 'Sin correo'}",
            'url': f"/personal?q={quote_plus(full_name or (w.mail or str(w.worker_id)))}"
        })

    return jsonify({'results': results[:15]})


@app.route('/api/reportes-publicos/resumen', methods=['GET'])
def api_reportes_publicos_resumen():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    today = date.today()
    default_from = today - timedelta(days=3650)

    from_date = _parse_date_arg(request.args.get('from')) or default_from
    to_date = _parse_date_arg(request.args.get('to')) or today

    if from_date > to_date:
        return jsonify({'error': 'Rango de fechas inválido'}), 400

    min_group = request.args.get('min_group', '1').strip()
    try:
        min_group = max(int(min_group), 1)
    except ValueError:
        min_group = 1

    params = {
        'from_date': from_date,
        'to_date': to_date,
        'min_group': min_group,
    }

    try:
        kpis_row = db.session.execute(
            text("SELECT * FROM sp_public_report_kpis(:from_date, :to_date, :min_group)"),
            params,
        ).mappings().first()

        monthly_rows = db.session.execute(
            text("SELECT * FROM sp_public_report_monthly(:from_date, :to_date, :min_group)"),
            params,
        ).mappings().all()

        vaccine_rows = db.session.execute(
            text("SELECT * FROM sp_public_report_vaccine_progress(:from_date, :to_date, :min_group)"),
            params,
        ).mappings().all()

        zone_rows = db.session.execute(
            text("SELECT * FROM sp_public_report_zone_risk(:from_date, :to_date, :min_group)"),
            params,
        ).mappings().all()
    except Exception as ex:
        db.session.rollback()
        kpis, monthly_rows, vaccine_rows, zone_rows = _fallback_public_report_data(
            from_date=from_date,
            to_date=to_date,
            min_group=min_group,
        )

        return jsonify({
            'filters': {
                'from': from_date.isoformat(),
                'to': to_date.isoformat(),
                'min_group': min_group,
            },
            'kpis': {k: _json_ready(v) for k, v in (kpis or {}).items()},
            'monthly': _serialize_rows(monthly_rows),
            'vaccines': _serialize_rows(vaccine_rows),
            'zones': _serialize_rows(zone_rows),
            'warning': 'Se uso modo de respaldo sin SP en la base local.',
            'detail': str(ex),
        }), 200

    return jsonify({
        'filters': {
            'from': from_date.isoformat(),
            'to': to_date.isoformat(),
            'min_group': min_group,
        },
        'kpis': {k: _json_ready(v) for k, v in (kpis_row or {}).items()},
        'monthly': _serialize_rows(monthly_rows),
        'vaccines': _serialize_rows(vaccine_rows),
        'zones': _serialize_rows(zone_rows),
    })


# =========================
# PERSONAL
# =========================

@app.route('/personal')
def personal():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    workers = Worker.query.order_by(Worker.role.asc(), Worker.name.asc()).all()

    workers_data = [{
        'worker_id': w.worker_id,
        'name':      w.name,
        'lastname':  w.lastname or '',
        'role':      w.role or 'Sin rol',
        'mail':      w.mail,
    } for w in workers]

    return render_template(
        'personal.html',
        workers=workers_data,
        total_workers=len(workers_data),
        **_session_vars()
    )


@app.route('/personal/agregar', methods=['GET', 'POST'])
def add_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name             = request.form.get('name', '').strip()
        lastname         = request.form.get('lastname', '').strip()
        birth_date_str   = request.form.get('birth_date', '').strip()
        role             = request.form.get('role', '').strip()
        curp             = request.form.get('curp', '').strip() or None
        mail             = request.form.get('mail', '').strip()
        address          = request.form.get('address', '').strip() or None
        password         = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not all([name, lastname, birth_date_str, role, mail, password]):
            return render_template('add_user.html',
                error='Por favor completa todos los campos obligatorios.',
                form=request.form, **_session_vars())

        if password != password_confirm:
            return render_template('add_user.html',
                error='Las contraseñas no coinciden.',
                form=request.form, **_session_vars())

        if Worker.query.filter_by(mail=mail).first():
            return render_template('add_user.html',
                error='Ya existe un usuario con ese email o nombre de usuario.',
                form=request.form, **_session_vars())

        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            return render_template('add_user.html',
                error='Fecha de nacimiento inválida.',
                form=request.form, **_session_vars())

        new_worker = Worker(
            name=name,
            lastname=lastname,
            birth_date=birth_date,
            role=role,
            curp=curp,
            mail=mail,
            address=address,
            password_hash=bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt()
            ).decode('utf-8')
        )

        db.session.add(new_worker)
        db.session.commit()
        return redirect(url_for('personal'))

    return render_template(
        'add_user.html',
        form={},
        error=None,
        **_session_vars()
    )

# =========================
# REGISTRAR APLICACIÓN (FORM)
# =========================
 
@app.route('/aplicaciones/registrar', methods=['GET', 'POST'])
def agregar_aplicacion():
    if 'user_id' not in session:
        return redirect(url_for('login'))
 
    patients = Patient.query.order_by(Patient.first_name.asc()).all()
    vaccines = Vaccine.query.order_by(Vaccine.name.asc()).all()
    workers  = Worker.query.order_by(Worker.name.asc()).all()
    today    = date.today().strftime('%Y-%m-%d')
 
    if request.method == 'POST':
        patient_id      = request.form.get('patient_id', '').strip()
        vaccine_id      = request.form.get('vaccine_id', '').strip()
        worker_id       = request.form.get('worker_id', '').strip() or session.get('user_id')
        applied_date_str = request.form.get('applied_date', '').strip()
        lot_number      = request.form.get('lot_number', '').strip() or None
        clinic_location = request.form.get('clinic_location', '').strip() or None
 
        def render_error(msg):
            return render_template('add_aplicacion.html',
                error=msg,
                form=request.form,
                patients=patients,
                vaccines=vaccines,
                workers=workers,
                today=today,
                **_session_vars()
            )
 
        if not patient_id or not vaccine_id or not applied_date_str:
            return render_error('Paciente, vacuna y fecha son obligatorios.')
 
        try:
            applied_date = datetime.strptime(applied_date_str, '%Y-%m-%d').date()
        except ValueError:
            return render_error('Fecha de aplicación inválida.')
 
        patient = db.session.get(Patient, int(patient_id))
        if not patient:
            return render_error('Paciente no encontrado.')
 
        vaccine = db.session.get(Vaccine, int(vaccine_id))
        if not vaccine:
            return render_error('Vacuna no encontrada.')
 
        if vaccine.inventory is not None and vaccine.inventory <= 0:
            return render_error(f'No hay inventario disponible para {vaccine.name}.')
 
        # Determinar qué dosis corresponde según el esquema
        applied_count = VaccinationRecord.query.filter_by(
            patient_id=int(patient_id),
            vaccine_id=int(vaccine_id)
        ).count()
 
        schedules = VaccinationScheme.query.filter_by(
            vaccine_id=int(vaccine_id)
        ).order_by(
            VaccinationScheme.ideal_age_months.asc(),
            VaccinationScheme.id_scheme.asc()
        ).all()
 
        if applied_count >= len(schedules):
            return render_error(f'El paciente ya completó todas las dosis programadas de {vaccine.name}.')
 
        dose_number = schedules[applied_count].dose_number
 
        # Reducir inventario
        if vaccine.inventory is not None:
            vaccine.inventory -= 1
 
        new_record = VaccinationRecord(
            patient_id=int(patient_id),
            vaccine_id=int(vaccine_id),
            worker_id=int(worker_id) if worker_id else None,
            applied_date=applied_date,
            dose_applied=dose_number,
            lot_number=lot_number,
            clinic_location=clinic_location
        )
 
        try:
            db.session.add(new_record)
            db.session.commit()
            return redirect(url_for('aplicaciones'))
        except Exception as e:
            db.session.rollback()
            return render_error(f'Error al guardar: {str(e)}')
 
    return render_template(
        'agregarAplicacion.html',
        form={},
        error=None,
        patients=patients,
        vaccines=vaccines,
        workers=workers,
        today=today,
        **_session_vars()
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

    try:
        birth = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido (use YYYY-MM-DD)"}), 400

    def _clean_text(value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _clean_phone(value):
        text = _clean_text(value)
        if not text:
            return None
        digits = ''.join(ch for ch in text if ch.isdigit())
        return int(digits) if digits else None

    blood_type = _clean_text(data.get("blood_type")) or "O+"

    try:
        new_patient = Patient(
            first_name=data["first_name"],
            last_name=data["last_name"],
            birth_date=birth,
            blood_type=blood_type,
            gender=data["gender"],
            nfc_token=_clean_text(data.get("nfc_token")),
            allergies=_clean_text(data.get("allergies")),
            notes=_clean_text(data.get("notes"))
        )

        db.session.add(new_patient)
        db.session.flush()

        tutor_data = data.get("tutor", {})
        new_guardian = None

        tutor_name = _clean_text(tutor_data.get("name"))
        tutor_lastname = _clean_text(tutor_data.get("lastname"))
        tutor_curp = _clean_text(tutor_data.get("curp"))

        if tutor_name or tutor_lastname:
            if tutor_curp:
                existing = Guardian.query.filter_by(curp=tutor_curp).first()
                new_guardian = existing or Guardian(
                    name=tutor_name,
                    lastname=tutor_lastname,
                    curp=tutor_curp,
                    number=_clean_phone(tutor_data.get("number")),
                    mail=_clean_text(tutor_data.get("mail")),
                    address=_clean_text(tutor_data.get("address"))
                )
                if not existing:
                    db.session.add(new_guardian)
                    db.session.flush()
            else:
                new_guardian = Guardian(
                    name=tutor_name,
                    lastname=tutor_lastname,
                    number=_clean_phone(tutor_data.get("number")),
                    mail=_clean_text(tutor_data.get("mail")),
                    address=_clean_text(tutor_data.get("address"))
                )
                db.session.add(new_guardian)
                db.session.flush()

            if new_guardian:
                db.session.add(Relations(
                    patient_id=new_patient.patient_id,
                    guardian_id=new_guardian.guardian_id
                ))

        db.session.commit()
        return jsonify({"message": "Paciente registrado correctamente", "patient_id": new_patient.patient_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
        inventory = 0

    def parse_int(val):
        if val is None or val == "":
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    vaccine = Vaccine(
        name=data["name"].strip(),
        inventory=inventory,
        manufacturer=(data.get("manufacturer") or "").strip() or None,
        description=(data.get("description") or "").strip() or None,
        min_age_months=parse_int(data.get("min_age_months")),
        max_age_months=parse_int(data.get("max_age_months"))
    )

    db.session.add(vaccine)
    db.session.commit()

    return jsonify({"message": "Vacuna registrada", "vaccine_id": vaccine.id_vaccine})

# =========================
# ELIMINAR PACIENTE
# =========================

@app.route("/delete_patient/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"error": "Paciente no encontrado"}), 404

    try:
        Relations.query.filter_by(patient_id=patient_id).delete()
        VaccinationRecord.query.filter_by(patient_id=patient_id).delete()
        ScanLog.query.filter_by(patient_id=patient_id).delete()
        Beacon.query.filter_by(patient_id=patient_id).delete()
        db.session.delete(patient)
        db.session.commit()
        return jsonify({"message": "Paciente eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================
# ELIMINAR VACUNA
# =========================

@app.route("/delete_vaccine/<int:vaccine_id>", methods=["POST"])
def delete_vaccine(vaccine_id):
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401

    vaccine = db.session.get(Vaccine, vaccine_id)
    if not vaccine:
        return jsonify({"error": "Vacuna no encontrada"}), 404

    try:
        VaccinationRecord.query.filter_by(vaccine_id=vaccine_id).delete()
        VaccinationScheme.query.filter_by(vaccine_id=vaccine_id).delete()
        db.session.delete(vaccine)
        db.session.commit()
        return jsonify({"message": "Vacuna eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================
# BEACON & SCAN
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
# APLICAR VACUNA (API)
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
# VERIFICAR ESQUEMA (API)
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
                "vaccine_id":           vaccine_id,
                "vaccine":              vaccine.name,
                "required_doses":       len(required_numbers),
                "applied_doses":        len(applied),
                "missing_doses":        len(missing_numbers),
                "missing_dose_numbers": missing_numbers
            })

    return jsonify({"patient_id": patient_id, "alerts": alerts})


# =========================
# OTROS ENDPOINTS API
# =========================

@app.route("/worker_login", methods=["POST"])
def worker_login():
    data = request.json or {}
    worker = _authenticate_worker(data.get("mail", ""), data.get("password", ""))
    if not worker:
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify({
        "message":   "Login exitoso",
        "worker_id": worker.worker_id,
        "name":      worker.name,
        "lastname":  worker.lastname,
        "role":      worker.role
    })


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


# =========================
# Start server
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_default_admin()

    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "5000"))
    app_debug = os.getenv("APP_DEBUG", "0").strip() == "1"
    use_waitress = os.getenv("USE_WAITRESS", "0").strip() == "1"  # Cambié a 0 para usar Flask dev server

    print(f"\n{'='*60}")
    print(f"🚀 SERVIDOR INICIANDO")
    print(f"{'='*60}")
    print(f"  Local:  http://localhost:{app_port}")
    print(f"  Red:    http://172.32.216.26:{app_port}")
    print(f"  Debug:  {app_debug}")
    print(f"  Waitress: {use_waitress}")
    print(f"{'='*60}\n")

    if use_waitress:
        from waitress import serve
        serve(app, host=app_host, port=app_port)
    else:
        app.run(host=app_host, port=app_port, debug=app_debug, use_reloader=False)