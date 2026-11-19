
from flask import Flask, render_template, request
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import fitz
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key")


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE USERS TABLE
def create_users_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# SKILLS LIST
skills_list = [
    "Python", "Java", "HTML", "CSS",
    "JavaScript", "SQL", "C", "C++",
    "React", "Flask", "Django",
    "Machine Learning", "Data Analysis",
    "Bootstrap", "Node.js", "MongoDB",
    "Excel", "Power BI", "NumPy", "Pandas",
    "Git", "GitHub", "PHP", "AWS",
    "Communication", "Problem Solving"
]


# JOB ROLE SKILLS
job_skills = {
    "Python Developer": [
        "Python", "SQL", "Flask", "Django",
        "NumPy", "Pandas", "Git"
    ],

    "Web Developer": [
        "HTML", "CSS", "JavaScript", "React",
        "Bootstrap", "Node.js", "MongoDB"
    ],

    "Java Developer": [
        "Java", "SQL", "HTML", "CSS",
        "Git", "Problem Solving"
    ],

    "Data Analyst": [
        "Python", "SQL", "Data Analysis",
        "Excel", "Power BI", "NumPy", "Pandas"
    ],

    "Software Engineer": [
        "Python", "Java", "SQL", "C++",
        "Git", "GitHub", "Problem Solving"
    ]
}


# JOB DESCRIPTIONS
job_descriptions = {
    "Python Developer": """
        Python programming, software development,
        backend development, database management,
        Flask, Django, data analysis and problem solving.
    """,

    "Web Developer": """
        Web development, HTML, CSS, JavaScript,
        responsive website design, React,
        Bootstrap, Node.js and MongoDB.
    """,

    "Java Developer": """
        Java programming, object oriented programming,
        SQL, software development, debugging
        and problem solving.
    """,

    "Data Analyst": """
        Data analysis, Python, SQL, Excel,
        Power BI, NumPy, Pandas and data visualization.
    """,

    "Software Engineer": """
        Software engineering, programming,
        Python, Java, SQL, Git, GitHub,
        software testing and problem solving.
    """
}


# LEARNING RECOMMENDATIONS
recommendations = {
    "Python": "Learn Python basics, functions and OOP.",
    "Java": "Learn Java basics, OOP and collections.",
    "HTML": "Learn HTML tags and page structure.",
    "CSS": "Learn CSS styling, Flexbox and Grid.",
    "JavaScript": "Learn JavaScript basics and DOM.",
    "SQL": "Practice SQL queries and database operations.",
    "React": "Learn React components, props and state.",
    "Flask": "Learn Flask routing and API development.",
    "Django": "Learn Django models, views and templates.",
    "Machine Learning": "Learn ML basics and model training.",
    "Data Analysis": "Practice Pandas, NumPy and data visualization.",
    "C": "Learn C programming and pointers.",
    "C++": "Learn C++ basics and object-oriented programming.",
    "Bootstrap": "Learn Bootstrap grid system and responsive design.",
    "Node.js": "Learn Node.js, npm and backend development.",
    "MongoDB": "Learn MongoDB queries and database management.",
    "Excel": "Practice Excel formulas, charts and pivot tables.",
    "Power BI": "Learn Power BI dashboards and data visualization.",
    "NumPy": "Learn NumPy arrays and numerical operations.",
    "Pandas": "Learn Pandas for data cleaning and analysis.",
    "Git": "Learn Git commands and version control.",
    "GitHub": "Practice repositories, commits and collaboration.",
    "PHP": "Learn PHP syntax and server-side programming.",
    "AWS": "Learn AWS cloud fundamentals and core services.",
    "Communication": "Improve communication and presentation skills.",
    "Problem Solving": "Practice logical thinking and coding problems."
}


