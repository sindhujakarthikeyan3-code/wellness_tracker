from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ------------------ CONFIG ------------------
app.secret_key = os.environ.get("SECRET_KEY", "superstrongsecretkey123!")

# PostgreSQL configuration from Render Secret
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/wellness_db"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session fix for Render
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
class AppUser(db.Model):  # avoid reserved 'user'
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
        # fetch weights safely
        weights = Weight.query.filter_by(user_id=session["user"]).all()
        weights_list = [w.weight for w in weights]
        return render_template("dashboard.html", weights=weights_list)
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

    session["user"] = user.id  # log in immediately
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

# ------------------ DIET ------------------
@app.route('/diet', methods=['POST'])
def diet():
    data = request.get_json(silent=True) or request.form
    try:
        bmi_val = float(data.get('bmi'))
        if bmi_val < 18.5:
            diet_plan = """High-calorie diet with protein and carbs: eggs, milk, nuts, rice, chicken."""
        elif bmi_val < 25:
            diet_plan = """Balanced diet: fruits, vegetables, lean protein, whole grains, moderate fats."""
        elif bmi_val < 30:
            diet_plan = """Low-calorie diet: reduce sugar & fats, more vegetables, lean protein, avoid fried foods."""
        else:
            diet_plan = """Weight-loss diet: strict calorie control, lots of veggies, avoid sugar, increase water intake."""
        return jsonify({"diet": diet_plan})
    except:
        return jsonify({"error": "Invalid BMI"})

# ------------------ DATABASE INIT ------------------
@app.route("/init_db")
def init_db():
    db.create_all()
    return "Tables created successfully!"

# ------------------ INIT ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ensures tables exist before first request
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)