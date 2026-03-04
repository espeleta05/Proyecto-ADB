from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from dotenv import load_dotenv
import bcrypt
import uuid
import os

load_dotenv()

app = Flask(__name__)

db_user = os.getenv("db_user", "root")
db_password = os.getenv("db_password", "")
db_host = os.getenv("db_host", "localhost")
db_name = os.getenv("db_name", "vacunas")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
print(app.url_map)

# MODELOS
class Child(db.Model):
    __tablename__ = 'children'
    id = db.Column(db.String(36), primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    birth_date = db.Column(db.Date)

class Beacon(db.Model):
    __tablename__ = 'beacons'
    id_beacon = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36))
    major = db.Column(db.Integer)
    minor = db.Column(db.Integer)
    child_id = db.Column(db.String(36), db.ForeignKey('children.id'))

class Vaccine(db.Model):
    __tablename__ = 'vaccines'
    id_vaccine = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    description = db.Column(db.String(100))
    min_age_months = db.Column(db.Integer)
    max_age_months = db.Column(db.Integer)

class Vaccination(db.Model):
    __tablename__ = "vaccinations"

    vaccination_id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.String(36), db.ForeignKey('children.id'))
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    dose_number = db.Column(db.Integer)
    applied_date = db.Column(db.Date)
    worker_id = db.Column(db.Integer, db.ForeignKey("healthcare_workers.worker_id"))


class VaccinationSchedule(db.Model):
    __tablename__ = 'vaccination_schedule'
    id_schedule = db.Column(db.Integer, primary_key=True)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id_vaccine'))
    dose_number = db.Column(db.Integer)
    recommended_age_months = db.Column(db.Integer)
    min_interval_days = db.Column(db.Integer)

class HealthcareWorker(db.Model):
    __tablename__ = "healthcare_workers"
    worker_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.String(36), db.ForeignKey("children.id"), nullable=False)
    uuid = db.Column(db.String(36), nullable=False)
    major = db.Column(db.Integer, nullable=False)
    minor = db.Column(db.Integer, nullable=False)
    rssi = db.Column(db.Integer, nullable=True)
    scanned_at = db.Column(db.DateTime, nullable=False)
    source_device = db.Column(db.String(30), nullable=True)


# RUTA PRINCIPAL
@app.route("/")
def home():
    return "Servidor Vacunacion Activo"

# REGISTRAR NIÑO
@app.route("/register_child", methods=["POST"])
def register_child():
    data = request.json

    new_child = Child(
        id=str(uuid.uuid4()),
        first_name=data["first_name"],
        last_name=data["last_name"],
        birth_date=data["birth_date"]
    )

    db.session.add(new_child)
    db.session.commit()

    return jsonify({"message": "Niño registrado", "child_id": new_child.id})

# REGISTRAR BEACON
@app.route("/register_beacon", methods=["POST"])
def register_beacon():
    data = request.json

    new_beacon = Beacon(
        uuid=data["uuid"],
        major=data["major"],
        minor=data["minor"],
        child_id=data["child_id"]
    )

    db.session.add(new_beacon)
    db.session.commit()

    return jsonify({"message": "Beacon registrado"})

# ESCANEAR BEACON
@app.route("/scan", methods=["POST"])
def scan():
    data = request.json

    uuid_ = data.get("uuid")
    major = data.get("major")
    minor = data.get("minor")

    # datos crudos extra
    rssi = data.get("rssi")  # puede venir None
    source_device = data.get("source_device", "unknown")

    beacon = Beacon.query.filter_by(uuid=uuid_, major=major, minor=minor).first()
    if not beacon:
        return jsonify({"error": "No encontrado"}), 404

    child = Child.query.get(beacon.child_id)
    if not child:
        return jsonify({"error": "Niño no registrado"}), 404

    # guardar log del escaneo (con timestamp real)
    log = ScanLog(
        child_id=child.id,
        uuid=uuid_,
        major=major,
        minor=minor,
        rssi=rssi,
        scanned_at=datetime.now(),
        source_device=source_device
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "id": child.id,
        "first_name": child.first_name,
        "last_name": child.last_name,
        "birth_date": str(child.birth_date)
    })

