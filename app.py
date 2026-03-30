from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3, hashlib, os, json, re, requests
from functools import wraps

app = Flask(__name__)
app.secret_key = "skillgap_secret_2024"

DB_PATH = "data/skillgap.db"
GROQ_API_KEY = ""
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── Skill alias map ───────────────────────────────────────────────────────────
SKILL_ALIASES = {
    "js": "JavaScript", "javascript": "JavaScript", "es6": "JavaScript",
    "ts": "TypeScript", "typescript": "TypeScript",
    "py": "Python", "python3": "Python",
    "reactjs": "React", "react.js": "React",
    "nodejs": "Node.js", "node js": "Node.js", "node": "Node.js",
    "expressjs": "Express.js", "express": "Express.js",
    "mysql": "SQL", "postgresql": "SQL", "postgres": "SQL", "sqlite": "SQL",
    "mongodb": "MongoDB", "mongo": "MongoDB",
    "html5": "HTML", "css3": "CSS", "scss": "CSS", "sass": "CSS",
    "aws": "AWS", "amazon web services": "AWS",
    "k8s": "Kubernetes",
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "sklearn": "Scikit-learn", "scikit learn": "Scikit-learn",
    "rest": "REST APIs", "restful": "REST APIs", "rest api": "REST APIs",
    "ci/cd": "CI/CD", "cicd": "CI/CD", "github actions": "CI/CD", "jenkins": "CI/CD",
    "git": "Git", "github": "Git", "gitlab": "Git",
    "linux": "Linux", "ubuntu": "Linux",
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "nlp": "NLP", "natural language processing": "NLP",
    "power bi": "Power BI", "powerbi": "Power BI",
    "penetration testing": "Penetration Testing", "pentest": "Penetration Testing",
    "ethical hacking": "Ethical Hacking",
    "networking": "Networking", "tcp/ip": "Networking",
    "microservices": "Microservices",
    "terraform": "Terraform",
    "statistics": "Statistics",
    "data visualization": "Data Visualization",
    "mlops": "MLOps",
    "testing": "Testing", "unit testing": "Testing", "jest": "Testing", "pytest": "Testing",
    "android sdk": "Android SDK", "android": "Android SDK",
    "jetpack compose": "Jetpack Compose",
    "wireframing": "Wireframing", "prototyping": "Prototyping",
    "user research": "User Research",
    "design systems": "Design Systems",
    "accessibility": "Accessibility",
    "siem": "SIEM", "splunk": "SIEM",
    "cryptography": "Cryptography", "encryption": "Cryptography",
    "risk assessment": "Risk Assessment",
    "incident response": "Incident Response",
    "monitoring": "Monitoring", "prometheus": "Monitoring", "grafana": "Monitoring",
    "authentication": "Authentication", "oauth": "Authentication", "jwt": "Authentication",
    "adobe xd": "Adobe XD",
}

