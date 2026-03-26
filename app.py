from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE CONNECTION ----------------
DB_HOST = os.getenv('DB_HOST', 'localhost')
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

# -------- CALCULATE STUDY STREAK --------
def calculate_study_streak(user_id):
    """
    Calculate the current study streak for a user.
    
    Logic:
    1. Get all unique study dates for the user
    2. Sort them in descending order
    3. Check if the most recent date is today or yesterday
    4. Count consecutive days backwards from the most recent date
    5. Return current streak and longest streak
    """
    cur = conn.cursor()
    
    # Get all unique study dates for the user, sorted in descending order
    cur.execute("""
        SELECT DISTINCT study_date 
        FROM study_sessions 
        WHERE user_id=%s 
        ORDER BY study_date DESC
    """, (user_id,))
    
    study_dates = cur.fetchall()
    
    if not study_dates:
        return 0, 0  # No study records
    
    # Convert dates to date objects for comparison
    study_dates_list = [date_tuple[0] for date_tuple in study_dates]
    today = datetime.now().date()
    
    # -------- Calculate Current Streak --------
    current_streak = 0
    start_date = study_dates_list[0]  # Most recent date
    
    # If the most recent study date is not today or yesterday, streak is 0
    if (today - start_date).days > 1:
        current_streak = 0
    else:
        # Count consecutive days from the most recent date
        current_date = start_date
        for study_date in study_dates_list:
            # Check if this date is exactly one day before the current date
            if (current_date - study_date).days == 1:
                current_streak += 1
                current_date = study_date
            elif study_date == current_date:
                # Same day, add to streak
                current_streak += 1
            else:
                # Gap found, streak breaks
                break
    
    # -------- Calculate Longest Streak --------
    longest_streak = 0
    streak = 1
    
    for i in range(len(study_dates_list) - 1):
        current = study_dates_list[i]
        next_date = study_dates_list[i + 1]
        
        # Check if dates are consecutive
        if (current - next_date).days == 1:
            streak += 1
        else:
            longest_streak = max(longest_streak, streak)
            streak = 1
    
    longest_streak = max(longest_streak, streak)
    
    return current_streak, longest_streak


# ---------------- HOME PAGE ----------------
@app.route("/")
def index():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cur = conn.cursor()

    # -------- Subjects (Only for logged in user)
    cur.execute(
        "SELECT id, subject_name FROM subjects WHERE user_id=%s ORDER BY id",
        (user_id,)
    )
    subjects = cur.fetchall()

    # -------- Study Sessions
    cur.execute("""
        SELECT s.id, sub.subject_name, s.study_date, s.duration_hours
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.user_id=%s
    """, (user_id,))
    sessions = cur.fetchall()

    # -------- Total Study Hours
    cur.execute(
        "SELECT COALESCE(SUM(duration_hours),0) FROM study_sessions WHERE user_id=%s",
        (user_id,)
    )
    total_hours = cur.fetchone()[0]

    # -------- Study Streak
    current_streak, longest_streak = calculate_study_streak(user_id)

    # -------- Subject Analytics
    cur.execute("""
        SELECT sub.subject_name, SUM(s.duration_hours)
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.user_id=%s
        GROUP BY sub.subject_name
        ORDER BY SUM(s.duration_hours) DESC
    """, (user_id,))
    subject_data = cur.fetchall()

    if subject_data:
        most_studied = subject_data[0][0]
        least_studied = subject_data[-1][0]
    else:
        most_studied = "N/A"
        least_studied = "N/A"

    # -------- Smart Study Plan
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
        study_plan=study_plan,
        current_streak=current_streak,
        longest_streak=longest_streak
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
    user_id = session["user_id"]

    cur = conn.cursor()

    cur.execute(
        "INSERT INTO subjects (subject_name, user_id) VALUES (%s,%s)",
        (subject_name, user_id)
    )

    conn.commit()

    return redirect("/")


