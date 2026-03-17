from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ------------------ CONFIG ------------------
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Database (SQLite for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session fix for Render (HTTPS)
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
class User(db.Model):
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
        return render_template("dashboard.html")
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
    data = request.json

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"status": "error", "message": "User already exists"})

    hashed = generate_password_hash(data['password'])

    user = User(email=data['email'], password=hashed)
    db.session.add(user)
    db.session.commit()

    return jsonify({"status": "success"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password, data['password']):
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
    data = request.json
    weight = float(data['weight'])
    height = float(data['height']) / 100

    bmi_value = weight / (height * height)
    return jsonify({"bmi": round(bmi_value, 2)})

# ------------------ WEIGHT TRACKING ------------------

@app.route('/add_weight', methods=['POST'])
def add_weight():
    if "user" not in session:
        return jsonify({"error": "login required"})

    data = request.json
    new_weight = Weight(user_id=session["user"], weight=float(data['weight']))
    
    db.session.add(new_weight)
    db.session.commit()

    return jsonify({"status": "saved"})

@app.route('/get_weights')
def get_weights():
    if "user" not in session:
        return jsonify([])

    weights = Weight.query.filter_by(user_id=session["user"]).all()
    return jsonify([w.weight for w in weights])

# ------------------ HEALTH SCORE ------------------

@app.route('/health_score', methods=['POST'])
def health_score():
    bmi = float(request.json['bmi'])

    if bmi < 18.5:
        score = 60
    elif bmi < 25:
        score = 90
    elif bmi < 30:
        score = 75
    else:
        score = 50

    return jsonify({"score": score})

# ------------------ DIET ------------------

@app.route('/diet', methods=['POST'])
def diet():
    bmi = float(request.json['bmi'])

    if bmi < 18.5:
        diet = "High calorie diet with protein and carbs"
    elif bmi < 25:
        diet = "Balanced diet with fruits, vegetables and protein"
    else:
        diet = "Low calorie diet, reduce sugar and fats"

    return jsonify({"diet": diet})

# ------------------ INIT ------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)