@app.route("/scan_logs/<child_id>", methods=["GET"])
def get_scan_logs(child_id):

    logs = ScanLog.query.filter_by(child_id=child_id).order_by(ScanLog.scanned_at.desc()).limit(20).all()

    result = []
    for l in logs:
        result.append({
            "log_id": l.log_id,
            "child_id": l.child_id,
            "uuid": l.uuid,
            "major": l.major,
            "minor": l.minor,
            "rssi": l.rssi,
            "scanned_at": l.scanned_at.isoformat(),
            "source_device": l.source_device
        })

    return jsonify(result)


@app.route("/create_worker", methods=["POST"])
def create_worker():
    data = request.json
    username = data["username"]
    full_name = data["full_name"]
    password = data["password"]

    # hash
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    worker = HealthcareWorker(username=username, full_name=full_name, password_hash=pw_hash)
    db.session.add(worker)
    db.session.commit()

    return jsonify({"message": "Responsable creado", "worker_id": worker.worker_id})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    worker = HealthcareWorker.query.filter_by(username=username).first()
    if not worker:
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    ok = bcrypt.checkpw(password.encode("utf-8"), worker.password_hash.encode("utf-8"))
    if not ok:
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    return jsonify({
        "message": "Login ok",
        "worker_id": worker.worker_id,
        "full_name": worker.full_name
    })



@app.route("/register_vaccine", methods=["POST"])
def register_vaccine():
    data = request.json

    new_vaccine = Vaccine(
        name=data["name"],
        min_age_months=data["min_age_months"],
        max_age_months=data["max_age_months"]
    )

    db.session.add(new_vaccine)
    db.session.commit()

    return jsonify({"message": "Vacuna registrada"})

@app.route("/apply_vaccine", methods=["POST"])
def apply_vaccine():
    data = request.json

    child_id = data["child_id"]
    vaccine_id = data["vaccine_id"]

    worker_id = data.get("worker_id")
    if not worker_id:
        return jsonify({"error": "Falta responsable (worker_id)"}), 400

    child = Child.query.get(child_id)

    if not child:
        return jsonify({"error": "Niño no encontrado"}), 404

    # Calcular edad en meses
    today = date.today()
    age_months = (today.year - child.birth_date.year) * 12 + (today.month - child.birth_date.month)

    # Buscar última dosis aplicada
    last_vaccination = Vaccination.query.filter_by(
        child_id=child_id,
        vaccine_id=vaccine_id
    ).order_by(Vaccination.dose_number.desc()).first()

    if last_vaccination:
        next_dose = last_vaccination.dose_number + 1
    else:
        next_dose = 1

    # Buscar esquema oficial
    schedule = VaccinationSchedule.query.filter_by(
        vaccine_id=vaccine_id,
        dose_number=next_dose
    ).first()

    if not schedule:
        return jsonify({"error": "Esquema completo"}), 400

    # Validar edad
    if age_months < schedule.recommended_age_months:
        return jsonify({"error": "Edad insuficiente para esta dosis"}), 400

    # Validar intervalo mínimo
    if last_vaccination:
        days_since_last = (today - last_vaccination.applied_date).days
        if days_since_last < schedule.min_interval_days:
            return jsonify({"error": "Intervalo mínimo no cumplido"}), 400

    # Guardar aplicación
    new_vaccination = Vaccination(
        child_id=child_id,
        vaccine_id=vaccine_id,
        dose_number=next_dose,
        applied_date=today,
        worker_id=worker_id
    )
    db.session.add(new_vaccination)
    db.session.commit()

    return jsonify({
        "message": "Vacuna aplicada correctamente",
        "dose_number": next_dose
    })

@app.route("/child_history/<child_id>", methods=["GET"])
def child_history(child_id):
    vaccinations = Vaccination.query.filter_by(child_id=child_id).order_by(Vaccination.applied_date.desc()).all()

    result = []
    for v in vaccinations:
        vaccine = Vaccine.query.get(v.vaccine_id)
        result.append({
            "vaccine": vaccine.name,
            "dose_number": v.dose_number,
            "date": str(v.applied_date)
        })

    return jsonify(result)

