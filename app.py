from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ------------------ CONFIG ------------------
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# ------------------ DATABASE ------------------
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL not set!")

# Fix postgres:// → postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# ✅ ADD THIS
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

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
    user_id = db.Column(db.Integer)
    weight = db.Column(db.Float)

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
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form

        email = data.get('email')
        password = data.get('password')

        # check if user exists
        if AppUser.query.filter_by(email=email).first():
            return render_template('register.html', error="User already exists")

        hashed = generate_password_hash(password)
        user = AppUser(email=email, password=hashed)

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    data = request.get_json(silent=True) or request.form

    email = data.get('email')
    password = data.get('password')

    user = AppUser.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session["user"] = user.id
        return jsonify({"status": "success"})

    return jsonify({"status": "error"})

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect("/login")

# ------------------ WEIGHT ------------------
@app.route('/add_weight', methods=['POST'])
def add_weight():
    if "user" not in session:
        return jsonify({"error": "login required"})

    data = request.get_json(silent=True) or request.form

    weight_val = data.get('weight')

    if not weight_val:
        return jsonify({"error": "No weight provided"})

    weight = float(weight_val)

    new = Weight(user_id=session["user"], weight=weight)

    db.session.add(new)
    db.session.commit()

    return jsonify({"status": "saved"})

@app.route('/get_weights')
def get_weights():
    if "user" not in session:
        return jsonify([])

    weights = Weight.query.filter_by(user_id=session["user"]).all()
    return jsonify([w.weight for w in weights])

# ------------------ INIT ------------------
@app.route('/init_db')
def init_db():
    db.create_all()
    return "DB Created!"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)