RESOURCES = {
    "Python": ["Python.org Official Tutorial (free)", "Automate the Boring Stuff (free book)", "CS50P on edX (free)"],
    "JavaScript": ["javascript.info (free)", "The Odin Project (free)", "freeCodeCamp JS Course"],
    "React": ["React Official Docs - react.dev", "Scrimba React Course (free tier)", "Full Stack Open (free)"],
    "Node.js": ["Node.js Official Docs", "The Odin Project NodeJS Path", "Full Stack Open (free)"],
    "SQL": ["SQLZoo (free interactive)", "Mode Analytics SQL Tutorial", "CS50 SQL on edX (free)"],
    "HTML": ["MDN Web Docs (free)", "freeCodeCamp Responsive Web Design", "The Odin Project Foundations"],
    "CSS": ["CSS-Tricks (free)", "Kevin Powell YouTube (free)", "freeCodeCamp CSS Course"],
    "Git": ["Pro Git Book (free)", "GitHub Learning Lab", "Atlassian Git Tutorials (free)"],
    "Docker": ["Docker Official Get Started Guide", "TechWorld with Nana Docker (YouTube)", "Play with Docker (free)"],
    "Kubernetes": ["Kubernetes Official Docs", "KodeKloud free tier", "TechWorld with Nana K8s (YouTube)"],
    "AWS": ["AWS Cloud Practitioner Essentials (free)", "AWS Free Tier + Official Docs", "freeCodeCamp AWS (YouTube)"],
    "Machine Learning": ["fast.ai (free)", "Andrew Ng ML Specialization (audit free)", "Kaggle Learn (free)"],
    "Deep Learning": ["fast.ai Deep Learning (free)", "d2l.ai (free book)", "Kaggle Intro to Deep Learning"],
    "TensorFlow": ["TensorFlow Official Tutorials", "DeepLearning.AI TensorFlow (audit free)", "Kaggle TF notebooks"],
    "PyTorch": ["PyTorch Official Tutorials", "fast.ai (uses PyTorch, free)", "Kaggle PyTorch notebooks"],
    "Scikit-learn": ["Scikit-learn Official Docs", "Kaggle ML courses (free)", "StatQuest YouTube (free)"],
    "Pandas": ["Pandas Official Docs", "Kaggle Pandas (free)", "Real Python Pandas tutorials"],
    "NumPy": ["NumPy Official Docs", "freeCodeCamp NumPy (YouTube)", "Kaggle NumPy exercises"],
    "Power BI": ["Microsoft Learn Power BI (free)", "Guy in a Cube YouTube (free)", "SQLBI free tutorials"],
    "Tableau": ["Tableau Public (free)", "Tableau e-Learning (free for students)", "Simplidata YouTube"],
    "Excel": ["Microsoft Excel free training", "ExcelJet shortcuts & formulas", "Chandoo.org (free)"],
    "Linux": ["The Linux Command Line (free book)", "OverTheWire Bandit wargame", "Linux Journey (free)"],
    "Bash": ["Bash Guide - mywiki.wooledge.org", "Ryan's Bash Scripting Tutorial (free)", "ShellCheck tool"],
    "CI/CD": ["GitHub Actions Official Docs", "Jenkins Official Docs", "TechWorld with Nana CI/CD (YouTube)"],
    "Terraform": ["Terraform Official Tutorials (free)", "HashiCorp Learn Platform", "freeCodeCamp Terraform (YouTube)"],
    "Figma": ["Figma Official YouTube Channel", "Figma for Beginners free course", "Coursera UI/UX (audit free)"],
    "MongoDB": ["MongoDB University (free)", "MongoDB Official Docs", "freeCodeCamp MongoDB (YouTube)"],
    "REST APIs": ["RESTful API Design by Microsoft", "Postman Learning Center (free)", "freeCodeCamp APIs course"],
    "Java": ["Java Programming MOOC (free)", "Codecademy Java (free tier)", "JetBrains Academy (free tier)"],
    "Kotlin": ["Kotlin Official Docs + Koans (free)", "Android Basics with Compose (free)", "JetBrains Academy Kotlin"],
    "Android SDK": ["Android Developers Official Docs", "Android Basics with Compose (free)", "Udacity Android Kotlin (free)"],
    "Firebase": ["Firebase Official Docs", "Fireship.io (YouTube, free)", "Google Codelabs Firebase (free)"],
    "Penetration Testing": ["TryHackMe (free tier)", "HackTheBox Academy (free tier)", "TCM Security free courses"],
    "Ethical Hacking": ["TryHackMe free rooms", "Cybrary (free tier)", "Professor Messer CompTIA (free)"],
    "Networking": ["Professor Messer CompTIA Network+ (free)", "Cisco Networking Basics (free)", "NetworkChuck YouTube"],
    "Statistics": ["StatQuest with Josh Starmer (YouTube)", "Khan Academy Statistics (free)", "Think Stats (free book)"],
    "Data Visualization": ["D3.js Official Docs", "Storytelling with Data (book)", "Kaggle Data Viz (free)"],
    "Cryptography": ["Cryptography I Coursera (audit free)", "Crypto101 (free book)", "Khan Academy Cryptography"],
    "Testing": ["pytest Official Docs", "freeCodeCamp Testing (YouTube)", "Test-Driven Development (book)"],
    "Redis": ["Redis University (free)", "Redis Official Docs", "TryRedis interactive (free)"],
    "NLP": ["Hugging Face Course (free)", "fast.ai NLP (free)", "Stanford CS224N (YouTube free)"],
    "MLOps": ["Made With ML (free)", "MLOps Zoomcamp (free)", "Evidently AI blog (free)"],
    "Microservices": ["Microservices.io (free)", "Sam Newman Microservices book", "freeCodeCamp Microservices (YouTube)"],
    "Authentication": ["OAuth 2.0 Simplified (free book)", "Auth0 Docs & Blog", "Web Dev Simplified YouTube"],
    "Monitoring": ["Prometheus Official Docs", "Grafana Official Docs", "TechWorld with Nana Monitoring (YouTube)"],
    "Jetpack Compose": ["Android Developers Compose Pathway (free)", "Google Codelabs Compose (free)", "Philipp Lackner YouTube"],
    "Wireframing": ["Figma Wireframing Guide (free)", "NN/g Wireframing article (free)", "Balsamiq Wireframing Basics"],
    "User Research": ["NN/g UX Research articles (free)", "Google UX Design Certificate (audit free)", "UX Mastery (free)"],
    "Design Systems": ["Design Systems Handbook (free)", "Figma Design Systems (YouTube)", "Atomic Design by Brad Frost (free)"],
    "Accessibility": ["WebAIM (free)", "MDN Accessibility Guide (free)", "Deque University (free tier)"],
    "SIEM": ["Splunk Free Training", "TryHackMe SOC Path (free tier)", "Cybrary SIEM (free tier)"],
    "Risk Assessment": ["NIST Cybersecurity Framework (free)", "ISACA free resources", "Cybrary Risk Management (free)"],
    "Incident Response": ["SANS Reading Room (free)", "TryHackMe Incident Response (free)", "Cybrary IR course (free)"],
    "Adobe XD": ["Adobe XD Official Tutorials", "Coursera UI/UX (audit free)", "YouTube: Adobe XD for Beginners"],
}