@app.route("/check_schedule/<child_id>", methods=["GET"])
def check_schedule(child_id):

    child = Child.query.get(child_id)
    if not child:
        return jsonify({"error": "Niño no encontrado"}), 404

    today = date.today()
    age_months = (today.year - child.birth_date.year) * 12 + (today.month - child.birth_date.month)

    alerts = []

    # recorrer todas las vacunas registradas
    vaccines = Vaccine.query.all()

    for vaccine in vaccines:

        # Esquema oficial (dosis) de esa vacuna
        schedules = VaccinationSchedule.query.filter_by(
            vaccine_id=vaccine.id_vaccine
        ).order_by(VaccinationSchedule.dose_number.asc()).all()

        # Dosis requeridas segun edad del niño
        required = [s for s in schedules if age_months >= s.recommended_age_months]

        # Dosis aplicadas
        applied = Vaccination.query.filter_by(
            child_id=child_id,
            vaccine_id=vaccine.id_vaccine
        ).count()

        # Si faltan dosis que ya deberían estar aplicadas
        if applied < len(required):
            missing_numbers = list(range(applied + 1, len(required) + 1))

            alerts.append({
                "vaccine_id": vaccine.id_vaccine,
                "vaccine": vaccine.name,
                "required_doses": len(required),
                "applied_doses": applied,
                "missing_doses": len(required) - applied,
                "missing_dose_numbers": missing_numbers
            })

    return jsonify({
        "child_id": child.id,
        "age_months": age_months,
        "alerts": alerts
    })


@app.route("/vaccines", methods=["GET"])
def get_vaccines():

    vaccines = Vaccine.query.all()

    result = []
    for v in vaccines:
        result.append({
            "id": v.id_vaccine,
            "name": v.name
        })

    return jsonify(result)

@app.route("/can_apply/<child_id>/<int:vaccine_id>", methods=["GET"])
def can_apply(child_id, vaccine_id):
    child = Child.query.get(child_id)
    if not child:
        return jsonify({"can_apply": False, "reason": "Niño no encontrado"}), 404

    today = date.today()
    age_months = (today.year - child.birth_date.year) * 12 + (today.month - child.birth_date.month)

    last_vaccination = Vaccination.query.filter_by(
        child_id=child_id,
        vaccine_id=vaccine_id
    ).order_by(Vaccination.dose_number.desc()).first()

    next_dose = last_vaccination.dose_number + 1 if last_vaccination else 1

    schedule = VaccinationSchedule.query.filter_by(
        vaccine_id=vaccine_id,
        dose_number=next_dose
    ).first()

    if not schedule:
        return jsonify({"can_apply": False, "reason": "Esquema completo"}), 200

    if age_months < schedule.recommended_age_months:
        return jsonify({"can_apply": False, "reason": "Edad insuficiente"}), 200

    if last_vaccination:
        days_since_last = (today - last_vaccination.applied_date).days
        if days_since_last < schedule.min_interval_days:
            return jsonify({"can_apply": False, "reason": "Intervalo mínimo no cumplido"}), 200

    return jsonify({"can_apply": True, "next_dose": next_dose}), 200

@app.route("/population/incomplete", methods=["GET"])
def population_incomplete():
    today = date.today()

    children = Child.query.all()
    total_children = len(children)

    incomplete_children = []

    vaccines = Vaccine.query.all()

    for child in children:
        age_months = (today.year - child.birth_date.year) * 12 + (today.month - child.birth_date.month)

        child_incomplete = False
        details = []

        for vaccine in vaccines:
            schedules = VaccinationSchedule.query.filter_by(
                vaccine_id=vaccine.id_vaccine
            ).all()

            required = [s for s in schedules if age_months >= s.recommended_age_months]

            applied = Vaccination.query.filter_by(
                child_id=child.id,
                vaccine_id=vaccine.id_vaccine
            ).count()

            if applied < len(required):
                child_incomplete = True
                details.append({
                    "vaccine": vaccine.name,
                    "required_doses": len(required),
                    "applied_doses": applied,
                    "missing": len(required) - applied
                })

        if child_incomplete:
            incomplete_children.append({
                "child_id": child.id,
                "first_name": child.first_name,
                "last_name": child.last_name,
                "age_months": age_months,
                "missing_details": details
            })

    incomplete_count = len(incomplete_children)
    percentage = round((incomplete_count / total_children) * 100, 2) if total_children > 0 else 0

    return jsonify({
        "total_children": total_children,
        "incomplete_children": incomplete_count,
        "percentage_incomplete": percentage,
        "details": incomplete_children
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)