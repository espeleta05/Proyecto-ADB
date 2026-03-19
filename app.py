from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
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
    nfc_token = db.Column(db.String(50), unique=True) 
    allergies = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def birth_date_fmt(self):
        return self.birth_date.strftime('%d/%m/%Y') if self.birth_date else "N/A"

class Guardian(db.Model):
    __tablename__ = 'guardians'
    guardian_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    curp = db.Column(db.String(18), unique=True)
    number = db.Column(db.BigInteger)
    mail = db.Column(db.String(100))
    address = db.Column(db.String(200))

class Relations(db.Model):
    __tablename__ = 'relations'
    relation_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id')) 
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.guardian_id'))

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


class Beacon(db.Model):
    __tablename__ = 'beacons'
    id_beacon = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36))
    major = db.Column(db.Integer)
    minor = db.Column(db.Integer)
    lugar = db.Column(db.String(100))
    estado = db.Column(db.Enum('Online','Offline'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))


class ScanLog(db.Model):
    __tablename__ = "scan_logs"
    log_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.patient_id"))
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

    vaccine = db.relationship('Vaccine')
    worker = db.relationship('Worker')


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

        if worker and worker.check_password(password):

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

    session.pop("user", None)
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

@app.route('/historial')
def historial():
    patients = Patient.query.all()

    return render_template(
        'historial.html',
        patients=patients,
        patient=None,
        applications=[],
        next_vaccines=[]
    )


@app.route('/historial/<int:id>')
def historial_paciente(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    patients = Patient.query.all()
    patient = Patient.query.get_or_404(id)

    relation = Relations.query.filter_by(patient_id=id).first()
    guardian = None
    if relation:
        guardian = Guardian.query.get(relation.guardian_id)

    patient.full_name = f"{patient.first_name} {patient.last_name}"
    patient.guardian = f"{guardian.name} {guardian.lastname}" if guardian else "Sin tutor"
    patient.contact = str(guardian.number) if guardian and guardian.number else "Sin teléfono"
    patient.allergies = patient.allergies or "Ninguna"
    patient.risk = "bajo"

    records = VaccinationRecord.query.filter_by(patient_id=id).all()

    applications = []
    next_vaccines = []

    for r in records:

        vaccine_name = r.vaccine.name if r.vaccine else "Vacuna desconocida"
        doctor_name = f"{r.worker.name} {r.worker.lastname}" if r.worker else "N/A"

        applied_date = r.applied_date.strftime('%d/%m/%Y') if r.applied_date else "N/A"

        # 🔹 Próxima fecha (simulada usando esquema)
        next_date = None

        scheme = VaccinationScheme.query.filter_by(
            vaccine_id=r.vaccine_id,
            dose_number=r.dose_applied
        ).first()

        if scheme and scheme.min_interval_days:
            next_dt = r.applied_date + timedelta(days=scheme.min_interval_days)
            next_date = next_dt.strftime('%d/%m/%Y')

            # guardar próximas
            if next_dt > datetime.today().date():
                next_vaccines.append({
                    "name": vaccine_name,
                    "dose": r.dose_applied,
                    "date": next_date
                })

        #  Armar objeto para el frontend
        app_data = {
            "name": vaccine_name,
            "id": r.vaccine_id,
            "dose": r.dose_applied,
            "date": applied_date,
            "doctor": doctor_name,
            "next_date": next_date,
            "notes": "Aplicación registrada"
        }

        applications.append(app_data)

    return render_template(
        'historial.html',
        patients=patients,
        patient=patient,
        applications=applications,
        next_vaccines=next_vaccines
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

    ok = worker.check_password(data["password"])

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


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