DEFAULT_RESOURCES = ["Search '[Skill] tutorial' on YouTube", "freeCodeCamp.org", "Official documentation"]
PRIORITY_MAP = {0: "High", 1: "High", 2: "Medium", 3: "Medium"}

# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'student'
    );
    CREATE TABLE IF NOT EXISTS job_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        skills TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_role_id INTEGER NOT NULL,
        resume_text TEXT,
        matched_skills TEXT,
        missing_skills TEXT,
        match_percentage REAL,
        roadmap TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(job_role_id) REFERENCES job_roles(id)
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM job_roles").fetchone()[0]
    if count == 0:
        roles = [
            ("Full Stack Developer", "Build end-to-end web applications",
             json.dumps(["HTML","CSS","JavaScript","React","Node.js","Python","SQL","REST APIs","Git","Docker"])),
            ("Data Analyst", "Analyze data and generate insights",
             json.dumps(["Python","SQL","Excel","Power BI","Tableau","Statistics","Pandas","NumPy","Data Visualization","Machine Learning"])),
            ("Machine Learning Engineer", "Design and deploy ML models",
             json.dumps(["Python","TensorFlow","PyTorch","Scikit-learn","SQL","Statistics","Deep Learning","Docker","MLOps","NumPy"])),
            ("DevOps Engineer", "Automate and manage infrastructure",
             json.dumps(["Linux","Docker","Kubernetes","CI/CD","AWS","Terraform","Bash","Python","Monitoring","Git"])),
            ("Backend Developer", "Build server-side applications",
             json.dumps(["Python","Node.js","SQL","REST APIs","Microservices","Docker","Git","Redis","Authentication","Testing"])),
            ("Android Developer", "Build Android mobile apps",
             json.dumps(["Java","Kotlin","Android SDK","Firebase","REST APIs","Git","Jetpack Compose","SQL","Testing","Python"])),
            ("UI/UX Designer", "Design user interfaces and experiences",
             json.dumps(["Figma","Wireframing","Prototyping","User Research","HTML","CSS","Design Systems","Accessibility","Adobe XD","JavaScript"])),
            ("Cybersecurity Analyst", "Protect systems and networks",
             json.dumps(["Networking","Linux","Python","Penetration Testing","SIEM","Bash","Cryptography","Ethical Hacking","Risk Assessment","Incident Response"])),
        ]
        db.executemany("INSERT INTO job_roles (title, description, skills) VALUES (?,?,?)", roles)
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        db.execute("INSERT OR IGNORE INTO users (name,email,password,role) VALUES (?,?,?,?)",
                   ("Admin","admin@skillgap.com", admin_pw, "admin"))
    db.commit()
    db.close()

