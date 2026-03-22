from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ------------------ APP SETUP ------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ------------------ DATABASE ------------------
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not set!")

# Fix URL for psycopg3
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class AppUser(db.Model):
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
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("register.html", error="All fields required")

        if AppUser.query.filter_by(email=email).first():
            return render_template("register.html", error="User already exists")

        hashed_pw = generate_password_hash(password)
        user = AppUser(email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = AppUser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.pop("user_id", None)
    return redirect("/login")

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# ------------------ WEIGHT TRACKING ------------------
@app.route('/add_weight', methods=['POST'])
def add_weight():
    if "user_id" not in session:
        return jsonify({"error": "login required"})

    weight_val = request.form.get('weight') or (request.json.get('weight') if request.json else None)
    if not weight_val:
        return jsonify({"error": "No weight provided"})

    weight = float(weight_val)
    new_weight = Weight(user_id=session["user_id"], weight=weight)
    db.session.add(new_weight)
    db.session.commit()
    return jsonify({"status": "saved"})

@app.route('/get_weights')
def get_weights():
    if "user_id" not in session:
        return jsonify([])
    weights = Weight.query.filter_by(user_id=session["user_id"]).all()
    return jsonify([w.weight for w in weights])

# ------------------ INIT DB ------------------
@app.route('/init_db')
def init_db_route():
    db.create_all()
    return "Database Initialized!"

# ------------------ RUN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)