# NLP SIMILARITY FUNCTION
def calculate_nlp_similarity(resume_text, job_role, required_skills):

    job_description = job_descriptions.get(job_role, "")

    job_profile = (
        job_role + " " +
        " ".join(required_skills) + " " +
        job_description
    )

    try:
        vectorizer = TfidfVectorizer(stop_words="english")

        tfidf_matrix = vectorizer.fit_transform([
            resume_text,
            job_profile
        ])

        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2]
        )[0][0]

        return round(similarity * 100)

    except ValueError:
        return 0


# REGISTRATION ROUTE
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )

            conn.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("This email is already registered.")

        finally:
            conn.close()

    return render_template("register.html")


# LOGIN ROUTE
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash("Login successful!")
            return redirect(url_for("dashboard"))

        else:
            flash("Invalid email or password.")

    return render_template("login.html")


# DASHBOARD ROUTE
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    return render_template("dashboard.html")


# LOGOUT ROUTE
@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out successfully.")

    return redirect(url_for("login"))

@app.route("/analyzer")
def analyzer():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")

# ABOUT US ROUTE
@app.route("/about")
def about():

    return render_template("about.html")


# HOME ROUTE
@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("register"))

# ANALYZE RESUME ROUTE
@app.route("/analyze", methods=["POST"])
def analyze():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Baaki existing code yahin rahega

    resume = request.files.get("resume")
    job_role = request.form.get("job_role")

    if not resume or resume.filename == "":
        return "Please upload your resume."

    if not job_role:
        return "Please select a job role."

    if job_role not in job_skills:
        return "Please select a valid job role."

    if not resume.filename.lower().endswith(".pdf"):
        return "Please upload a PDF file."

    try:
        pdf_document = fitz.open(
            stream=resume.read(),
            filetype="pdf"
        )

        resume_text = ""

        for page in pdf_document:
            resume_text += page.get_text()

        pdf_document.close()

    except Exception:
        return "Unable to read this PDF. Please upload a valid PDF resume."

    resume_indicators = [
        "technical skills",
        "skills",
        "experience",
        "work experience",
        "projects",
        "career objective",
        "professional summary",
        "education",
        "email",
        "phone"
    ]

    matched_indicators = sum(
        1 for word in resume_indicators
        if word in resume_text.lower()
    )

    if matched_indicators < 2:
        return "This PDF does not appear to be a resume. Please upload your resume."

    # EXTRACT SKILLS
    found_skills = []

    for skill in skills_list:

        pattern = (
            r'(?<![A-Za-z0-9])'
            + re.escape(skill)
            + r'(?![A-Za-z0-9+#])'
        )

        if re.search(pattern, resume_text, re.IGNORECASE):
            found_skills.append(skill)

    # GET REQUIRED SKILLS
    required_skills = job_skills.get(job_role, [])

    # FIND MISSING SKILLS
    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in
        [s.lower() for s in found_skills]
    ]

    # CALCULATE SKILL MATCH PERCENTAGE
    if required_skills:
        match_percentage = round(
            (len(required_skills) - len(missing_skills))
            / len(required_skills) * 100
        )
    else:
        match_percentage = 0

    # CALCULATE NLP SIMILARITY
    nlp_match_percentage = calculate_nlp_similarity(
        resume_text,
        job_role,
        required_skills
    )

    # CREATE LEARNING PLAN
    learning_plan = []

    for skill in missing_skills:

        suggestion = recommendations.get(
            skill,
            "Practice this skill with a beginner project."
        )

        learning_plan.append({
            "skill": skill,
            "suggestion": suggestion
        })

    # SHOW RESULT PAGE
    return render_template(
        "result.html",
        job_role=job_role,
        found_skills=found_skills,
        required_skills=required_skills,
        missing_skills=missing_skills,
        match_percentage=match_percentage,
        nlp_match_percentage=nlp_match_percentage,
        learning_plan=learning_plan
    )



# INITIALIZE DATABASE
create_users_table()


# RUN APPLICATION
if __name__ == "__main__":
    app.run(debug=True)

