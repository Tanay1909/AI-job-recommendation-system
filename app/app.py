from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, json, io, os

# ML imports
from src.ingestion import load_data
from src.preprocessing import clean_text
from src.feature_engineering import vectorize
from src.predict import recommend_jobs
from src.resume_parser import extract_text_from_pdf
from src.skill_extractor import extract_skills

# DB init
from app.database import init_db

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CREATE APP ----------------
app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- INIT DB ----------------
init_db()

# ---------------- LOAD MODEL ----------------
jobs = load_data("data/jobs.csv")
jobs['description'] = jobs['description'].apply(clean_text)
vectorizer, job_vectors = vectorize(jobs['description'])

# Store latest results for PDF
results_cache = []

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    global results_cache
    results_list = None
    skills = None

    if request.method == "POST":
        file = request.files.get("resume_file")

        if file:
            text = extract_text_from_pdf(file)
            cleaned = clean_text(text)
            skills = extract_skills(cleaned)

            results = recommend_jobs(skills, jobs, vectorizer, job_vectors)
            results_list = results.to_dict(orient="records")

            # Save for PDF
            results_cache = results_list

            # Save history
            if session.get("user"):
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                c.execute("INSERT INTO history VALUES(NULL,?,?,?)",
                          (session["user"], skills, json.dumps(results_list)))
                conn.commit()
                conn.close()

    return render_template(
        "index.html",
        results=results_list,
        skills=skills,
        user=session.get("user")
    )

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()

        if user:
            session["user"] = u
            return redirect("/")

    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES(NULL,?,?)", (u, p))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if not session.get("user"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE username=?", (session["user"],))
    data = c.fetchall()
    conn.close()

    return render_template("history.html", data=data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- DOWNLOAD PDF ----------------
@app.route("/download")
def download():
    global results_cache

    if not results_cache:
        return "No data to download"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Job Recommendation Report", styles['Title']))
    content.append(Spacer(1, 10))

    for job in results_cache:
        content.append(Paragraph(f"Job: {job['job_title']}", styles['Heading2']))
        content.append(Paragraph(f"Match: {job['match (%)']}%", styles['Normal']))
        content.append(Spacer(1, 10))

    doc.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="report.pdf",
        mimetype="application/pdf"
    )

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))