from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from flask_bcrypt import Bcrypt

app = Flask(__name__, template_folder="templates")
app.secret_key = "secretkey"

bcrypt = Bcrypt(app)

# ✅ PostgreSQL connection (Render)
def get_db_connection():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )

# ✅ Home route
@app.route("/")
def home():
    return redirect("/login")

# ✅ Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ✅ Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and bcrypt.check_password_hash(user[3], password):
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ✅ Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# ✅ Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)