# ── Groq AI analysis ──────────────────────────────────────────────────────────

def analyze_with_groq(resume_text, role_title, required_skills):
    prompt = f"""You are a resume skill analyzer. Extract skills from the resume and compare with required skills.

RESUME:
{resume_text}

REQUIRED SKILLS FOR "{role_title}":
{', '.join(required_skills)}

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "matched_skills": ["skills from required list found in resume"],
  "missing_skills": ["required skills NOT found in resume"],
  "match_percentage": 75,
  "skill_summary": "2-sentence assessment of the candidate",
  "roadmap": [
    {{"skill": "SkillName", "priority": "High", "resources": ["Resource 1", "Resource 2"], "estimated_weeks": 3}}
  ]
}}

Rules:
- matched_skills must only contain skills from the required list
- missing_skills = required skills not found in resume
- match_percentage = (matched / total required) * 100, as integer
- roadmap covers only missing skills ordered by priority (High first)
- resources should be specific free learning resources"""

    try:
        res = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 2000,
            },
            timeout=30
        )
        content = res.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except Exception as e:
        return None

# ── Fallback rule-based extraction ───────────────────────────────────────────

def extract_skills(text, required_skills):
    text_lower = text.lower()
    found = set()
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            found.add(canonical)
    for skill in required_skills:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
            found.add(skill)
    return list(found)

def build_roadmap(missing_skills):
    roadmap = []
    for i, skill in enumerate(missing_skills):
        priority = PRIORITY_MAP.get(i, "Low")
        weeks = 2 if priority == "High" else (3 if priority == "Medium" else 4)
        roadmap.append({
            "skill": skill,
            "priority": priority,
            "resources": RESOURCES.get(skill, DEFAULT_RESOURCES),
            "estimated_weeks": weeks
        })
    return roadmap

def generate_summary(match_pct, matched, missing, role_title):
    if match_pct >= 80:
        tone, tip = "strong", "You're well-prepared — polish the remaining gaps and you'll be competitive."
    elif match_pct >= 50:
        tone, tip = "moderate", "A focused 4-8 week sprint on the missing skills will make you job-ready."
    else:
        tone, tip = "early-stage", "Follow the roadmap step by step — consistent daily practice will get you there."
    top = ", ".join(matched[:3]) + ("..." if len(matched) > 3 else "") if matched else "none yet"
    return f"Your profile is a {tone} match for {role_title}. Strongest skills: {top}. {tip}"

# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip()
        pw = hashlib.sha256(request.form.get("password","").encode()).hexdigest()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email,pw)).fetchone()
        db.close()
        if user:
            session.update({"user_id": user["id"], "name": user["name"], "role": user["role"]})
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        pw = hashlib.sha256(request.form.get("password","").encode()).hexdigest()
        db = get_db()
        try:
            db.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (name,email,pw))
            db.commit(); db.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            db.close()
            return render_template("register.html", error="Email already registered")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    roles = db.execute("SELECT * FROM job_roles ORDER BY title").fetchall()
    analyses = db.execute(
        """SELECT a.*, j.title as role_title FROM analyses a
           JOIN job_roles j ON a.job_role_id=j.id
           WHERE a.user_id=? ORDER BY a.created_at DESC LIMIT 5""",
        (session["user_id"],)).fetchall()
    db.close()
    return render_template("dashboard.html", roles=roles, analyses=analyses)

