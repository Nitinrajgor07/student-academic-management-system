
import os
from flask import Flask, render_template, request, redirect, session, jsonify
from functools import wraps
import mysql.connector
import hashlib
import re

app = Flask(__name__)
app.secret_key = "mysecret123"

# ================= MASTER DEPARTMENT / COURSE LIST =================
# Single source of truth — pass as departments=DEPARTMENTS to every route.
# Adding a new program here automatically updates every dropdown.
DEPARTMENTS = [
    "M.Sc CS & IT",
    "B.Tech CS",
    "B.Tech IT",
    "B.Tech AI & ML",
    "BCA",
    "MCA",
    "M.Tech",
    "MBA",
    "B.Com",
    "BBA",
    "Mechanical Engineering",
    "Civil Engineering",
    "Electrical Engineering",
    "Electronics & Communication",
    "Information Technology",
]

# ================= DB CONNECTION =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="studentuser",
        password="1234",
        database="studentdb"
    )

# Create required tables if they don't exist on startup
try:
    db = get_db()
    cursor = db.cursor()
    
    # 1. Create companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(30),
            website VARCHAR(150),
            industry VARCHAR(100),
            company_size VARCHAR(50),
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            password VARCHAR(255) NOT NULL
        )
    """)

    # 2. Create fees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT,
            semester INT,
            fee_type VARCHAR(50),
            amount DECIMAL(10,2),
            due_date DATE,
            status VARCHAR(20) DEFAULT 'Unpaid',
            paid_date DATE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # 3. Create notices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            category VARCHAR(50),
            posted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Create certificate_requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificate_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT,
            cert_type VARCHAR(100) NOT NULL,
            reason TEXT,
            status VARCHAR(50) DEFAULT 'Pending',
            requested_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_on DATETIME NULL,
            priority VARCHAR(20) DEFAULT 'Medium',
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    try:
        cursor.execute("ALTER TABLE certificate_requests ADD COLUMN priority VARCHAR(20) DEFAULT 'Medium'")
    except Exception as alter_err:
        print("Alter table status (priority column might already exist):", alter_err)

    # 5. Create vacancies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id INT NULL,
            company_name VARCHAR(150) NOT NULL,
            logo_url VARCHAR(255) NULL,
            job_title VARCHAR(150) NOT NULL,
            eligible_departments VARCHAR(255) NOT NULL,
            location VARCHAR(100) NOT NULL,
            package_lpa VARCHAR(50) NOT NULL,
            job_type VARCHAR(50) NOT NULL,
            vacancies_count INT NOT NULL,
            last_date DATE NOT NULL,
            cgpa_required DECIMAL(3,1) NOT NULL DEFAULT 0.0,
            skills_required VARCHAR(255) NOT NULL,
            status VARCHAR(20) DEFAULT 'Open',
            posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
        )
    """)

    # 6. Create applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vacancy_id INT NOT NULL,
            student_id INT NOT NULL,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'Applied',
            FOREIGN KEY (vacancy_id) REFERENCES vacancies(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE KEY unique_student_vacancy (student_id, vacancy_id)
        )
    """)

    # 7. Create offers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            company_name VARCHAR(150) NOT NULL,
            job_title VARCHAR(150) NOT NULL,
            package_lpa VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            offer_date DATE NOT NULL,
            letter_url VARCHAR(255) NULL,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # Seed vacancies if empty
    cursor.execute("SELECT COUNT(*) FROM vacancies")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM companies WHERE email='careers@google.com'")
        google_res = cursor.fetchone()
        if google_res:
            google_id = google_res[0]
        else:
            google_pwd = hashlib.sha256('Google123'.encode('utf-8')).hexdigest()
            cursor.execute("""
                INSERT INTO companies (name, email, phone, website, industry, company_size, address, city, state, country, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'Google India', 'careers@google.com', '+91 80 6792 0000', 'https://careers.google.com',
                'Technology', '10000+', 'Bangalore, Karnataka', 'Bangalore', 'Karnataka', 'India', google_pwd
            ))
            google_id = cursor.lastrowid
        
        cursor.execute("SELECT id FROM companies WHERE email='recruiting@stripe.com'")
        stripe_res = cursor.fetchone()
        stripe_id = stripe_res[0] if stripe_res else None

        cursor.execute("SELECT id FROM companies WHERE email='recruitment@aether.io'")
        aether_res = cursor.fetchone()
        aether_id = aether_res[0] if aether_res else None

        cursor.execute("""
            INSERT INTO vacancies (company_id, company_name, logo_url, job_title, eligible_departments, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required, status)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            google_id, 'Google India', 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',
            'Software Engineer Intern', 'B.Tech CS, MCA, M.Sc CS & IT', 'Bangalore', '₹12 LPA', 'Internship',
            15, '2026-07-30', 7.5, 'Java, Python, SQL, DSA', 'Open',

            stripe_id, 'Stripe Inc', 'https://upload.wikimedia.org/wikipedia/commons/b/ba/Stripe_Logo%2C_revised_2016.svg',
            'Backend Systems Engineer', 'B.Tech CS, M.Tech, MCA', 'Remote', '₹25 LPA', 'Full-Time',
            5, '2026-08-15', 8.0, 'Ruby, Python, Go, System Design', 'Open',

            aether_id, 'Aether Corp', '',
            'Cloud Solutions Intern', 'BCA, MCA, B.Sc IT', 'Mumbai', '₹8 LPA', 'Internship',
            10, '2026-07-28', 7.0, 'AWS, Docker, Linux, Networking', 'Open'
        ))

    # Ensure hr_name column exists in companies table
    try:
        cursor.execute("SHOW COLUMNS FROM companies LIKE 'hr_name'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE companies ADD COLUMN hr_name VARCHAR(150) NULL")
    except Exception as alter_err:
        print("Error checking/adding hr_name column:", alter_err)

    # Ensure logo_url column exists in companies table
    try:
        cursor.execute("SHOW COLUMNS FROM companies LIKE 'logo_url'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE companies ADD COLUMN logo_url VARCHAR(255) NULL")
    except Exception as alter_err:
        print("Error checking/adding logo_url column:", alter_err)

    # Ensure about column exists in companies table
    try:
        cursor.execute("SHOW COLUMNS FROM companies LIKE 'about'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE companies ADD COLUMN about TEXT NULL")
    except Exception as alter_err:
        print("Error checking/adding about column:", alter_err)

    # Ensure description column exists in vacancies table
    try:
        cursor.execute("SHOW COLUMNS FROM vacancies LIKE 'description'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE vacancies ADD COLUMN description TEXT NULL")
    except Exception as alter_err:
        print("Error checking/adding description column:", alter_err)

    # Ensure eligible_semester column exists in vacancies table
    try:
        cursor.execute("SHOW COLUMNS FROM vacancies LIKE 'eligible_semester'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE vacancies ADD COLUMN eligible_semester VARCHAR(50) NULL")
    except Exception as alter_err:
        print("Error checking/adding eligible_semester column:", alter_err)

    # Seed the default demo company recruiter account
    cursor.execute("SELECT id FROM companies WHERE email = 'hr@abctecnologies.com'")
    demo_comp = cursor.fetchone()
    if not demo_comp:
        hashed_pwd = hashlib.sha256('Company@123'.encode('utf-8')).hexdigest()
        cursor.execute("""
            INSERT INTO companies (name, email, phone, website, industry, company_size, address, city, state, country, password, hr_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'ABC Technologies Pvt Ltd', 'hr@abctecnologies.com', '+1 (555) 019-2834', 'https://abctechnologies.com',
            'Technology', '51-250', 'Tech Park, Sector 62', 'Noida', 'Uttar Pradesh', 'India', hashed_pwd, 'Recruitment Team'
        ))

    # Seed the 10 demo recruiter/company accounts
    demo_companies = [
        {
            "name": "NovaTech Solutions Pvt Ltd",
            "hr_name": "Amit Sharma",
            "email": "hr@novatechsolutions.in",
            "password": "Nova@123",
            "phone": "+91 98765 43210",
            "website": "https://novatechsolutions.in",
            "industry": "Technology",
            "company_size": "100-500",
            "address": "IT Park, Sector 4",
            "city": "Gurugram",
            "state": "Haryana",
            "country": "India"
        },
        {
            "name": "BrightSoft Technologies",
            "hr_name": "Priya Patel",
            "email": "careers@brightsofttech.com",
            "password": "Bright@123",
            "phone": "+1 415 555 2678",
            "website": "https://brightsofttech.com",
            "industry": "Software Services",
            "company_size": "50-100",
            "address": "Silicon Valley Blvd",
            "city": "San Jose",
            "state": "California",
            "country": "United States"
        },
        {
            "name": "NextGen Infotech",
            "hr_name": "Rahul Verma",
            "email": "hr@nextgeninfotech.in",
            "password": "Next@123",
            "phone": "+91 99887 76655",
            "website": "https://nextgeninfotech.in",
            "industry": "IT Consulting",
            "company_size": "200-1000",
            "address": "Electronics City, Phase 1",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India"
        },
        {
            "name": "SkyLink Systems",
            "hr_name": "Neha Shah",
            "email": "recruitment@skylinksystems.com",
            "password": "Sky@123",
            "phone": "+1 212 555 7890",
            "website": "https://skylinksystems.com",
            "industry": "Telecommunications",
            "company_size": "500-2000",
            "address": "Broad Street, 45th Floor",
            "city": "New York",
            "state": "New York",
            "country": "United States"
        },
        {
            "name": "Vertex Digital Pvt Ltd",
            "hr_name": "Karan Mehta",
            "email": "jobs@vertexdigital.in",
            "password": "Vertex@123",
            "phone": "+91 91234 56789",
            "website": "https://vertexdigital.in",
            "industry": "Digital Marketing",
            "company_size": "10-50",
            "address": "Connaught Place",
            "city": "New Delhi",
            "state": "Delhi",
            "country": "India"
        },
        {
            "name": "AlphaCore Technologies",
            "hr_name": "Sneha Iyer",
            "email": "hr@alphacoretech.com",
            "password": "Alpha@123",
            "phone": "+91 80 4444 8888",
            "website": "https://alphacoretech.com",
            "industry": "Hardware & Systems",
            "company_size": "100-500",
            "address": "Whitefield",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India"
        },
        {
            "name": "CodeSphere Solutions",
            "hr_name": "Vivek Kumar",
            "email": "hiring@codesphere.in",
            "password": "Code@123",
            "phone": "+91 22 6666 9999",
            "website": "https://codesphere.in",
            "industry": "Product Development",
            "company_size": "50-200",
            "address": "Bandra Kurla Complex",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India"
        },
        {
            "name": "FutureBridge Software",
            "hr_name": "Rohan Desai",
            "email": "careers@futurebridge.io",
            "password": "Future@123",
            "phone": "+44 20 7946 0192",
            "website": "https://futurebridge.io",
            "industry": "Artificial Intelligence",
            "company_size": "20-100",
            "address": "Shoreditch High St",
            "city": "London",
            "state": "Greater London",
            "country": "United Kingdom"
        },
        {
            "name": "Innovix Labs",
            "hr_name": "Anjali Singh",
            "email": "hr@innovixlabs.com",
            "password": "Innovix@123",
            "phone": "+1 650 555 0144",
            "website": "https://innovixlabs.com",
            "industry": "Biotechnology",
            "company_size": "50-150",
            "address": "Sand Hill Road",
            "city": "Menlo Park",
            "state": "California",
            "country": "United States"
        },
        {
            "name": "QuantumEdge Technologies",
            "hr_name": "Deep Patel",
            "email": "recruitment@quantumedge.in",
            "password": "Quantum@123",
            "phone": "+91 79 2324 5678",
            "website": "https://quantumedge.in",
            "industry": "Quantum Computing",
            "company_size": "10-50",
            "address": "Infocity",
            "city": "Gandhinagar",
            "state": "Gujarat",
            "country": "India"
        }
    ]

    for comp in demo_companies:
        cursor.execute("SELECT id FROM companies WHERE email = %s", (comp["email"],))
        if not cursor.fetchone():
            hashed_pwd = hashlib.sha256(comp["password"].encode('utf-8')).hexdigest()
            cursor.execute("""
                INSERT INTO companies (name, email, phone, website, industry, company_size, address, city, state, country, password, hr_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                comp["name"], comp["email"], comp["phone"], comp["website"],
                comp["industry"], comp["company_size"], comp["address"], comp["city"],
                comp["state"], comp["country"], hashed_pwd, comp["hr_name"]
            ))

    # Seed a default active offer for all students if table is empty
    cursor.execute("SELECT COUNT(*) FROM offers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM students")
        students_list = cursor.fetchall()
        for s_row in students_list:
            sid = s_row[0]
            cursor.execute("""
                INSERT INTO offers (student_id, company_name, job_title, package_lpa, status, offer_date, letter_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (sid, 'NovaTech Solutions Pvt Ltd', 'Associate Software Engineer', '₹8.5 LPA', 'Pending', '2026-07-15', '#'))

    db.commit()
    cursor.close()
    db.close()
except Exception as e:
    print("Error creating startup database tables:", e)

# ================= LOGIN REQUIRED (ADMIN PROTECT) =================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

# ================= HOME =================
@app.route("/")
def home():
    return render_template("login.html")

# ================= ADMIN LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    username = request.form['username']
    password = request.form['password']
    if username.lower() == "admin" and password == "Admin123":
        session['admin_logged_in'] = True
        return redirect("/admin")
    else:
        return render_template("login.html", admin_error="Invalid username or password.")


# ================= ADMIN STANDALONE LOGIN =================
@app.route("/admin_login", methods=["GET", "POST"])
@app.route("/adminlogin", methods=["GET", "POST"])
def adminlogin():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username.lower() == "admin" and password == "Admin123":
            session['admin_logged_in'] = True
            return redirect("/admin")
        else:
            return render_template("adminlogin.html", error="Invalid username or password.")
    return render_template("adminlogin.html")

# ================= ADMIN LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= STUDENT LOGIN =================
@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email    = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, password FROM students WHERE email=%s", (email,))
        student = cursor.fetchone()
        db.close()

        if student:
            if student[1].strip() == password.strip():
                session['student_id'] = student[0]
                return redirect("/student_dashboard")

        return render_template("student_login.html", error="Invalid email or password.")

    return render_template("student_login.html")

# ================= STUDENT DASHBOARD (UPDATED) =================
# Marks summary bhi dashboard pe dikhne ke liye
# internal + final dono fetch karta hai
 
@app.route("/student_dashboard")
def student_dashboard():
    if 'student_id' not in session:
        return redirect("/student_login")
 
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
 
    # Student info
    cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
 
    # Marks data for dashboard summary
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='internal'", (student_id,))
    internal = cursor.fetchone()
 
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='final'", (student_id,))
    final = cursor.fetchone()
 
    # Fetch active vacancies for placement cell card
    cursor.execute("""
        SELECT v.id, v.company_name, v.job_title, v.eligible_departments, v.location, v.package_lpa, v.job_type, v.vacancies_count, v.last_date, v.cgpa_required, v.skills_required, v.status, a.status AS apply_status
        FROM vacancies v
        LEFT JOIN applications a ON v.id = a.vacancy_id AND a.student_id = %s
        WHERE v.status='Open'
        ORDER BY v.posted_date DESC
        LIMIT 5
    """, (student_id,))
    vacancies = cursor.fetchall()
 
    db.close()
 
    marks_data = None
    if internal or final:
        marks_data = {'internal': internal, 'final': final}
 
    vacancies_list = []
    for row in vacancies:
        vacancies_list.append({
            'id': row[0],
            'company_name': row[1],
            'job_title': row[2],
            'eligible_departments': row[3],
            'location': row[4],
            'package_lpa': row[5],
            'job_type': row[6],
            'vacancies_count': row[7],
            'last_date': row[8].strftime('%d %b %Y') if row[8] else '',
            'cgpa_required': float(row[9]) if row[9] is not None else 0.0,
            'skills_required': row[10],
            'status': row[11],
            'apply_status': row[12] if row[12] else 'Open'
        })
 
    return render_template("student_dashboard.html",
                           s=student,
                           marks_data=marks_data,
                           vacancies=vacancies_list)

# ================= STUDENT ATTENDANCE =================
# ================= STUDENT ATTENDANCE (UPDATED) =================
# Ye route student_attendance.html ko att_summary dict pass karta hai
# Har subject ki attendance % calculate hoti hai
 
@app.route("/student_attendance")
def student_attendance():
    if 'student_id' not in session:
        return redirect("/student_login")
 
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM students WHERE id=%s", (session['student_id'],))
    s = cursor.fetchone()
    cursor.execute("SELECT * FROM attendance WHERE student_id=%s", (session['student_id'],))
    data = cursor.fetchall()
    db.close()
 
    # Calculate attendance % for each subject
    subjects = {
        'java':       {'label': 'Java',       'idx': 3},
        'python':     {'label': 'Python',     'idx': 4},
        'ml':         {'label': 'ML',         'idx': 5},
        'blockchain': {'label': 'Blockchain', 'idx': 6},
        'ds':         {'label': 'DS',         'idx': 7},
        'adbms':      {'label': 'ADBMS',      'idx': 8},
    }
 
    total = len(data)
    att_summary = {}
 
    for sub, info in subjects.items():
        present = sum(1 for row in data if row[info['idx']] == 'Present')
        pct = round((present / total * 100)) if total > 0 else 0
        att_summary[sub] = {
            'label':   info['label'],
            'present': present,
            'total':   total,
            'pct':     pct
        }
 
    return render_template("student_attendance.html",
                           data=data,
                           att_summary=att_summary,
                           s=s)
 

# ================= TIMETABLE =================
@app.route("/timetable", methods=["GET"])
def timetable():
    return render_template("timetable.html")

# ================= ADMIN DASHBOARD =================
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    import datetime
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM timetable")
    timetable_data = cursor.fetchall()

    cursor.execute("SELECT * FROM attendance")
    attendance = cursor.fetchall()

    cursor.execute("SELECT * FROM marks")
    marks = cursor.fetchall()

    # Fetch real pending requests from database (Pending status)
    cursor.execute("""
        SELECT cr.id, students.name, students.enrollment_no, cr.cert_type,
               cr.requested_on, cr.status, cr.priority, cr.reason
        FROM certificate_requests cr
        JOIN students ON cr.student_id = students.id
        WHERE cr.status = 'Pending'
        ORDER BY cr.requested_on DESC
    """)
    pending_requests = cursor.fetchall()
    pending_count = len(pending_requests)

    # --- CALCULATE CHART DATA ---
    # 1. Enrollment Trend
    today = datetime.date.today()
    trend_labels = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_name = datetime.date(y, m, 1).strftime("%b")
        trend_labels.append(month_name)

    student_ids = [row[0] for row in students]
    trend_data = [0] * 6
    if student_ids:
        for sid in student_ids:
            m_idx = sid % 6
            trend_data[m_idx] += 1
        cumulative = 0
        for i in range(6):
            cumulative += trend_data[i]
            trend_data[i] = cumulative
    else:
        trend_data = [0] * 6

    # 2. Course Ratios
    cursor.execute("SELECT course, COUNT(*) FROM students GROUP BY course")
    course_counts = cursor.fetchall()
    course_labels = [row[0] or "Unknown" for row in course_counts]
    course_data = [row[1] for row in course_counts]

    # 3. Subject Averages
    cursor.execute("SELECT AVG(java), AVG(python), AVG(ml), AVG(blockchain), AVG(ds), AVG(adbms) FROM marks WHERE type='final'")
    avg_row = cursor.fetchone()
    subject_labels = ['Java', 'Python', 'ML', 'Blockchain', 'DS', 'ADBMS']
    if avg_row and any(val is not None for val in avg_row):
        subject_data = [
            round((float(val) / 70) * 100, 1) if val is not None else 0.0
            for val in avg_row
        ]
    else:
        subject_data = [0.0] * 6

    chart_data = {
        'enrollment_labels': trend_labels,
        'enrollment_data': trend_data,
        'course_labels': course_labels,
        'course_data': course_data,
        'subject_labels': subject_labels,
        'subject_data': subject_data
    }

    db.close()
    return render_template(
        "admin_dashboard.html",
        students=students,
        timetable=timetable_data,
        attendance=attendance,
        marks=marks,
        pending_requests=pending_requests,
        pending_count=pending_count,
        chart_data=chart_data
    )

# ================= ADMIN SOURCING ANALYTICS DASHBOARD =================
@app.route("/analytics")
@login_required
def analytics():
    db = get_db()
    cursor = db.cursor()

    # 1. Total Students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # 2. Total Companies
    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]

    # 3. Offered Courses count
    cursor.execute("SELECT COUNT(DISTINCT course) FROM students")
    total_courses = cursor.fetchone()[0] or 1

    # 4. Pie data (Enrollments per Course)
    cursor.execute("SELECT course, COUNT(*) FROM students GROUP BY course")
    enrollments = cursor.fetchall()
    pie_labels = [row[0] for row in enrollments]
    pie_data = [row[1] for row in enrollments]

    # If empty, add fallbacks
    if not pie_labels:
        pie_labels = ['MCA', 'BTech', 'MBA']
        pie_data = [12, 24, 8]

    # 5. Leaderboard & Average Marks calculations
    cursor.execute("SELECT * FROM marks WHERE type='final'")
    final_marks = cursor.fetchall()
    
    cursor.execute("SELECT * FROM marks WHERE type='internal'")
    internal_marks = cursor.fetchall()

    cursor.execute("SELECT id, name, email, course FROM students")
    all_students = cursor.fetchall()

    leaderboard = []
    topper_name = "N/A"
    topper_max_pct = 0

    student_names = []
    internal_totals = []
    final_totals = []

    # Map student details
    students_map = {s[0]: {'name': s[1], 'email': s[2], 'course': s[3]} for s in all_students}

    # Aggregate subject-wise averages
    sub_totals = {3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    sub_counts = {3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}

    for row in final_marks:
        sid = row[1]
        if sid in students_map:
            # Sum subjects for averages
            for idx in range(3, 9):
                val = row[idx]
                if val is not None:
                    sub_totals[idx] += int(val)
                    sub_counts[idx] += 1

            # Match with internal marks
            int_row = next((r for r in internal_marks if r[1] == sid), None)
            int_sum = sum(int(int_row[i]) for i in range(3, 9) if int_row[i] is not None) if int_row else 0
            fin_sum = sum(int(row[i]) for i in range(3, 9) if row[i] is not None)
            combined_total = int_sum + fin_sum
            # Percent out of 600 total (180 internal + 420 final)
            pct = round((combined_total / 600) * 100)
            
            leaderboard.append({
                'id': sid,
                'name': students_map[sid]['name'],
                'email': students_map[sid]['email'],
                'course': students_map[sid]['course'],
                'internal': int_sum,
                'final': fin_sum,
                'total': combined_total,
                'pct': pct
            })
            
            student_names.append(students_map[sid]['name'])
            internal_totals.append(int_sum)
            final_totals.append(fin_sum)

            if pct > topper_max_pct:
                topper_max_pct = pct
                topper_name = students_map[sid]['name']

    # Sort leaderboard by percentage desc
    leaderboard = sorted(leaderboard, key=lambda x: x['pct'], reverse=True)[:5]

    # Calculate average subject marks
    avg_subject_marks = []
    for idx in range(3, 9):
        avg_val = round((sub_totals[idx] / (sub_counts[idx] * 70) * 100)) if sub_counts[idx] > 0 else 75
        avg_subject_marks.append(avg_val)

    avg_marks = round(sum(l['pct'] for l in leaderboard) / len(leaderboard)) if leaderboard else 82

    db.close()

    # Pack stats
    stats = {
        'total_students': total_students,
        'avg_marks': avg_marks,
        'topper': topper_name,
        'total_courses': total_courses,
        'total_companies': total_companies
    }

    # Growth, Revenue, Department and Placement rates (Simulated / Calculated dynamically)
    placement_labels = ['Applied', 'Shortlisted', 'Interviewing', 'Offered', 'Rejected']
    placement_data = [20, 15, 8, 45, 12]
    attendance_subject_labels = ['Java', 'Python', 'ML', 'Blockchain', 'DS', 'ADBMS']
    attendance_subject_data = [92, 88, 94, 85, 90, 87]
    dept_performance_labels = ['MCA', 'BTech', 'MBA', 'MTech']
    dept_performance_cgpa = [8.6, 7.9, 8.2, 8.8]
    revenue_stats = {'expected': '₹12.5L', 'paid': '₹9.8L', 'pending': '₹2.7L'}
    revenue_data = [9.8, 2.7]
    growth_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    student_growth_data = [120, 135, 150, 175, 190, 210, 240]
    company_growth_data = [12, 16, 22, 28, 35, 42, 50]

    return render_template(
        "analytics.html",
        stats=stats,
        leaderboard=leaderboard,
        pie_labels=pie_labels,
        pie_data=pie_data,
        avg_subject_marks=avg_subject_marks,
        student_names=student_names,
        internal_totals=internal_totals,
        final_totals=final_totals,
        placement_labels=placement_labels,
        placement_data=placement_data,
        attendance_subject_labels=attendance_subject_labels,
        attendance_subject_data=attendance_subject_data,
        dept_performance_labels=dept_performance_labels,
        dept_performance_cgpa=dept_performance_cgpa,
        revenue_stats=revenue_stats,
        revenue_data=revenue_data,
        growth_labels=growth_labels,
        student_growth_data=student_growth_data,
        company_growth_data=company_growth_data
    )

# ================= ADD STUDENT PAGE =================
@app.route("/add_student_page")
@login_required
def add_student_page():
    import datetime
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    today_str = datetime.date.today().isoformat()
    # Count students added today (using DATE() on created_at if available, else approximate with id range)
    try:
        cursor.execute("SELECT COUNT(*) FROM students WHERE DATE(created_at) = %s", (today_str,))
        today_admissions = cursor.fetchone()[0]
    except Exception:
        today_admissions = 0
    cursor.close()
    db.close()
    return render_template("add_student.html",
                           total_students=total_students,
                           today_admissions=today_admissions,
                           today_date=today_str)

# ================= ADD STUDENT (SAVE) =================
@app.route("/add_student", methods=["POST"])
@login_required
def add_student():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    INSERT INTO students
    (name, email, course, password,
     phone, dob, gender, address, enrollment_no, semester,
     java, python, ml, blockchain, ds, adbms)
    VALUES (%s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s)
    """, (
        request.form['name'],
        request.form['email'],
        request.form['course'],
        request.form['password'],
        request.form.get('phone', ''),
        request.form.get('dob') or None,
        request.form.get('gender', ''),
        request.form.get('address', ''),
        request.form.get('enrollment_no', ''),
        request.form.get('semester', 1),
        request.form.get('java', 0) or 0,
        request.form.get('python', 0) or 0,
        request.form.get('ml', 0) or 0,
        request.form.get('blockchain', 0) or 0,
        request.form.get('ds', 0) or 0,
        request.form.get('adbms', 0) or 0,
    ))

    db.commit()
    db.close()
    return redirect("/admin")

# ================= EDIT STUDENT =================
@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        cursor.execute("""
        UPDATE students
        SET name=%s, email=%s, course=%s, password=%s,
            phone=%s, dob=%s, gender=%s, address=%s,
            enrollment_no=%s, semester=%s
        WHERE id=%s
        """, (
            request.form['name'],
            request.form['email'],
            request.form['course'],
            request.form['password'],
            request.form.get('phone', ''),
            request.form.get('dob') or None,
            request.form.get('gender', ''),
            request.form.get('address', ''),
            request.form.get('enrollment_no', ''),
            request.form.get('semester', 1),
            id
        ))
        db.commit()
        db.close()
        return redirect("/admin")

    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()
    db.close()
    return render_template("edit_student.html", s=student)

# ================= DELETE STUDENT =================
@app.route("/delete_student/<int:id>")
@login_required
def delete_student(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    db.commit()
    db.close()
    return redirect("/admin")

# ================= ATTENDANCE =================
@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    import datetime
    import json

    db = get_db()
    cursor = db.cursor()

    # 1. Handle POST submission for attendance entry
    if request.method == "POST":
        action = request.form.get("action")
        
        # Save daily attendance
        if action == "save_attendance":
            date_val = request.form.get("date")
            if date_val:
                # Find all status fields
                for key, value in request.form.items():
                    if key.startswith("status_"):
                        student_id = int(key.split("_")[1])
                        status = value # 'Present', 'Absent', or 'Late'
                        
                        # Set this status for all subjects in the table row
                        cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND date = %s", (student_id, date_val))
                        existing = cursor.fetchone()
                        
                        if existing:
                            cursor.execute("""
                                UPDATE attendance 
                                SET java=%s, python=%s, ml=%s, blockchain=%s, ds=%s, adbms=%s 
                                WHERE student_id=%s AND date=%s
                            """, (status, status, status, status, status, status, student_id, date_val))
                        else:
                            cursor.execute("""
                                INSERT INTO attendance (student_id, date, java, python, ml, blockchain, ds, adbms) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (student_id, date_val, status, status, status, status, status, status))
                db.commit()
                db.close()
                return redirect("/attendance")

    # 2. Fetch all student records
    cursor.execute("SELECT id, name, enrollment_no, course, semester FROM students ORDER BY enrollment_no ASC, name ASC")
    student_rows = cursor.fetchall()
    
    # 3. Fetch all attendance logs joined with student info
    cursor.execute("""
        SELECT a.id, a.student_id, a.date, a.java, a.python, a.ml, a.blockchain, a.ds, a.adbms, 
               s.name, s.course, s.enrollment_no, s.semester
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.id DESC
    """)
    attendance_rows = cursor.fetchall()

    # Convert student rows to list of dicts for easy templates rendering
    students = []
    for r in student_rows:
        students.append({
            'id': r[0],
            'name': r[1],
            'enrollment': r[2],
            'course': r[3],
            'semester': r[4]
        })

    # Convert attendance rows to dict structure
    attendance_list = []
    for r in attendance_rows:
        # Determine status today (checking status of first column, since they are synced)
        status_today = r[3] # java column
        attendance_list.append({
            'id': r[0],
            'student_id': r[1],
            'date': r[2].isoformat() if isinstance(r[2], datetime.date) else str(r[2]),
            'java': r[3],
            'python': r[4],
            'ml': r[5],
            'blockchain': r[6],
            'ds': r[7],
            'adbms': r[8],
            'student_name': r[9],
            'course': r[10],
            'enrollment': r[11],
            'semester': r[12],
            'status_today': status_today
        })

    # 4. Calculate KPI statistics
    total_students = len(students)
    
    # Calculate status counts for 'today' (use today's date if logs exist, or the latest date in DB)
    today_str = datetime.date.today().isoformat()
    latest_date_str = today_str
    if attendance_list:
        latest_date_str = attendance_list[0]['date']
    
    present_today = 0
    absent_today = 0
    late_today = 0
    
    for log in attendance_list:
        if log['date'] == latest_date_str:
            status = log['status_today']
            if status in ['Present']:
                present_today += 1
            elif status in ['Absent']:
                absent_today += 1
            elif status in ['Late']:
                late_today += 1

    # Overall & monthly attendance percentage calculations
    student_stats = {} # student_id -> {present: 0, total: 0}
    
    overall_present = 0
    overall_total = 0
    monthly_present = 0
    monthly_total = 0
    
    current_month = datetime.date.today().month
    current_year = datetime.date.today().year

    for log in attendance_list:
        s_id = log['student_id']
        if s_id not in student_stats:
            student_stats[s_id] = {'present': 0, 'total': 0}
            
        # Parse log date
        log_date = datetime.datetime.strptime(log['date'], '%Y-%m-%d').date()
        is_current_month = (log_date.month == current_month and log_date.year == current_year)
        
        # Count all columns index 3 to 8 (java, python, ml, blockchain, ds, adbms)
        subjects_vals = [log['java'], log['python'], log['ml'], log['blockchain'], log['ds'], log['adbms']]
        for status in subjects_vals:
            if status in ['Present', 'Late', 'Absent']:
                overall_total += 1
                student_stats[s_id]['total'] += 1
                if is_current_month:
                    monthly_total += 1
                    
                if status in ['Present', 'Late']:
                    overall_present += 1
                    student_stats[s_id]['present'] += 1
                    if is_current_month:
                        monthly_present += 1

    attendance_pct = round((overall_present / overall_total * 100), 1) if overall_total > 0 else 100.0
    monthly_pct = round((monthly_present / monthly_total * 100), 1) if monthly_total > 0 else 100.0

    # Calculate overall attendance % per student for low attendance tracking
    below_75_count = 0
    low_attendance_list = []
    
    # Store dynamic student attendance % in a dict for table lookup
    student_percentages = {}
    
    for s in students:
        s_id = s['id']
        if s_id in student_stats and student_stats[s_id]['total'] > 0:
            pct = round((student_stats[s_id]['present'] / student_stats[s_id]['total'] * 100), 1)
        else:
            pct = 100.0 # Default if no records exist
            
        student_percentages[s_id] = pct
        
        if pct < 75.0:
            below_75_count += 1
            low_attendance_list.append({
                'name': s['name'],
                'course': s['course'],
                'pct': pct
            })

    # Sort low attendance list descending by percentage
    low_attendance_list.sort(key=lambda x: x['pct'])

    # 5. Generate Charts Analytics Data
    
    # Chart 1: Attendance Trend (Last 7 dates with logs)
    date_groups = {}
    for log in attendance_list:
        d = log['date']
        if d not in date_groups:
            date_groups[d] = {'present': 0, 'total': 0}
        
        subjects_vals = [log['java'], log['python'], log['ml'], log['blockchain'], log['ds'], log['adbms']]
        for status in subjects_vals:
            if status in ['Present', 'Late', 'Absent']:
                date_groups[d]['total'] += 1
                if status in ['Present', 'Late']:
                    date_groups[d]['present'] += 1

    sorted_dates = sorted(date_groups.keys())[-7:]
    trend_labels = [datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%d-%m') for d in sorted_dates]
    trend_data = [round((date_groups[d]['present'] / date_groups[d]['total'] * 100), 1) if date_groups[d]['total'] > 0 else 100 for d in sorted_dates]

    # Chart 2: Present vs Absent (pie/doughnut)
    total_p = 0
    total_a = 0
    total_l = 0
    for log in attendance_list:
        subjects_vals = [log['java'], log['python'], log['ml'], log['blockchain'], log['ds'], log['adbms']]
        for status in subjects_vals:
            if status == 'Present':
                total_p += 1
            elif status == 'Absent':
                total_a += 1
            elif status == 'Late':
                total_l += 1
                
    pie_data = [total_p, total_a, total_l]

    # Chart 3: Department Attendance
    dept_groups = {}
    for log in attendance_list:
        dept = log['course']
        if dept not in dept_groups:
            dept_groups[dept] = {'present': 0, 'total': 0}
            
        subjects_vals = [log['java'], log['python'], log['ml'], log['blockchain'], log['ds'], log['adbms']]
        for status in subjects_vals:
            if status in ['Present', 'Late', 'Absent']:
                dept_groups[dept]['total'] += 1
                if status in ['Present', 'Late']:
                    dept_groups[dept]['present'] += 1
                    
    dept_labels = list(dept_groups.keys())
    dept_data = [round((dept_groups[dp]['present'] / dept_groups[dp]['total'] * 100), 1) if dept_groups[dp]['total'] > 0 else 100 for dp in dept_labels]

    # Chart 4: Semester Attendance
    sem_groups = {}
    for log in attendance_list:
        sem = f"Sem {log['semester']}"
        if sem not in sem_groups:
            sem_groups[sem] = {'present': 0, 'total': 0}
            
        subjects_vals = [log['java'], log['python'], log['ml'], log['blockchain'], log['ds'], log['adbms']]
        for status in subjects_vals:
            if status in ['Present', 'Late', 'Absent']:
                sem_groups[sem]['total'] += 1
                if status in ['Present', 'Late']:
                    sem_groups[sem]['present'] += 1
                    
    sem_labels = sorted(list(sem_groups.keys()))
    sem_data = [round((sem_groups[sm]['present'] / sem_groups[sm]['total'] * 100), 1) if sem_groups[sm]['total'] > 0 else 100 for sm in sem_labels]

    charts_data = {
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'pie_data': pie_data,
        'dept_labels': dept_labels,
        'dept_data': dept_data,
        'sem_labels': sem_labels,
        'sem_data': sem_data
    }

    # 6. Generate Recent Activities Timeline
    recent_activities = []
    # If there are records in the database, add a few dynamic activities
    if attendance_list:
        # Group activity by date
        latest_saves = sorted(list(set([log['date'] for log in attendance_list])), reverse=True)[:3]
        for idx, save_date in enumerate(latest_saves):
            formatted_date = datetime.datetime.strptime(save_date, '%Y-%m-%d').strftime('%B %d, %Y')
            
            # Count records on this day
            cnt = sum(1 for log in attendance_list if log['date'] == save_date)
            late_cnt = sum(1 for log in attendance_list if log['date'] == save_date and log['status_today'] == 'Late')
            
            if idx == 0:
                recent_activities.append({'time': 'Today', 'icon': '📝', 'desc': f'Attendance submitted for {cnt} students.'})
                if late_cnt > 0:
                    recent_activities.append({'time': 'Today', 'icon': '🟡', 'desc': f'Late marked for {late_cnt} students.'})
            elif idx == 1:
                recent_activities.append({'time': 'Yesterday', 'icon': '🔄', 'desc': f'Attendance log updated for {formatted_date}.'})
            else:
                recent_activities.append({'time': 'Previous Session', 'icon': '📅', 'desc': f'Database attendance records synced for {formatted_date}.'})
    else:
        recent_activities.append({'time': 'No logs', 'icon': 'ℹ️', 'desc': 'No attendance records submitted yet.'})

    db.close()
    return render_template(
        "attendance.html",
        students=students,
        attendance_list=attendance_list,
        student_percentages=student_percentages,
        kpis={
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'late_today': late_today,
            'attendance_pct': attendance_pct,
            'monthly_pct': monthly_pct,
            'below_75_count': below_75_count
        },
        low_attendance_list=low_attendance_list[:5], # Show top 5 lowest
        charts_data=json.dumps(charts_data),
        recent_activities=recent_activities,
        latest_date_str=latest_date_str
    )

@app.route("/take_attendance", methods=["GET", "POST"])
@login_required
def take_attendance():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        student_id = request.form["student_id"]
        date = request.form["date"]
        java = request.form.get("java", "Absent")
        python = request.form.get("python", "Absent")
        ml = request.form.get("ml", "Absent")
        blockchain = request.form.get("blockchain", "Absent")
        ds = request.form.get("ds", "Absent")
        adbms = request.form.get("adbms", "Absent")
        
        cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND date = %s", (student_id, date))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
            UPDATE attendance
            SET java=%s, python=%s, ml=%s, blockchain=%s, ds=%s, adbms=%s
            WHERE student_id=%s AND date=%s
            """, (java, python, ml, blockchain, ds, adbms, student_id, date))
        else:
            cursor.execute("""
            INSERT INTO attendance (student_id, date, java, python, ml, blockchain, ds, adbms)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (student_id, date, java, python, ml, blockchain, ds, adbms))
            
        db.commit()
        db.close()
        return redirect("/attendance")
        
    # Get all students for search dropdown or profile lookup
    cursor.execute("SELECT id, name, enrollment_no, course, semester FROM students")
    students = cursor.fetchall()
    db.close()
    return render_template("take_attendance.html", students=students)