# ---------------- UPDATE SUBJECT ----------------
@app.route("/update_subject/<int:subject_id>", methods=["POST"])
def update_subject(subject_id):

    subject_name = request.form["subject_name"]
    user_id = session["user_id"]

    cur = conn.cursor()

    # Verify that the subject belongs to the logged-in user
    cur.execute("SELECT user_id FROM subjects WHERE id=%s", (subject_id,))
    subject_owner = cur.fetchone()

    if not subject_owner or subject_owner[0] != user_id:
        return "Unauthorized: This subject does not belong to you!", 403

    cur.execute(
        "UPDATE subjects SET subject_name=%s WHERE id=%s AND user_id=%s",
        (subject_name, subject_id, user_id)
    )

    conn.commit()

    return redirect("/")


# ---------------- DELETE SUBJECT ----------------
@app.route("/delete_subject/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):

    user_id = session["user_id"]

    cur = conn.cursor()

    # Verify that the subject belongs to the logged-in user
    cur.execute("SELECT user_id FROM subjects WHERE id=%s", (subject_id,))
    subject_owner = cur.fetchone()

    if not subject_owner or subject_owner[0] != user_id:
        return "Unauthorized: This subject does not belong to you!", 403

    # Delete all study sessions related to this subject first (cascade delete)
    cur.execute(
        "DELETE FROM study_sessions WHERE subject_id=%s AND user_id=%s",
        (subject_id, user_id)
    )

    # Delete the subject
    cur.execute(
        "DELETE FROM subjects WHERE id=%s AND user_id=%s",
        (subject_id, user_id)
    )

    conn.commit()

    return redirect("/")


# ---------------- ADD STUDY SESSION ----------------
@app.route("/add_session", methods=["POST"])
def add_session():

    subject_id = request.form["subject_id"]
    study_date = request.form["study_date"]
    duration_hours = request.form["duration_hours"]
    user_id = session["user_id"]

    # Verify that the subject belongs to the logged-in user
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM subjects WHERE id=%s", (subject_id,))
    subject_owner = cur.fetchone()

    if not subject_owner or subject_owner[0] != user_id:
        return "Unauthorized: This subject does not belong to you!"

    cur.execute(
        """INSERT INTO study_sessions
        (subject_id, study_date, duration_hours, user_id)
        VALUES (%s,%s,%s,%s)""",
        (subject_id, study_date, duration_hours, user_id)
    )

    conn.commit()

    return redirect("/")


# ---------------- UPDATE STUDY SESSION ----------------
@app.route("/update_session/<int:session_id>", methods=["POST"])
def update_session(session_id):

    subject_id = request.form["subject_id"]
    study_date = request.form["study_date"]
    duration_hours = request.form["duration_hours"]
    user_id = session["user_id"]

    cur = conn.cursor()

    # Verify that the session belongs to the logged-in user
    cur.execute("SELECT user_id FROM study_sessions WHERE id=%s", (session_id,))
    session_owner = cur.fetchone()

    if not session_owner or session_owner[0] != user_id:
        return "Unauthorized: This session does not belong to you!", 403

    # Verify that the subject belongs to the logged-in user
    cur.execute("SELECT user_id FROM subjects WHERE id=%s", (subject_id,))
    subject_owner = cur.fetchone()

    if not subject_owner or subject_owner[0] != user_id:
        return "Unauthorized: This subject does not belong to you!", 403

    cur.execute(
        """UPDATE study_sessions 
        SET subject_id=%s, study_date=%s, duration_hours=%s 
        WHERE id=%s AND user_id=%s""",
        (subject_id, study_date, duration_hours, session_id, user_id)
    )

    conn.commit()

    return redirect("/")


# ---------------- DELETE STUDY SESSION ----------------
@app.route("/delete_session/<int:session_id>", methods=["POST"])
def delete_session(session_id):

    user_id = session["user_id"]

    cur = conn.cursor()

    # Verify that the session belongs to the logged-in user
    cur.execute("SELECT user_id FROM study_sessions WHERE id=%s", (session_id,))
    session_owner = cur.fetchone()

    if not session_owner or session_owner[0] != user_id:
        return "Unauthorized: This session does not belong to you!", 403

    # Delete the session
    cur.execute(
        "DELETE FROM study_sessions WHERE id=%s AND user_id=%s",
        (session_id, user_id)
    )

    conn.commit()

    return redirect("/")


# ---------------- POMODORO TIMER ----------------
@app.route("/pomodoro")
def pomodoro():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("pomodoro.html")


# ---------------- RUN APP ----------------
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
