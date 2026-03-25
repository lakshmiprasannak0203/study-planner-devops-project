from flask import Flask, render_template, request, redirect, session
import psycopg2

# CREATE APP FIRST (VERY IMPORTANT)
app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE CONNECTION
conn = psycopg2.connect(
    host="localhost",
    database="study_planner",
    user="postgres",
    password="lakshmi",
    port="5432"
)

# ---------------- HOME ----------------
@app.route("/")
def index():

    if 'user_id' not in session:
        return redirect("/login")

    cur = conn.cursor()

    # SUBJECTS
    cur.execute("SELECT id, subject_name FROM subjects WHERE user_id=%s", (session['user_id'],))
    subjects = cur.fetchall()

    # STUDY SESSIONS
    cur.execute("""
        SELECT s.id, sub.subject_name, s.study_date, s.duration_hours
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.user_id = %s
    """, (session['user_id'],))
    sessions = cur.fetchall()

    # TOTAL HOURS
    cur.execute("SELECT COALESCE(SUM(duration_hours),0) FROM study_sessions WHERE user_id=%s", (session['user_id'],))
    total_hours = cur.fetchone()[0]

    # SUBJECT ANALYSIS
    cur.execute("""
        SELECT sub.subject_name, SUM(s.duration_hours)
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.user_id = %s
        GROUP BY sub.subject_name
        ORDER BY SUM(s.duration_hours) DESC
    """, (session['user_id'],))
    subject_data = cur.fetchall()

    most_studied = subject_data[0][0] if subject_data else "N/A"

    # 🔥 SMART STUDY PLAN
    study_plan = []
    if subject_data:
        max_hours = max([d[1] for d in subject_data])

        for sub, hrs in subject_data:
            if hrs < max_hours:
                study_plan.append((sub, 3, "Focus More 🔴"))
            else:
                study_plan.append((sub, 1, "Revise 🟢"))

    return render_template(
        "index.html",
        subjects=subjects,
        sessions=sessions,
        total_hours=total_hours,
        most_studied=most_studied,
        study_plan=study_plan
    )

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = conn.cursor()
        cur.execute(
            "SELECT id, name FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (name, email, password)
        )
        conn.commit()

        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- ADD SUBJECT ----------------
@app.route("/add_subject", methods=["POST"])
def add_subject():

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO subjects (subject_name, user_id) VALUES (%s,%s)",
        (request.form["subject_name"], session['user_id'])
    )
    conn.commit()

    return redirect("/")

# ---------------- ADD SESSION ----------------
@app.route("/add_session", methods=["POST"])
def add_session():

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO study_sessions (subject_id, study_date, duration_hours, user_id)
        VALUES (%s,%s,%s,%s)
    """, (
        request.form["subject_id"],
        request.form["study_date"],
        request.form["duration_hours"],
        session['user_id']
    ))
    conn.commit()

    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)