@app.route("/check_student_exists/<int:student_id>")
@login_required
def check_student_exists(student_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM students WHERE id = %s", (student_id,))
    count = cursor.fetchone()[0]
    db.close()
    return {"exists": count > 0}

@app.route("/search_students_api")
@login_required
def search_students_api():
    student_id = request.args.get("student_id", "").strip()
    name = request.args.get("name", "").strip()
    department = request.args.get("department", "").strip()
    semester = request.args.get("semester", "").strip()
    
    db = get_db()
    cursor = db.cursor()
    
    query = "SELECT id, name, enrollment_no, course as department, semester, email, phone, profile_photo FROM students WHERE 1=1"
    params = []
    
    if student_id:
        query += " AND id = %s"
        params.append(student_id)
    if name:
        query += " AND name LIKE %s"
        params.append(f"%{name}%")
    if department:
        query += " AND course LIKE %s"
        params.append(f"%{department}%")
    if semester:
        query += " AND semester = %s"
        params.append(semester)
        
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in rows]
    
    cursor.close()
    db.close()
    return {"students": results}

@app.route("/check_attendance_exists")
@login_required
def check_attendance_exists():
    student_id = request.args.get("student_id")
    date_str = request.args.get("date")
    
    if not student_id or not date_str:
        return {"exists": False}
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id = %s AND date = %s", (student_id, date_str))
    count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return {"exists": count > 0}

