from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE CONNECTION (FIXED FOR LOCAL + DOCKER) ----------------
DB_HOST = os.getenv('DB_HOST', 'localhost')  # localhost for local, 'db' for Docker
DB_NAME = os.getenv('DB_NAME', 'study_planner')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'lakshmi')

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port="5432"
)

# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    cur = conn.cursor()

    # Get subjects
    cur.execute("SELECT * FROM subjects")
    subjects = cur.fetchall()

    # Study Sessions
    cur.execute("""
        SELECT s.id, sub.subject_name, s.study_date, s.duration_hours
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
    """)
    sessions = cur.fetchall()

    # Total Study Hours
    cur.execute("SELECT COALESCE(SUM(duration_hours),0) FROM study_sessions")
    total_hours = cur.fetchone()[0]

    # Subject Analytics
    cur.execute("""
        SELECT sub.subject_name, SUM(s.duration_hours)
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        GROUP BY sub.subject_name
        ORDER BY SUM(s.duration_hours) DESC
    """)
    subject_data = cur.fetchall()

    if subject_data:
        most_studied = subject_data[0][0]
        least_studied = subject_data[-1][0]
    else:
        most_studied = "N/A"
        least_studied = "N/A"

    # Smart Study Plan
    study_plan = []
    for sub, hrs in subject_data:
        if hrs < 2:
            status = "Focus More"
        else:
            status = "Good Progress"
        study_plan.append((sub, hrs, status))

    return render_template(
        "index.html",
        sessions=sessions,
        subjects=subjects,
        total_hours=total_hours,
        most_studied=most_studied,
        least_studied=least_studied,
        study_plan=study_plan
    )

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (name,email,password)
        )
        conn.commit()
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )
        user = cur.fetchone()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect("/")
        else:
            return "Invalid Login"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- ADD SUBJECT ----------------
@app.route("/add_subject", methods=["POST"])
def add_subject():
    subject_name = request.form["subject_name"]
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO subjects (subject_name) VALUES (%s)",
        (subject_name,)
    )
    conn.commit()
    return redirect("/")

# ---------------- ADD STUDY SESSION ----------------
@app.route("/add_session", methods=["POST"])
def add_session():
    subject_id = request.form["subject_id"]
    study_date = request.form["study_date"]
    duration_hours = request.form["duration_hours"]

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO study_sessions (subject_id, study_date, duration_hours) VALUES (%s,%s,%s)",
        (subject_id, study_date, duration_hours)
    )
    conn.commit()
    return redirect("/")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