@app.route("/api/analyze", methods=["POST"])
@login_required
def analyze():
    data = request.get_json()
    resume_text = data.get("resume_text","").strip()
    job_role_id = data.get("job_role_id")
    if not resume_text or not job_role_id:
        return jsonify({"error": "Resume text and job role required"}), 400

    db = get_db()
    role = db.execute("SELECT * FROM job_roles WHERE id=?", (job_role_id,)).fetchone()
    if not role:
        db.close()
        return jsonify({"error": "Job role not found"}), 404

    required = json.loads(role["skills"])

    # Try Groq AI first, fall back to rule-based
    result = analyze_with_groq(resume_text, role["title"], required)
    if result:
        matched = result.get("matched_skills", [])
        missing = result.get("missing_skills", [])
        pct = result.get("match_percentage", 0)
        roadmap = result.get("roadmap", [])
        summary = result.get("skill_summary", generate_summary(pct, matched, missing, role["title"]))
        # Enrich roadmap resources from local DB if missing
        for item in roadmap:
            if not item.get("resources"):
                item["resources"] = RESOURCES.get(item["skill"], DEFAULT_RESOURCES)
    else:
        # Fallback
        extracted = extract_skills(resume_text, required)
        matched = [s for s in required if s in extracted]
        missing = [s for s in required if s not in extracted]
        pct = round((len(matched) / len(required)) * 100) if required else 0
        roadmap = build_roadmap(missing)
        summary = generate_summary(pct, matched, missing, role["title"])

    db.execute(
        """INSERT INTO analyses (user_id,job_role_id,resume_text,matched_skills,missing_skills,match_percentage,roadmap)
           VALUES (?,?,?,?,?,?,?)""",
        (session["user_id"], job_role_id, resume_text,
         json.dumps(matched), json.dumps(missing), pct, json.dumps(roadmap)))
    db.commit(); db.close()

    return jsonify({"matched_skills": matched, "missing_skills": missing,
                    "match_percentage": pct, "skill_summary": summary,
                    "roadmap": roadmap, "role_title": role["title"],
                    "required_skills": required})

@app.route("/history")
@login_required
def history():
    db = get_db()
    analyses = db.execute(
        """SELECT a.*, j.title as role_title FROM analyses a
           JOIN job_roles j ON a.job_role_id=j.id
           WHERE a.user_id=? ORDER BY a.created_at DESC""",
        (session["user_id"],)).fetchall()
    db.close()
    return render_template("history.html", analyses=analyses)

@app.route("/history/<int:analysis_id>")
@login_required
def view_analysis(analysis_id):
    db = get_db()
    analysis = db.execute(
        """SELECT a.*, j.title as role_title, j.skills as role_skills FROM analyses a
           JOIN job_roles j ON a.job_role_id=j.id
           WHERE a.id=? AND a.user_id=?""",
        (analysis_id, session["user_id"])).fetchone()
    db.close()
    if not analysis:
        return redirect(url_for("history"))
    return render_template("view_analysis.html", analysis=analysis)

@app.route("/admin")
@login_required
@admin_required
def admin():
    db = get_db()
    roles = db.execute("SELECT * FROM job_roles ORDER BY title").fetchall()
    users = db.execute("SELECT id,name,email,role FROM users ORDER BY name").fetchall()
    db.close()
    return render_template("admin.html", roles=roles, users=users)

@app.route("/api/admin/roles", methods=["POST"])
@login_required
@admin_required
def add_role():
    data = request.get_json()
    skills = [s.strip() for s in data.get("skills","").split(",") if s.strip()]
    db = get_db()
    db.execute("INSERT INTO job_roles (title,description,skills) VALUES (?,?,?)",
               (data["title"], data.get("description",""), json.dumps(skills)))
    db.commit(); db.close()
    return jsonify({"success": True})

@app.route("/api/admin/roles/<int:role_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_role(role_id):
    db = get_db()
    db.execute("DELETE FROM job_roles WHERE id=?", (role_id,))
    db.commit(); db.close()
    return jsonify({"success": True})

@app.template_filter("fromjson")
def fromjson_filter(s):
    try: return json.loads(s)
    except: return []

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