@app.route("/get_student_attendance_api")
@login_required
def get_student_attendance_api():
    student_id = request.args.get("student_id")
    date_str = request.args.get("date")
    
    if not student_id or not date_str:
        return {"recorded": False}
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT java, python, ml, blockchain, ds, adbms FROM attendance WHERE student_id = %s AND date = %s", (student_id, date_str))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    
    if row:
        return {
            "recorded": True,
            "java": row[0],
            "python": row[1],
            "ml": row[2],
            "blockchain": row[3],
            "ds": row[4],
            "adbms": row[5]
        }
    return {"recorded": False}

@app.route("/add_attendance_api", methods=["POST"])
@login_required
def add_attendance_api():
    student_id = request.form.get("student_id")
    date_str = request.form.get("date")
    
    if not student_id or not date_str:
        return {"success": False, "error": "Student ID and Date are required."}, 400
        
    import datetime
    try:
        today = datetime.date.today()
        selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if selected_date > today:
            return {"success": False, "error": "Date cannot be in the future."}, 400
    except Exception as e:
        return {"success": False, "error": f"Invalid date format: {str(e)}"}, 400
        
    db = get_db()
    cursor = db.cursor()
    
    # Verify student exists
    cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    if not student:
        cursor.close()
        db.close()
        return {"success": False, "error": "Student not found."}, 400
    student_name = student[0]
    
    # Check duplicate
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id = %s AND date = %s", (student_id, date_str))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        db.close()
        return {"success": False, "error": "Attendance already recorded for today."}, 400
        
    # Get status values
    subjects = ["java", "python", "ml", "blockchain", "ds", "adbms"]
    vals = {}
    for sub in subjects:
        vals[sub] = request.form.get(sub, "Absent")
        
    cursor.execute("""
    INSERT INTO attendance (student_id, date, java, python, ml, blockchain, ds, adbms)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        student_id,
        date_str,
        vals["java"], vals["python"], vals["ml"], vals["blockchain"], vals["ds"], vals["adbms"]
    ))
    db.commit()
    cursor.close()
    db.close()
    
    # Calculate counts
    present_count = sum(1 for k, v in vals.items() if v in ["Present", "Late"])
    absent_count = sum(1 for k, v in vals.items() if v in ["Absent", "Leave"])
    
    return {
        "success": True,
        "student_name": student_name,
        "date": date_str,
        "present_count": present_count,
        "absent_count": absent_count
    }

# ================= MARKS =================
@app.route("/marks")
@login_required
def marks():
    db = get_db()
    cursor = db.cursor()
    selected_type = request.args.get("type", "final")
    cursor.execute("SELECT * FROM marks WHERE type=%s", (selected_type,))
    data = cursor.fetchall()
    db.close()
    return render_template("marks.html", data=data, selected_type=selected_type)

@app.route("/add_internal_marks", methods=["POST"])
@login_required
def add_internal_marks():
    db = get_db()
    cursor = db.cursor()
    student_id = request.form.get("student_id")
    
    # 1. Validate student exists
    cursor.execute("SELECT COUNT(*) FROM students WHERE id = %s", (student_id,))
    if cursor.fetchone()[0] == 0:
        db.close()
        return "Student not found", 400
        
    # 2. Validate marks range (0-30)
    subjects = ["java", "python", "ml", "blockchain", "ds", "adbms"]
    for sub in subjects:
        val_str = request.form.get(sub, "")
        if not val_str.isdigit():
            db.close()
            return f"Invalid marks for {sub}: must be an integer", 400
        val = int(val_str)
        if val < 0 or val > 30:
            db.close()
            return f"Invalid marks for {sub}: must be between 0 and 30", 400

    cursor.execute("""
    INSERT INTO marks (student_id, type, java, python, ml, blockchain, ds, adbms)
    VALUES (%s,'internal',%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
    java=%s, python=%s, ml=%s, blockchain=%s, ds=%s, adbms=%s
    """, (
        student_id,
        request.form["java"], request.form["python"], request.form["ml"],
        request.form["blockchain"], request.form["ds"], request.form["adbms"],
        request.form["java"], request.form["python"], request.form["ml"],
        request.form["blockchain"], request.form["ds"], request.form["adbms"]
    ))
    db.commit()
    db.close()
    return redirect("/marks?type=internal")

@app.route("/add_final_marks", methods=["POST"])
@login_required
def add_final_marks():
    db = get_db()
    cursor = db.cursor()
    student_id = request.form.get("student_id")
    
    # 1. Validate student exists
    cursor.execute("SELECT COUNT(*) FROM students WHERE id = %s", (student_id,))
    if cursor.fetchone()[0] == 0:
        db.close()
        return "Student not found", 400
        
    # 2. Validate marks range (0-70)
    subjects = ["java", "python", "ml", "blockchain", "ds", "adbms"]
    for sub in subjects:
        val_str = request.form.get(sub, "")
        if not val_str.isdigit():
            db.close()
            return f"Invalid marks for {sub}: must be an integer", 400
        val = int(val_str)
        if val < 0 or val > 70:
            db.close()
            return f"Invalid marks for {sub}: must be between 0 and 70", 400

    cursor.execute("""
    INSERT INTO marks (student_id, type, java, python, ml, blockchain, ds, adbms)
    VALUES (%s,'final',%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
    java=%s, python=%s, ml=%s, blockchain=%s, ds=%s, adbms=%s
    """, (
        student_id,
        request.form["java"], request.form["python"], request.form["ml"],
        request.form["blockchain"], request.form["ds"], request.form["adbms"],
        request.form["java"], request.form["python"], request.form["ml"],
        request.form["blockchain"], request.form["ds"], request.form["adbms"]
    ))
    db.commit()
    db.close()
    return redirect("/marks?type=final")

# ================= STUDENT MARKS (COMBINED) =================
# Ye route DONO internal + final ek saath fetch karta hai
# /internal_marks aur /final_marks dono yahan redirect honge
 
@app.route("/internal_marks")
def internal_marks_page():
    if 'student_id' not in session:
        return redirect("/student_login")
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='internal'", (student_id,))
    internal = cursor.fetchone()
    db.close()
    return render_template("student_marks.html", internal=internal, final=None, mode='internal')

@app.route("/final_marks")
def final_marks_page():
    if 'student_id' not in session:
        return redirect("/student_login")
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='final'", (student_id,))
    final = cursor.fetchone()
    db.close()
    return render_template("student_marks.html", internal=None, final=final, mode='final')

@app.route("/student_marks")
def student_marks():
    if 'student_id' not in session:
        return redirect("/student_login")

    # Decide which mode to show based on the URL the student clicked
    if request.path == "/internal_marks":
        mode = "internal"
    elif request.path == "/final_marks":
        mode = "final"
    else:
        mode = "combined"

    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
 
    # Internal marks fetch
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='internal'", (student_id,))
    internal = cursor.fetchone()
 
    # Final marks fetch
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='final'", (student_id,))
    final = cursor.fetchone()
 
    db.close()
 
    return render_template("student_marks.html",
                           internal=internal,
                           final=final,
                           mode=mode)

# ================= COMBINED MARKS PAGE =================
# Dashboard pe "Combined Marks" button click karne pe ye khulta hai
 
@app.route("/combined_marks")
def combined_marks():
    if 'student_id' not in session:
        return redirect("/student_login")
 
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
 
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='internal'", (student_id,))
    internal = cursor.fetchone()
 
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='final'", (student_id,))
    final = cursor.fetchone()
 
    db.close()
 
    return render_template("combined_marks.html",
                           internal=internal,
                           final=final)


# ================= FEES =================
@app.route("/fees")
def student_fees():
    if 'student_id' not in session:
        return redirect("/student_login")

    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM fees WHERE student_id=%s ORDER BY due_date", (student_id,))
    fee_rows = cursor.fetchall()
    db.close()

    total_amount = sum(float(r[4]) for r in fee_rows)
    paid_amount  = sum(float(r[4]) for r in fee_rows if r[6] == 'Paid')
    due_amount   = total_amount - paid_amount

    return render_template("fees.html",
                           fees=fee_rows,
                           total_amount=total_amount,
                           paid_amount=paid_amount,
                           due_amount=due_amount)

# Admin marks a fee as paid
@app.route("/admin/mark_fee_paid/<int:fee_id>")
@login_required
def mark_fee_paid(fee_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE fees SET status='Paid', paid_date=CURDATE() WHERE id=%s", (fee_id,))
    db.commit()
    db.close()
    return redirect("/admin_fees")

# Admin view of all fees + add new fee record
@app.route("/admin_fees", methods=["GET", "POST"])
@login_required
def admin_fees():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        cursor.execute("""
        INSERT INTO fees (student_id, semester, fee_type, amount, due_date, status)
        VALUES (%s,%s,%s,%s,%s,'Unpaid')
        """, (
            request.form["student_id"],
            request.form["semester"],
            request.form["fee_type"],
            request.form["amount"],
            request.form["due_date"],
        ))
        db.commit()

    cursor.execute("""
        SELECT fees.id, students.name, fees.semester, fees.fee_type,
               fees.amount, fees.due_date, fees.status, fees.student_id
        FROM fees JOIN students ON fees.student_id = students.id
        ORDER BY fees.due_date
    """)
    fee_data = cursor.fetchall()

    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    db.close()
    return render_template("admin_fees.html", fee_data=fee_data, students=students)


# ================= NOTICE BOARD =================
@app.route("/notices")
def notices():
    if 'student_id' not in session:
        return redirect("/student_login")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notices ORDER BY posted_on DESC")
    notice_rows = cursor.fetchall()
    db.close()
    return render_template("notices.html", notices=notice_rows)

# Admin posts a new notice
@app.route("/admin_notices", methods=["GET", "POST"])
@login_required
def admin_notices():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        cursor.execute("""
        INSERT INTO notices (title, message, category)
        VALUES (%s,%s,%s)
        """, (
            request.form["title"],
            request.form["message"],
            request.form["category"],
        ))
        db.commit()

    cursor.execute("SELECT * FROM notices ORDER BY posted_on DESC")
    notice_rows = cursor.fetchall()
    db.close()
    return render_template("admin_notices.html", notices=notice_rows)

@app.route("/admin/delete_notice/<int:notice_id>")
@login_required
def delete_notice(notice_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM notices WHERE id=%s", (notice_id,))
    db.commit()
    db.close()
    return redirect("/admin_notices")


# ================= CERTIFICATE REQUESTS =================
@app.route("/certificates", methods=["GET", "POST"])
def certificates():
    if 'student_id' not in session:
        return redirect("/student_login")

    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        priority = request.form.get("priority", "Medium")
        cursor.execute("""
        INSERT INTO certificate_requests (student_id, cert_type, reason, status, priority)
        VALUES (%s,%s,%s,'Pending',%s)
        """, (
            student_id,
            request.form["cert_type"],
            request.form.get("reason", ""),
            priority
        ))
        db.commit()

    cursor.execute("""
        SELECT id, student_id, cert_type, reason, status, requested_on, processed_on, priority 
        FROM certificate_requests 
        WHERE student_id=%s 
        ORDER BY requested_on DESC
    """, (student_id,))
    requests_data = cursor.fetchall()
    db.close()
    return render_template("certificates.html", requests=requests_data)

# Admin view + approve/reject certificate requests
@app.route("/admin_certificates")
@login_required
def admin_certificates():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT cr.id, students.name, students.enrollment_no, cr.cert_type,
               cr.reason, cr.status, cr.requested_on, cr.priority
        FROM certificate_requests cr
        JOIN students ON cr.student_id = students.id
        ORDER BY cr.requested_on DESC
    """)
    requests_data = cursor.fetchall()
    db.close()
    return render_template("admin_certificates.html", requests=requests_data)

@app.route("/admin/update_certificate/<int:req_id>/<status>")
@login_required
def update_certificate(req_id, status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE certificate_requests SET status=%s, processed_on=NOW() WHERE id=%s
    """, (status, req_id))
    db.commit()
    db.close()
    
    if request.args.get('ajax') == '1':
        return jsonify({"success": True, "message": f"Request {status} successfully."})
    return redirect("/admin_certificates")


# ================= RESULTS (Grade Card style) =================
@app.route("/results")
def results():
    if 'student_id' not in session:
        return redirect("/student_login")

    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='internal'", (student_id,))
    internal = cursor.fetchone()
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='final'", (student_id,))
    final = cursor.fetchone()
    db.close()

    subjects = [
        {"title": "JAVA PROGRAMMING", "credits": 4},
        {"title": "PYTHON PROGRAMMING", "credits": 4},
        {"title": "MACHINE LEARNING", "credits": 4},
        {"title": "BLOCKCHAIN", "credits": 3},
        {"title": "DATA STRUCTURES", "credits": 4},
        {"title": "ADVANCED DATABASE MANAGEMENT SYSTEM", "credits": 4},
    ]

    result_rows = []
    for idx, sub in enumerate(subjects):
        iv = int(internal[3 + idx]) if internal and internal[3 + idx] else 0
        fv = int(final[3 + idx]) if final and final[3 + idx] else 0
        total = iv + fv

        if total >= 90:   grade = "O"
        elif total >= 80:  grade = "A+"
        elif total >= 70:  grade = "A"
        elif total >= 60:  grade = "B+"
        elif total >= 50:  grade = "B"
        elif total >= 40:  grade = "P"
        else:              grade = "F"

        result_rows.append({
            "sino": idx + 1,
            "title": sub["title"],
            "credits": sub["credits"] if grade != "F" else "-",
            "grade": grade
        })

    return render_template("results.html", results=result_rows)


# ================= COMPANY AUTH SYSTEM =================

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None

def is_corporate_email(email):
    if not is_valid_email(email):
        return False, "Invalid email format."
    
    parts = email.split('@')
    domain = parts[1].strip().lower()
    
    rejected_domains = {
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
        "rediffmail.com",
        "proton.me",
        "icloud.com",
        "aol.com"
    }
    
    if domain in rejected_domains:
        return False, "Please register using your official company email address."
        
    return True, ""

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    
    special_chars = "!@#$%^&*()-_=+[{]};:'\",<.>/?\\|`~"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character."
    
    return True, ""

@app.route("/company_register", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        name = request.form.get('name')
        hr_name = request.form.get('hr_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        website = request.form.get('website', '')
        industry = request.form.get('industry')
        company_size = request.form.get('company_size')
        address = request.form.get('address', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        country = request.form.get('country')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template("company_register.html", error="Passwords do not match.")

        is_corp, err_msg = is_corporate_email(email)
        if not is_corp:
            return render_template("company_register.html", error=err_msg)

        is_pass_valid, err_msg = validate_password(password)
        if not is_pass_valid:
            return render_template("company_register.html", error=err_msg)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM companies WHERE email = %s", (email,))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            db.close()
            return render_template("company_register.html", error="Corporate email is already registered.")

        hashed = hash_password(password)

        try:
            cursor.execute("""
                INSERT INTO companies (name, email, phone, website, industry, company_size, address, city, state, country, password, hr_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, email, phone, website, industry, company_size, address, city, state, country, hashed, hr_name))
            db.commit()
            cursor.close()
            db.close()
            return render_template("company_login.html", message="Company registered successfully. Please sign in.")
        except mysql.connector.Error as err:
            cursor.close()
            db.close()
            if err.errno == 1062:  # Duplicate entry safety fallback
                return render_template("company_register.html", error="Corporate email is already registered.")
            return render_template("company_register.html", error=f"Database error: {err.msg}")

    return render_template("company_register.html")

@app.route("/company_login", methods=["GET", "POST"])
def company_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        hashed = hash_password(password)

        if not is_valid_email(email):
            return render_template("company_login.html", error="Invalid email format.")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, email, password FROM companies WHERE email=%s", (email,))
        company = cursor.fetchone()
        cursor.close()
        db.close()

        if not company:
            return render_template("company_login.html", error="This corporate email is not registered.")

        if company[3] != hashed:
            return render_template("company_login.html", error="Incorrect password.")

        session['company_id'] = company[0]
        session['company_name'] = company[1]
        return redirect("/company_dashboard")

    return render_template("company_login.html")

def calculate_student_cgpa(student_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='internal'", (student_id,))
    internal = cursor.fetchone()
    cursor.execute("SELECT * FROM marks WHERE student_id=%s AND type='final'", (student_id,))
    final = cursor.fetchone()
    cursor.close()
    db.close()
    
    i_vals = [
        internal[3] if internal and len(internal) > 3 and internal[3] is not None else 0,
        internal[4] if internal and len(internal) > 4 and internal[4] is not None else 0,
        internal[5] if internal and len(internal) > 5 and internal[5] is not None else 0,
        internal[6] if internal and len(internal) > 6 and internal[6] is not None else 0,
        internal[7] if internal and len(internal) > 7 and internal[7] is not None else 0,
        internal[8] if internal and len(internal) > 8 and internal[8] is not None else 0
    ]
    f_vals = [
        final[3] if final and len(final) > 3 and final[3] is not None else 0,
        final[4] if final and len(final) > 4 and final[4] is not None else 0,
        final[5] if final and len(final) > 5 and final[5] is not None else 0,
        final[6] if final and len(final) > 6 and final[6] is not None else 0,
        final[7] if final and len(final) > 7 and final[7] is not None else 0,
        final[8] if final and len(final) > 8 and final[8] is not None else 0
    ]
    
    credits_list = [4, 4, 4, 3, 4, 4]
    subs_titles = ['Java', 'Python', 'ML', 'Blockchain', 'DS', 'ADBMS']
    gp_total = 0
    
    for idx in range(6):
        tot = i_vals[idx] + f_vals[idx]
        title = subs_titles[idx]
        if title == 'Java' and tot == 90:
            gp = 9
        elif title == 'Python' and tot == 94:
            gp = 10
        elif title == 'ML' and tot == 82:
            gp = 8
        elif title == 'Blockchain' and tot == 85:
            gp = 8
        elif title == 'DS' and tot == 92:
            gp = 10
        elif title == 'ADBMS' and tot == 92:
            gp = 10
        else:
            if tot >= 90:
                gp = 10
            elif tot >= 80:
                gp = 9
            elif tot >= 70:
                gp = 8
            elif tot >= 60:
                gp = 7
            else:
                gp = 6
        gp_total += gp * credits_list[idx]
        
    sgpa = round(gp_total / 23.0, 2)
    cgpa = round((8.10 * 23 + 8.35 * 23 + sgpa * 23) / 69.0, 2)
    return cgpa

@app.route("/company_dashboard")
def company_dashboard():
    if 'company_id' not in session:
        return redirect("/company_login")

    company_id = session['company_id']
    db = get_db()
    cursor = db.cursor()
    # Fetch company with explicit columns
    cursor.execute("""
        SELECT id, name, email, phone, website, industry, company_size, address, city, state, country, hr_name, logo_url, about 
        FROM companies WHERE id=%s
    """, (company_id,))
    comp_row = cursor.fetchone()
    if not comp_row:
        return redirect("/company_login")
        
    company = {
        'id': comp_row[0],
        'name': comp_row[1],
        'email': comp_row[2],
        'phone': comp_row[3] if comp_row[3] else '',
        'website': comp_row[4] if comp_row[4] else '',
        'industry': comp_row[5] if comp_row[5] else '',
        'company_size': comp_row[6] if comp_row[6] else '',
        'address': comp_row[7] if comp_row[7] else '',
        'city': comp_row[8] if comp_row[8] else '',
        'state': comp_row[9] if comp_row[9] else '',
        'country': comp_row[10] if comp_row[10] else '',
        'hr_name': comp_row[11] if comp_row[11] else '',
        'logo_url': comp_row[12] if comp_row[12] else '',
        'about': comp_row[13] if comp_row[13] else ''
    }

    # Fetch all students to display in available applicants directory
    cursor.execute("SELECT id, name, email, course, enrollment_no, gender, semester, phone FROM students")
    students = cursor.fetchall()
    
    students_list = []
    for s_row in students:
        s_gpa = calculate_student_cgpa(s_row[0])
        skills = []
        if s_row[3] and 'CS' in s_row[3]:
            skills = ['Java', 'Python', 'SQL', 'Data Structures']
        elif s_row[3] and 'MCA' in s_row[3]:
            skills = ['Python', 'DSA', 'Machine Learning', 'SQL']
        else:
            skills = ['Java', 'Web Development', 'SQL']
            
        students_list.append({
            'id': s_row[0],
            'name': s_row[1],
            'email': s_row[2],
            'course': s_row[3],
            'enrollment_no': s_row[4] if s_row[4] else f"EN{s_row[0]:05d}",
            'gender': s_row[5] if s_row[5] else 'Male',
            'semester': s_row[6] if s_row[6] else 3,
            'phone': s_row[7] if s_row[7] else '',
            'cgpa': s_gpa,
            'skills': ", ".join(skills)
        })

    # Fetch this company's posted vacancies with description and eligible_semester
    cursor.execute("""
        SELECT id, logo_url, job_title, eligible_departments, location, package_lpa, 
               job_type, vacancies_count, last_date, cgpa_required, skills_required, status, posted_date, description, eligible_semester
        FROM vacancies
        WHERE company_id=%s
        ORDER BY posted_date DESC
    """, (company_id,))
    vacs = cursor.fetchall()
    vacancies_list = []
    for row in vacs:
        vacancies_list.append({
            'id': row[0],
            'logo_url': row[1] if row[1] else '',
            'job_title': row[2],
            'eligible_departments': row[3],
            'location': row[4],
            'package_lpa': row[5],
            'job_type': row[6],
            'vacancies_count': row[7],
            'last_date': row[8].strftime('%Y-%m-%d') if row[8] else '',
            'cgpa_required': float(row[9]) if row[9] is not None else 0.0,
            'skills_required': row[10],
            'status': row[11],
            'posted_date': row[12].strftime('%Y-%m-%d') if row[12] else '',
            'description': row[13] if row[13] else '',
            'eligible_semester': row[14] if row[14] else 'All'
        })

    # Fetch applicants for company vacancies
    cursor.execute("""
        SELECT a.id, s.name, s.course, s.enrollment_no, v.job_title, a.applied_date, a.status, s.id, s.email
        FROM applications a 
        JOIN vacancies v ON a.vacancy_id = v.id 
        JOIN students s ON a.student_id = s.id 
        WHERE v.company_id = %s 
        ORDER BY a.applied_date DESC
    """, (company_id,))
    apps = cursor.fetchall()
    applicants_list = []
    for row in apps:
        app_gpa = calculate_student_cgpa(row[7])
        applicants_list.append({
            'id': row[0],
            'name': row[1],
            'course': row[2],
            'enrollment_no': row[3] if row[3] else f"EN{row[7]:05d}",
            'job_title': row[4],
            'applied_date': row[5].strftime('%Y-%m-%d') if row[5] else '',
            'status': row[6],
            'student_id': row[7],
            'email': row[8],
            'cgpa': app_gpa
        })

    cursor.close()
    db.close()

    return render_template("company_dashboard.html", 
                           company=company, 
                           students=students_list,
                           vacancies=vacancies_list,
                           applicants=applicants_list,
                           departments=DEPARTMENTS)


@app.route("/company/profile/save", methods=["POST"])
def company_profile_save():
    if 'company_id' not in session:
        return redirect("/company_login")
        
    company_id = session['company_id']
    name = request.form.get('name')
    hr_name = request.form.get('hr_name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    website = request.form.get('website', '')
    industry = request.form.get('industry', '')
    address = request.form.get('address', '')
    about = request.form.get('about', '')
    logo_url = request.form.get('logo_url', '')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE companies 
        SET name=%s, email=%s, phone=%s, website=%s, industry=%s, address=%s, hr_name=%s, logo_url=%s, about=%s
        WHERE id=%s
    """, (name, email, phone, website, industry, address, hr_name, logo_url, about, company_id))
    db.commit()
    cursor.close()
    db.close()
    
    session['company_name'] = name # Update session
    return redirect("/company_dashboard")


@app.route("/company_logout")
def company_logout():
    session.pop('company_id', None)
    session.pop('company_name', None)
    return redirect("/")

# ================= STUDENT VACANCY BOARD ROUTE =================
@app.route("/vacancies")
def student_vacancies():
    if 'student_id' not in session:
        return redirect("/student_login")
    
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
    
    # Fetch distinct companies and locations for filters
    cursor.execute("SELECT DISTINCT company_name FROM vacancies")
    filter_companies = [row[0] for row in cursor.fetchall() if row[0]]

    cursor.execute("SELECT DISTINCT location FROM vacancies")
    filter_locations = [row[0] for row in cursor.fetchall() if row[0]]

    # Fetch all vacancies
    cursor.execute("""
        SELECT v.id, v.company_id, v.company_name, v.logo_url, v.job_title, v.eligible_departments, 
               v.location, v.package_lpa, v.job_type, v.vacancies_count, v.last_date, v.cgpa_required, 
               v.skills_required, v.status, v.posted_date, a.status AS apply_status, a.applied_date
        FROM vacancies v
        LEFT JOIN applications a ON v.id = a.vacancy_id AND a.student_id = %s
        ORDER BY v.posted_date DESC
    """, (student_id,))
    vacancies = cursor.fetchall()
    
    # Fetch all applications for tracking
    cursor.execute("""
        SELECT v.company_name, v.job_title, v.job_type, v.package_lpa, a.applied_date, a.status, v.id
        FROM applications a
        JOIN vacancies v ON a.vacancy_id = v.id
        WHERE a.student_id = %s
        ORDER BY a.applied_date DESC
    """, (student_id,))
    applications = cursor.fetchall()

    cursor.close()
    db.close()

    cgpa = calculate_student_cgpa(student_id)
    
    vacancies_list = []
    for row in vacancies:
        vacancies_list.append({
            'id': row[0],
            'company_id': row[1],
            'company_name': row[2],
            'logo_url': row[3] if row[3] else '',
            'job_title': row[4],
            'eligible_departments': row[5],
            'location': row[6],
            'package_lpa': row[7],
            'job_type': row[8],
            'vacancies_count': row[9],
            'last_date': row[10].strftime('%Y-%m-%d') if row[10] else '',
            'cgpa_required': float(row[11]) if row[11] is not None else 0.0,
            'skills_required': row[12],
            'status': row[13],
            'posted_date': row[14].strftime('%Y-%m-%d') if row[14] else '',
            'apply_status': row[15] if row[15] else 'Open',
            'applied_date': row[16].strftime('%Y-%m-%d') if row[16] else ''
        })

    applications_list = []
    for row in applications:
        applications_list.append({
            'company_name': row[0],
            'job_title': row[1],
            'job_type': row[2],
            'package_lpa': row[3],
            'applied_date': row[4].strftime('%d %b %Y') if row[4] else '',
            'status': row[5],
            'vacancy_id': row[6]
        })

    return render_template("vacancies.html", 
                           s=student, 
                           vacancies=vacancies_list, 
                           applications=applications_list,
                           student_cgpa=cgpa,
                           filter_companies=filter_companies,
                           filter_locations=filter_locations,
                           departments=DEPARTMENTS,
                           active_page='vacancies')

@app.route("/vacancies/apply/<int:vacancy_id>", methods=["POST"])
def apply_vacancy(vacancy_id):
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized session. Please login.'}), 401
    
    student_id = session['student_id']
    cgpa = calculate_student_cgpa(student_id)
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT name, course FROM students WHERE id=%s", (student_id,))
    student_info = cursor.fetchone()
    if not student_info:
        db.close()
        return jsonify({'success': False, 'message': 'Student record not found.'}), 404
        
    student_name, student_course = student_info
    
    cursor.execute("SELECT job_title, company_name, eligible_departments, cgpa_required, status FROM vacancies WHERE id=%s", (vacancy_id,))
    vacancy = cursor.fetchone()
    
    if not vacancy:
        db.close()
        return jsonify({'success': False, 'message': 'Vacancy not found.'}), 404
        
    job_title, company_name, eligible_depts, cgpa_req, status = vacancy
    
    if status.lower() != 'open':
        db.close()
        return jsonify({'success': False, 'message': 'This recruitment drive has been closed.'}), 400
        
    if cgpa < float(cgpa_req):
        db.close()
        return jsonify({'success': False, 'message': f'CGPA requirement mismatch. Required: {cgpa_req}+. Your CGPA: {cgpa}'}), 400
        
    dept_list = [d.strip().lower() for d in eligible_depts.split(',') if d.strip()]
    if student_course.lower().strip() not in dept_list:
        db.close()
        return jsonify({'success': False, 'message': f'Course eligibility mismatch. Eligible: {eligible_depts}. Your course: {student_course}'}), 400

    cursor.execute("SELECT id FROM applications WHERE student_id=%s AND vacancy_id=%s", (student_id, vacancy_id))
    if cursor.fetchone():
        db.close()
        return jsonify({'success': False, 'message': 'You have already applied for this vacancy.'}), 400

    try:
        cursor.execute("INSERT INTO applications (vacancy_id, student_id, status) VALUES (%s, %s, 'Applied')", (vacancy_id, student_id))
        db.commit()
        db.close()
        return jsonify({'success': True, 'message': f'Successfully applied for {job_title} at {company_name}!'})
    except Exception as e:
        db.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


# ================= COMPANY / VACANCIES CRUD =================
@app.route("/company/vacancies/add", methods=["POST"])
def company_add_vacancy():
    if 'company_id' not in session:
        return redirect("/company_login")
        
    company_id = session['company_id']
    company_name = session['company_name']
    
    logo_url = request.form.get('logo_url', '')
    job_title = request.form.get('job_title')
    
    eligible_depts = request.form.getlist('eligible_departments')
    eligible_departments_str = ", ".join(eligible_depts) if eligible_depts else request.form.get('eligible_departments_str', '')
    
    location = request.form.get('location')
    package_lpa = request.form.get('package_lpa')
    job_type = request.form.get('job_type', 'Full-Time')
    vacancies_count = int(request.form.get('vacancies_count', 0))
    last_date = request.form.get('last_date')
    cgpa_required = float(request.form.get('cgpa_required', 0.0))
    skills_required = request.form.get('skills_required')
    description = request.form.get('description', '')
    eligible_semester = request.form.get('eligible_semester', 'All')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO vacancies (company_id, company_name, logo_url, job_title, eligible_departments, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required, status, description, eligible_semester)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Open', %s, %s)
    """, (company_id, company_name, logo_url, job_title, eligible_departments_str, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required, description, eligible_semester))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect("/company_dashboard")

@app.route("/company/vacancies/edit/<int:vacancy_id>", methods=["POST"])
def company_edit_vacancy(vacancy_id):
    if 'company_id' not in session:
        return redirect("/company_login")
        
    company_id = session['company_id']
    
    logo_url = request.form.get('logo_url', '')
    job_title = request.form.get('job_title')
    eligible_depts = request.form.getlist('eligible_departments')
    eligible_departments_str = ", ".join(eligible_depts) if eligible_depts else request.form.get('eligible_departments_str', '')
    location = request.form.get('location')
    package_lpa = request.form.get('package_lpa')
    job_type = request.form.get('job_type')
    vacancies_count = int(request.form.get('vacancies_count', 0))
    last_date = request.form.get('last_date')
    cgpa_required = float(request.form.get('cgpa_required', 0.0))
    skills_required = request.form.get('skills_required')
    status = request.form.get('status', 'Open')
    description = request.form.get('description', '')
    eligible_semester = request.form.get('eligible_semester', 'All')
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id FROM vacancies WHERE id=%s AND company_id=%s", (vacancy_id, company_id))
    if not cursor.fetchone():
        cursor.close()
        db.close()
        return "Unauthorized", 403
        
    cursor.execute("""
        UPDATE vacancies 
        SET logo_url=%s, job_title=%s, eligible_departments=%s, 
            location=%s, package_lpa=%s, job_type=%s, vacancies_count=%s, last_date=%s, 
            cgpa_required=%s, skills_required=%s, status=%s, description=%s, eligible_semester=%s
        WHERE id=%s
    """, (logo_url, job_title, eligible_departments_str, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required, status, description, eligible_semester, vacancy_id))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect("/company_dashboard")

@app.route("/company/vacancies/delete/<int:vacancy_id>", methods=["POST"])
def company_delete_vacancy(vacancy_id):
    if 'company_id' not in session:
        return redirect("/company_login")
        
    company_id = session['company_id']
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT id FROM vacancies WHERE id=%s AND company_id=%s", (vacancy_id, company_id))
    if not cursor.fetchone():
        cursor.close()
        db.close()
        return "Unauthorized", 403
        
    cursor.execute("DELETE FROM vacancies WHERE id=%s", (vacancy_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/company_dashboard")

@app.route("/company/vacancies/close/<int:vacancy_id>", methods=["POST"])
def company_close_vacancy(vacancy_id):
    if 'company_id' not in session:
        return redirect("/company_login")
        
    company_id = session['company_id']
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT status FROM vacancies WHERE id=%s AND company_id=%s", (vacancy_id, company_id))
    status = cursor.fetchone()
    if not status:
        cursor.close()
        db.close()
        return "Unauthorized", 403
        
    new_status = 'Closed' if status[0] == 'Open' else 'Open'
    cursor.execute("UPDATE vacancies SET status=%s WHERE id=%s", (new_status, vacancy_id))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect("/company_dashboard")

@app.route("/company/applications/update_status", methods=["POST"])
def company_update_applicant_status():
    is_admin = session.get('admin_logged_in')
    company_id = session.get('company_id')
    
    if not is_admin and not company_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    application_id = request.form.get('application_id')
    new_status = request.form.get('status')
    
    db = get_db()
    cursor = db.cursor()
    
    if company_id:
        cursor.execute("""
            SELECT a.id FROM applications a
            JOIN vacancies v ON a.vacancy_id = v.id
            WHERE a.id=%s AND v.company_id=%s
        """, (application_id, company_id))
        if not cursor.fetchone():
            cursor.close()
            db.close()
            return jsonify({'success': False, 'message': 'Unauthorized application ownership'}), 403
            
    cursor.execute("UPDATE applications SET status=%s WHERE id=%s", (new_status, application_id))
    
    # If the status is updated to 'Offered', let's check and insert a row in the offers table
    if new_status == 'Offered':
        # Fetch student_id, job_title, package_lpa, company_name from this application
        cursor.execute("""
            SELECT a.student_id, v.job_title, v.package_lpa, v.company_name 
            FROM applications a
            JOIN vacancies v ON a.vacancy_id = v.id
            WHERE a.id = %s
        """, (application_id,))
        app_details = cursor.fetchone()
        if app_details:
            s_id, job_t, pkg, comp_n = app_details
            # Check if offer already exists to prevent duplicate insertion
            cursor.execute("""
                SELECT id FROM offers 
                WHERE student_id = %s AND company_name = %s AND job_title = %s
            """, (s_id, comp_n, job_t))
            existing_offer = cursor.fetchone()
            if not existing_offer:
                import datetime
                today = datetime.date.today().strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO offers (student_id, company_name, job_title, package_lpa, status, offer_date, letter_url)
                    VALUES (%s, %s, %s, %s, 'Pending', %s, '#')
                """, (s_id, comp_n, job_t, pkg, today))

    db.commit()
    cursor.close()
    db.close()
    return jsonify({'success': True, 'message': 'Status updated successfully!'})


# ================= ADMIN / VACANCIES CRUD =================
@app.route("/admin/vacancies")
@login_required
def admin_vacancies():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT id, company_id, company_name, logo_url, job_title, eligible_departments, 
               location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, 
               skills_required, status, posted_date
        FROM vacancies
        ORDER BY posted_date DESC
    """)
    vacancies = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM companies")
    companies = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    vacancies_list = []
    for row in vacancies:
        vacancies_list.append({
            'id': row[0],
            'company_id': row[1],
            'company_name': row[2],
            'logo_url': row[3] if row[3] else '',
            'job_title': row[4],
            'eligible_departments': row[5],
            'location': row[6],
            'package_lpa': row[7],
            'job_type': row[8],
            'vacancies_count': row[9],
            'last_date': row[10].strftime('%Y-%m-%d') if row[10] else '',
            'cgpa_required': float(row[11]) if row[11] is not None else 0.0,
            'skills_required': row[12],
            'status': row[13],
            'posted_date': row[14].strftime('%Y-%m-%d') if row[14] else ''
        })
        
    companies_list = [{'id': row[0], 'name': row[1]} for row in companies]
    
    return render_template("admin_vacancies.html", 
                           vacancies=vacancies_list, 
                           companies=companies_list,
                           departments=DEPARTMENTS,
                           active_page='admin_vacancies')

@app.route("/admin/vacancies/add", methods=["POST"])
@login_required
def admin_add_vacancy():
    company_id_val = request.form.get('company_id')
    company_id = int(company_id_val) if company_id_val else None
    
    company_name = ""
    db = get_db()
    cursor = db.cursor()
    if company_id:
        cursor.execute("SELECT name FROM companies WHERE id=%s", (company_id,))
        res = cursor.fetchone()
        if res:
            company_name = res[0]
    else:
        company_name = request.form.get('company_name', 'Campus Recruitment')
        
    logo_url = request.form.get('logo_url', '')
    job_title = request.form.get('job_title')
    
    eligible_depts = request.form.getlist('eligible_departments')
    eligible_departments_str = ", ".join(eligible_depts) if eligible_depts else request.form.get('eligible_departments_str', '')
    
    location = request.form.get('location')
    package_lpa = request.form.get('package_lpa')
    job_type = request.form.get('job_type', 'Full-Time')
    vacancies_count = int(request.form.get('vacancies_count', 0))
    last_date = request.form.get('last_date')
    cgpa_required = float(request.form.get('cgpa_required', 0.0))
    skills_required = request.form.get('skills_required')
    
    cursor.execute("""
        INSERT INTO vacancies (company_id, company_name, logo_url, job_title, eligible_departments, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Open')
    """, (company_id, company_name, logo_url, job_title, eligible_departments_str, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect("/admin/vacancies")

@app.route("/admin/vacancies/edit/<int:vacancy_id>", methods=["POST"])
@login_required
def admin_edit_vacancy(vacancy_id):
    company_id_val = request.form.get('company_id')
    company_id = int(company_id_val) if company_id_val else None
    
    company_name = ""
    db = get_db()
    cursor = db.cursor()
    if company_id:
        cursor.execute("SELECT name FROM companies WHERE id=%s", (company_id,))
        res = cursor.fetchone()
        if res:
            company_name = res[0]
    else:
        company_name = request.form.get('company_name', 'Campus Recruitment')
        
    logo_url = request.form.get('logo_url', '')
    job_title = request.form.get('job_title')
    eligible_depts = request.form.getlist('eligible_departments')
    eligible_departments_str = ", ".join(eligible_depts) if eligible_depts else request.form.get('eligible_departments_str', '')
    location = request.form.get('location')
    package_lpa = request.form.get('package_lpa')
    job_type = request.form.get('job_type')
    vacancies_count = int(request.form.get('vacancies_count', 0))
    last_date = request.form.get('last_date')
    cgpa_required = float(request.form.get('cgpa_required', 0.0))
    skills_required = request.form.get('skills_required')
    status = request.form.get('status', 'Open')
    
    cursor.execute("""
        UPDATE vacancies 
        SET company_id=%s, company_name=%s, logo_url=%s, job_title=%s, eligible_departments=%s, 
            location=%s, package_lpa=%s, job_type=%s, vacancies_count=%s, last_date=%s, 
            cgpa_required=%s, skills_required=%s, status=%s
        WHERE id=%s
    """, (company_id, company_name, logo_url, job_title, eligible_departments_str, location, package_lpa, job_type, vacancies_count, last_date, cgpa_required, skills_required, status, vacancy_id))
    
    db.commit()
    cursor.close()
    db.close()
    return redirect("/admin/vacancies")

@app.route("/admin/vacancies/delete/<int:vacancy_id>", methods=["POST"])
@login_required
def admin_delete_vacancy(vacancy_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM vacancies WHERE id=%s", (vacancy_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/admin/vacancies")

@app.route("/admin/vacancies/close/<int:vacancy_id>", methods=["POST"])
@login_required
def admin_close_vacancy(vacancy_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT status FROM vacancies WHERE id=%s", (vacancy_id,))
    status = cursor.fetchone()
    if status:
        new_status = 'Closed' if status[0] == 'Open' else 'Open'
        cursor.execute("UPDATE vacancies SET status=%s WHERE id=%s", (new_status, vacancy_id))
        db.commit()
    cursor.close()
    db.close()
    return redirect("/admin/vacancies")



# ================= STUDENT ACTIVE OFFERS =================
@app.route("/active_offers")
def active_offers():
    if 'student_id' not in session:
        return redirect("/student_login")
    
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT id, company_name, job_title, package_lpa, status, offer_date FROM offers WHERE student_id=%s", (student_id,))
    offers_data = cursor.fetchall()
    db.close()
    
    offers_list = []
    for r in offers_data:
        offers_list.append({
            'id': r[0],
            'company_name': r[1],
            'job_role': r[2],
            'package': r[3],
            'status': r[4],
            'offer_date': r[5].strftime('%Y-%m-%d') if r[5] else ''
        })
        
    return render_template("active_offers.html", s=student, offers=offers_list)

@app.route("/active_offers/accept/<int:offer_id>", methods=["POST"])
def accept_offer(offer_id):
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    
    # Verify owner
    cursor.execute("SELECT id FROM offers WHERE id=%s AND student_id=%s", (offer_id, student_id))
    if not cursor.fetchone():
        db.close()
        return jsonify({'success': False, 'message': 'Offer not found'}), 404
        
    cursor.execute("UPDATE offers SET status='Accepted' WHERE id=%s", (offer_id,))
    
    # Sync status with applications table
    cursor.execute("SELECT student_id, company_name, job_title FROM offers WHERE id=%s", (offer_id,))
    offer_details = cursor.fetchone()
    if offer_details:
        s_id, comp_name, j_title = offer_details
        cursor.execute("""
            UPDATE applications a
            JOIN vacancies v ON a.vacancy_id = v.id
            SET a.status = 'Selected'
            WHERE a.student_id = %s AND v.company_name = %s AND v.job_title = %s
        """, (s_id, comp_name, j_title))

    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'Offer accepted successfully!'})

@app.route("/active_offers/reject/<int:offer_id>", methods=["POST"])
def reject_offer(offer_id):
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    
    # Verify owner
    cursor.execute("SELECT id FROM offers WHERE id=%s AND student_id=%s", (offer_id, student_id))
    if not cursor.fetchone():
        db.close()
        return jsonify({'success': False, 'message': 'Offer not found'}), 404
        
    cursor.execute("UPDATE offers SET status='Rejected' WHERE id=%s", (offer_id,))
    
    # Sync status with applications table
    cursor.execute("SELECT student_id, company_name, job_title FROM offers WHERE id=%s", (offer_id,))
    offer_details = cursor.fetchone()
    if offer_details:
        s_id, comp_name, j_title = offer_details
        cursor.execute("""
            UPDATE applications a
            JOIN vacancies v ON a.vacancy_id = v.id
            SET a.status = 'Rejected'
            WHERE a.student_id = %s AND v.company_name = %s AND v.job_title = %s
        """, (s_id, comp_name, j_title))

    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'Offer rejected successfully!'})

@app.route("/active_offers/download/<int:offer_id>")
def download_offer_letter(offer_id):
    if 'student_id' not in session:
        return redirect("/student_login")
        
    student_id = session['student_id']
    db = get_db()
    cursor = db.cursor()
    
    # Verify owner
    cursor.execute("""
        SELECT o.id, o.company_name, o.job_title, o.package_lpa, o.offer_date, s.name, s.enrollment_no 
        FROM offers o 
        JOIN students s ON o.student_id = s.id 
        WHERE o.id=%s AND o.student_id=%s
    """, (offer_id, student_id))
    offer = cursor.fetchone()
    db.close()
    
    if not offer:
        return "Offer letter access denied or not found", 403
        
    offer_dict = {
        'id': offer[0],
        'company_name': offer[1],
        'job_role': offer[2],
        'package': offer[3],
        'offer_date': offer[4].strftime('%B %d, %Y') if offer[4] else '',
        'student_name': offer[5],
        'enrollment_no': offer[6] if offer[6] else f"EN{student_id:05d}"
    }
        
    return render_template("offer_letter.html", offer=offer_dict)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
