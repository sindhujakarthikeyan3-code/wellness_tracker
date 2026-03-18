from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ------------------ CONFIG ------------------
# Secret key for sessions
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecretkey")

# PostgreSQL configuration from Render secret
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "postgresql://localhost:5432/wellness_db_ppcr"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session secure settings for Render
if os.environ.get("RENDER"):
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="None"
    )
else:
    app.config.update(
        SESSION_COOKIE_SECURE=False
    )

db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class AppUser(db.Model):  # Avoid 'user' reserved word
    __tablename__ = "app_user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Weight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    if "user" in session:
        weights = Weight.query.filter_by(user_id=session["user"]).all()
        return render_template("dashboard.html", weights=[w.weight for w in weights])
    return redirect("/login")

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/register_page')
def register_page():
    return render_template("register.html")

# ------------------ AUTH ------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or request.form
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Missing fields"})

    existing_user = AppUser.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"status": "error", "message": "User already exists"})

    hashed = generate_password_hash(password)
    user = AppUser(email=email, password=hashed)
    db.session.add(user)
    db.session.commit()

    session["user"] = user.id  # log in after registration
    return jsonify({"status": "success"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Missing fields"})

    user = AppUser.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session["user"] = user.id
        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Invalid credentials"})

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect("/login")

# ------------------ BMI ------------------
@app.route('/bmi', methods=['POST'])
def bmi():
    data = request.get_json(silent=True) or request.form
    try:
        weight = float(data.get('weight'))
        height = float(data.get('height')) / 100
        bmi_value = weight / (height * height)
        return jsonify({"bmi": round(bmi_value, 2)})
    except:
        return jsonify({"error": "Invalid input"})

# ------------------ WEIGHT TRACKING ------------------
@app.route('/add_weight', methods=['POST'])
def add_weight():
    if "user" not in session:
        return jsonify({"error": "login required"})

    data = request.get_json(silent=True) or request.form
    try:
        weight_val = float(data.get('weight'))
        new_weight = Weight(user_id=session["user"], weight=weight_val)
        db.session.add(new_weight)
        db.session.commit()
        return jsonify({"status": "saved"})
    except:
        return jsonify({"error": "Invalid weight"})

@app.route('/get_weights')
def get_weights():
    if "user" not in session:
        return jsonify([])
    weights = Weight.query.filter_by(user_id=session["user"]).all()
    return jsonify([w.weight for w in weights])

# ------------------ HEALTH SCORE ------------------
@app.route('/health_score', methods=['POST'])
def health_score():
    data = request.get_json(silent=True) or request.form
    try:
        bmi_val = float(data.get('bmi'))
        if bmi_val < 18.5:
            score = 60
        elif bmi_val < 25:
            score = 90
        elif bmi_val < 30:
            score = 75
        else:
            score = 50
        return jsonify({"score": score})
    except:
        return jsonify({"error": "Invalid BMI"})

# ------------------ DIET RECOMMENDATION ------------------
@app.route('/diet', methods=['POST'])
def diet():
    data = request.get_json(silent=True) or request.form
    try:
        bmi_val = float(data.get('bmi'))
        if bmi_val < 18.5:
            diet_plan = (
                "High calorie diet with protein, carbs, and healthy fats. "
                "Include nuts, eggs, dairy, lean meats, and whole grains."
            )
        elif bmi_val < 25:
            diet_plan = (
                "Balanced diet with fruits, vegetables, lean protein, "
                "whole grains, and healthy fats. Hydrate well."
            )
        elif bmi_val < 30:
            diet_plan = (
                "Low calorie diet. Reduce sugar and refined carbs, "
                "eat more vegetables, lean protein, and moderate carbs."
            )
        else:
            diet_plan = (
                "Weight loss diet. Strictly reduce sugars, fried foods, "
                "and processed items. Focus on vegetables, lean proteins, "
                "and drink plenty of water."
            )
        return jsonify({"diet": diet_plan})
    except:
        return jsonify({"error": "Invalid BMI"})

# ------------------ INIT ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # create tables in PostgreSQL if not exist
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)