from google import genai
from google.genai import types
import resend
import os
import uuid
from datetime import datetime
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask import send_file
import io
import secrets

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = "temporary-secret-key-change-later"

# =========================================================
# FILE UPLOAD CONFIG
# =========================================================
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================================================
# EMAIL HELPERS (Using Resend API)
# =========================================================
def send_verification_email(user_email, username, token):
    resend.api_key = os.getenv("RESEND_API_KEY")
    # ...
    verify_url = url_for('verify_email', token=token, _external=True) # <-- Line 53, ye bilkul left se align ho
    html_body = f"""
    <h2>Welcome to ImageTag AI, {username}!</h2>
    <p>Please click the link below to verify your email address and activate your account:</p>
    <a href="{verify_url}" style="padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
    <p>If you didn't sign up, please ignore this email.</p>
    """

    try:
        params = {
            "from": "ImageTag AI <onboarding@resend.dev>",
            "to": [user_email],
            "subject": "Verify Your Email - ImageTag AI",
            "html": html_body
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

def send_reset_email(user_email, username, token):
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    reset_url = url_for('reset_password', token=token, _external=True)

    html_body = f"""
    <h2>Password Reset Request</h2>
    <p>Hi {username},</p>
    <p>We received a request to reset your password for ImageTag AI.</p>
    <p>Click the button below to set a new password:</p>
    <a href="{reset_url}" style="padding: 10px 20px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 5px;">Reset Password</a>
    <p>If you didn't request this, you can safely ignore this email.</p>
    """

    try:
        params = {
            "from": "ImageTag AI <onboarding@resend.dev>",
            "to": [user_email],
            "subject": "Reset Your Password - ImageTag AI",
            "html": html_body
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"❌ Reset email failed: {e}")
        return False

# =========================================================
# GEMINI AI CONFIG (NAYI LIBRARY)
# =========================================================
# 👇 YAHAN APNI GEMINI API KEY PASTE KAREIN 👇
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Nayi library mein client banate hain
client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_image_with_gemini(image_path):
    """Gemini se caption aur tags dono nikalta hai (Nayi Library)."""
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
            prompt = """
        Analyze this image and provide:
        1. A short and punchy caption (Maximum 6-8 words only, no extra details).
        2. A list of 5 relevant tags with confidence percentages (like 95%).
        
        Format exactly like this:
        CAPTION: [short caption here]
        TAGS: tag1: 95%, tag2: 88%, tag3: 80%
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompt,
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
            ]
        )
        
        text = response.text
        caption = ""
        tags_list = []
        
        lines = text.split('\n')
        for line in lines:
            if line.startswith("CAPTION:"):
                caption = line.replace("CAPTION:", "").strip()
            elif line.startswith("TAGS:"):
                tags_str = line.replace("TAGS:", "").strip()
                for tag in tags_str.split(','):
                    parts = tag.strip().split(':')
                    if len(parts) == 2:
                        name = parts[0].strip()
                        conf_str = parts[1].strip().replace('%', '')
                        try:
                            conf = float(conf_str) / 100.0
                            tags_list.append({"name": name, "confidence": conf})
                        except:
                            pass
        
        if not tags_list:
            tags_list = [{"name": "image", "confidence": 0.9}]
            
        return caption, tags_list
        
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return "Could not analyze image.", []

# =========================================================
# DATABASE CONFIG
# =========================================================
# =========================================================
# DATABASE CONFIG
# =========================================================
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "image_tag_db"),
    "charset": "utf8mb4",
    "use_unicode": True,
}

# Agar Aiven (cloud) ka host hai to SSL lagao, localhost ke liye nahi
if DB_CONFIG["host"] != "localhost":
    DB_CONFIG["ssl_ca"] = "ca.pem"
    DB_CONFIG["ssl_verify_cert"] = True

def get_db():
    if "db" not in g:
        try:
            g.db = mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            print(f"❌ Database connection error: {e}")
            raise
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()

def init_db():
    try:
        config_no_db = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        conn = mysql.connector.connect(**config_no_db)
        cursor = conn.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE {DB_CONFIG['database']}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(255) DEFAULT NULL,
                reset_token VARCHAR(255) DEFAULT NULL,
                language VARCHAR(10) DEFAULT 'en',
                email_notifications BOOLEAN DEFAULT TRUE,
                theme VARCHAR(20) DEFAULT 'light',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_username (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                image_name VARCHAR(255) NOT NULL,
                original_name VARCHAR(255),
                caption TEXT,
                tags_json TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_date (user_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ MySQL database initialized: {DB_CONFIG['database']}")
        return True
    except Error as e:
        print(f"❌ MySQL init error: {e}")
        return False

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def validate_upload(file):
    if not file or file.filename == "":
        return False, "No file selected."
    if not allowed_file(file.filename):
        return False, "Invalid file format. Only JPG, JPEG, and PNG are allowed."
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, "Invalid file type. Please upload a valid image."
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        size_mb = size / (1024 * 1024)
        return False, f"File too large ({size_mb:.2f} MB). Maximum allowed is 5 MB."
    if size == 0:
        return False, "File is empty."
    return True, ""

def generate_unique_filename(original_filename):
    ext = original_filename.rsplit(".", 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"{timestamp}_{unique_id}.{ext}"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# =========================================================
# ROUTES
# =========================================================
@app.route("/setup-database")
def setup_database():
    if init_db():
        return "✅ Database tables created successfully! You can now go back and signup."
    else:
        return "❌ Failed to create tables. Check logs."
    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash("Username already taken. Please choose another.", "error")
                return render_template("signup.html")

            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered. Please login instead.", "error")
                return render_template("signup.html")

            verification_token = secrets.token_urlsafe(32)
            password_hash = generate_password_hash(password)
            
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, created_at, is_verified, verification_token) "
                "VALUES (%s, %s, %s, %s, FALSE, %s)",
                (username, email, password_hash, datetime.now(), verification_token)
            )
            db.commit()

            if send_verification_email(email, username, verification_token):
                flash("Account created! Please check your email.", "success")
            else:
                flash("Account created but email could not be sent. Click Resend below.", "warning")
                
            return render_template("verify_notice.html", email=email)

        except Error as e:
            db.rollback()
            print(f"❌ Signup DB error: {e}")
            flash("Something went wrong. Please try again.", "error")
            return render_template("signup.html")
        finally:
            cursor.close()

    return render_template("signup.html")

@app.route("/verify-email/<token>")
def verify_email(token):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE verification_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            flash("Invalid or expired verification link.", "error")
            return redirect(url_for("login"))

        cursor.execute(
            "UPDATE users SET is_verified = TRUE, verification_token = NULL WHERE id = %s",
            (user["id"],)
        )
        db.commit()
        
        flash("Email verified successfully! You can now login.", "success")
        return redirect(url_for("login"))
    finally:
        cursor.close()

@app.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email")
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash("Email not found.", "error")
            return redirect(url_for("signup"))

        if user.get("is_verified") == 1:
            flash("This email is already verified. Please login.", "success")
            return redirect(url_for("login"))

        new_token = secrets.token_urlsafe(32)
        cursor.execute("UPDATE users SET verification_token = %s WHERE id = %s", (new_token, user["id"]))
        db.commit()

        if send_verification_email(email, user["username"], new_token):
            flash("Verification email resent! Please check your inbox.", "success")
        else:
            flash("Failed to send email. Please try again later.", "error")

        return render_template("verify_notice.html", email=email)
    finally:
        cursor.close()

@app.route("/change-email-page")
def change_email_page():
    old_email = request.args.get("email", "")
    if not old_email:
        return redirect(url_for("signup"))
    return render_template("change_email.html", old_email=old_email)

@app.route("/update-email", methods=["POST"])
def update_email():
    old_email = request.form.get("old_email")
    new_email = request.form.get("new_email", "").strip().lower()

    if not new_email:
        flash("Please enter a new email address.", "error")
        return redirect(url_for("change_email_page", email=old_email))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (new_email,))
        if cursor.fetchone():
            flash("This email is already registered. Please use another.", "error")
            return redirect(url_for("change_email_page", email=old_email))

        new_token = secrets.token_urlsafe(32)
        cursor.execute(
            "UPDATE users SET email = %s, verification_token = %s, is_verified = FALSE WHERE email = %s",
            (new_email, new_token, old_email)
        )
        db.commit()

        cursor.execute("SELECT username FROM users WHERE email = %s", (new_email,))
        user = cursor.fetchone()
        user_name = user["username"] if user else "User"

        if send_verification_email(new_email, user_name, new_token):
            flash("Email updated successfully! Check your new inbox.", "success")
        else:
            flash("Email updated, but verification email could not be sent. Click Resend below.", "warning")

        return render_template("verify_notice.html", email=new_email)
    finally:
        cursor.close()

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user:
                reset_token = secrets.token_urlsafe(32)
                cursor.execute("UPDATE users SET reset_token = %s WHERE id = %s", (reset_token, user["id"]))
                db.commit()
                send_reset_email(email, user["username"], reset_token)
                
            flash("If an account exists with this email, a reset link has been sent.", "success")
            return redirect(url_for("login"))
        finally:
            cursor.close()

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE reset_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            flash("Invalid or expired password reset link.", "error")
            return redirect(url_for("login"))

        if request.method == "POST":
            new_pass = request.form.get("new_password", "").strip()
            confirm = request.form.get("confirm_password", "").strip()

            if len(new_pass) < 6:
                flash("Password must be at least 6 characters.", "error")
            elif new_pass != confirm:
                flash("Passwords do not match.", "error")
            else:
                hashed_pass = generate_password_hash(new_pass)
                cursor.execute(
                    "UPDATE users SET password_hash = %s, reset_token = NULL WHERE id = %s",
                    (hashed_pass, user["id"])
                )
                db.commit()
                
                flash("Password reset successfully! You can now login.", "success")
                return redirect(url_for("login"))

        return render_template("reset_password.html", token=token)
    finally:
        cursor.close()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user or not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password.", "error")
                return render_template("login.html")

            if not user.get("is_verified") or user.get("is_verified") == 0:
                flash("Please verify your email address before logging in. Check your inbox.", "error")
                return render_template("login.html")

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["theme"] = user.get("theme", "light")

            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))

        except Error as e:
            print(f"❌ Login DB error: {e}")
            flash("Something went wrong. Please try again.", "error")
            return render_template("login.html")
        finally:
            cursor.close()

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as count FROM analyses WHERE user_id = %s", (session["user_id"],))
        total = cursor.fetchone()["count"]

        cursor.execute(
            "SELECT id, image_name, caption, created_at FROM analyses WHERE user_id = %s ORDER BY created_at DESC LIMIT 3",
            (session["user_id"],)
        )
        recent_rows = cursor.fetchall()
        
        recent_analysis = []
        for row in recent_rows:
            recent_analysis.append({
                "id": row["id"],
                "image_name": row["image_name"],
                "caption": row["caption"],
                "date": row["created_at"].strftime("%Y-%m-%d %H:%M")
            })

        return render_template("dashboard.html", total_analyses=total, total_images=total, total_results=total, recent_analysis=recent_analysis if recent_analysis else None)
    finally:
        cursor.close()

@app.route("/upload")
@login_required
def upload():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if "image" not in request.files:
        return render_template("error.html", error_message="No file part in the request.")

    file = request.files["image"]
    valid, error_msg = validate_upload(file)
    if not valid:
        return render_template("error.html", error_message=error_msg)

    original_name = secure_filename(file.filename)
    unique_name = generate_unique_filename(original_name)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    print("⏳ Sending image to Gemini AI...")
    caption, tags = analyze_image_with_gemini(save_path)
    print(f"✅ Gemini Analysis done. Tags found: {len(tags)}")

    tags_json = json.dumps(tags)
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO analyses (user_id, image_name, original_name, caption, tags_json, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (session["user_id"], unique_name, original_name, caption, tags_json, datetime.now())
        )
        db.commit()
        analysis_id = cursor.lastrowid
        flash("Image analyzed successfully!", "success")
        return redirect(url_for("result", analysis_id=analysis_id))
    except Error as e:
        db.rollback()
        print(f"❌ Analysis DB error: {e}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return render_template("error.html", error_message="Database error. Please try again.")
    finally:
        cursor.close()

@app.route("/result/<int:analysis_id>")
@login_required
def result(analysis_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM analyses WHERE id = %s AND user_id = %s", (analysis_id, session["user_id"]))
        analysis = cursor.fetchone()
        if not analysis:
            flash("Analysis not found.", "error")
            return redirect(url_for("dashboard"))
        try:
            tags_list = json.loads(analysis["tags_json"]) if analysis["tags_json"] else []
        except:
            tags_list = []
        result_data = {
            "id": analysis["id"],
            "image_name": analysis["image_name"],
            "original_name": analysis["original_name"],
            "date": analysis["created_at"].strftime("%Y-%m-%d %H:%M"),
            "caption": analysis["caption"],
            "tags": tags_list,
        }
        return render_template("result.html", result=result_data)
    finally:
        cursor.close()

@app.route("/download-report/<int:analysis_id>")
@login_required
def download_report(analysis_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM analyses WHERE id = %s AND user_id = %s", (analysis_id, session["user_id"]))
        analysis = cursor.fetchone()
        if not analysis:
            flash("Analysis not found.", "error")
            return redirect(url_for("history"))

        try:
            tags_list = json.loads(analysis["tags_json"]) if analysis["tags_json"] else []
        except:
            tags_list = []

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, 750, "ImageTag AI - Analysis Report")
        p.setFont("Helvetica", 12)
        p.drawString(50, 730, "----------------------------------------")
        
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], analysis["image_name"])
        try:
            if os.path.exists(image_path):
                img = ImageReader(image_path)
                p.drawImage(img, 50, 380, width=250, height=320, preserveAspectRatio=True, anchor='nw')
            else:
                p.drawString(50, 500, "[Image file not found on server]")
        except Exception as e:
            print(f"PDF Image Error: {e}")
            p.drawString(50, 500, "[Could not load image]")

        text_x = 330
        p.setFont("Helvetica-Bold", 12)
        p.drawString(text_x, 700, "Image Name: ")
        p.setFont("Helvetica", 12)
        p.drawString(text_x, 680, str(analysis["original_name"])[:35])
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(text_x, 650, "Analysis Date: ")
        p.setFont("Helvetica", 12)
        p.drawString(text_x, 630, analysis["created_at"].strftime("%Y-%m-%d %H:%M"))

        p.setFont("Helvetica-Bold", 12)
        p.drawString(text_x, 600, "AI Service: ")
        p.setFont("Helvetica", 12)
        p.drawString(text_x, 580, "Google Gemini AI")

        p.setFont("Helvetica-Bold", 12)
        p.drawString(text_x, 540, "Image Caption:")
        p.setFont("Helvetica-Oblique", 11)
        
        caption = str(analysis["caption"])
        if len(caption) > 40:
            p.drawString(text_x, 520, caption[:40] + "...")
            p.drawString(text_x, 505, caption[40:80])
        else:
            p.drawString(text_x, 520, caption)

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, 340, "Detected Tags")
        p.setFont("Helvetica", 12)
        
        y_position = 320
        if tags_list:
            for tag in tags_list:
                tag_text = f"• {tag['name'].capitalize()} : {int(tag['confidence'] * 100)}% confidence"
                p.drawString(60, y_position, tag_text)
                y_position -= 20
                if y_position < 60:
                    p.showPage()
                    p.setFont("Helvetica", 12)
                    y_position = 750
        else:
            p.drawString(60, y_position, "No tags detected.")

        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, 30, "Generated by Image Analysis & Tagging Web Application")

        p.showPage()
        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"Analysis_Report_{analysis_id}.pdf", mimetype='application/pdf')
    finally:
        cursor.close()

@app.route("/history")
@login_required
def history():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        search_query = request.args.get("search", "").strip()
        filter_type = request.args.get("filter", "")

        query = "SELECT * FROM analyses WHERE user_id = %s"
        params = [session["user_id"]]

        if search_query:
            query += " AND (original_name LIKE %s OR caption LIKE %s)"
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])

        if filter_type == "saved":
            pass 
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        history_list = []
        for row in rows:
            history_list.append({
                "id": row["id"],
                "image_name": row["image_name"],
                "original_name": row["original_name"],
                "date": row["created_at"].strftime("%Y-%m-%d %H:%M"),
                "caption": row["caption"],
            })

        return render_template("history.html", history=history_list or None)
    finally:
        cursor.close()

@app.route("/history/<int:result_id>")
@login_required
def history_details(result_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM analyses WHERE id = %s AND user_id = %s", (result_id, session["user_id"]))
        analysis = cursor.fetchone()
        if not analysis:
            flash("Analysis not found.", "error")
            return redirect(url_for("history"))
        try:
            tags_list = json.loads(analysis["tags_json"]) if analysis["tags_json"] else []
        except:
            tags_list = []
        result_data = {
            "id": analysis["id"],
            "image_name": analysis["image_name"],
            "original_name": analysis["original_name"],
            "date": analysis["created_at"].strftime("%Y-%m-%d %H:%M"),
            "caption": analysis["caption"],
            "tags": tags_list,
        }
        return render_template("history-detail.html", result=result_data)
    finally:
        cursor.close()

@app.route("/delete-history/<int:result_id>", methods=["POST"])
@login_required
def delete_history(result_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT image_name FROM analyses WHERE id = %s AND user_id = %s", (result_id, session["user_id"]))
        row = cursor.fetchone()
        if not row:
            flash("Analysis not found.", "error")
            return redirect(url_for("history"))

        cursor.execute("DELETE FROM analyses WHERE id = %s AND user_id = %s", (result_id, session["user_id"]))
        db.commit()

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], row["image_name"])
        if os.path.exists(file_path):
            os.remove(file_path)

        flash("Analysis deleted successfully!", "success")
        return redirect(url_for("history"))
    finally:
        cursor.close()

@app.route("/profile")
@login_required
def profile():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
        user = cursor.fetchone()
        if not user:
            flash("User not found. Please login again.", "error")
            return redirect(url_for("logout"))

        cursor.execute("SELECT COUNT(*) as count FROM analyses WHERE user_id = %s", (session["user_id"],))
        total = cursor.fetchone()["count"]

        return render_template("profile.html", user={"username": user["username"], "email": user["email"]}, total_analyses=total)
    finally:
        cursor.close()

@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # User ki saari images delete karo pehle
        cursor.execute("SELECT image_name FROM analyses WHERE user_id = %s", (session["user_id"],))
        images = cursor.fetchall()
        
        for img in images:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], img["image_name"])
            if os.path.exists(file_path):
                os.remove(file_path)

        # Ab user delete karo (Cascade ki wajah se analyses bhi delete ho jayenge)
        cursor.execute("DELETE FROM users WHERE id = %s", (session["user_id"],))
        db.commit()

        # Session clear karo aur bahar nikal do
        session.clear()
        flash("Your account and all data have been permanently deleted.", "success")
        return redirect(url_for("index"))

    except Exception as e:
        db.rollback()
        print(f"❌ Delete Account Error: {e}")
        flash("Could not delete account. Please try again.", "error")
        return redirect(url_for("settings"))
    finally:
        cursor.close()

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        if request.method == "POST":
            email_notifications = 1 if request.form.get("email_notifications") else 0
            
            # Sirf email notifications update kar rahe hain
            cursor.execute(
                "UPDATE users SET email_notifications = %s WHERE id = %s",
                (email_notifications, session["user_id"])
            )
            db.commit()
            flash("Settings updated successfully!", "success")
            return redirect(url_for("settings"))

        # User ki current settings nikaalo
        cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
        user = cursor.fetchone()

        return render_template("settings.html", user=user)
    finally:
        cursor.close()

@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()

            if not username or not email:
                flash("All fields are required.", "error")
            elif len(username) < 3:
                flash("Username must be at least 3 characters.", "error")
            else:
                cursor.execute("SELECT id FROM users WHERE (username = %s OR email = %s) AND id != %s", (username, email, session["user_id"]))
                if cursor.fetchone():
                    flash("Username or email already taken.", "error")
                else:
                    cursor.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", (username, email, session["user_id"]))
                    db.commit()
                    session["username"] = username
                    session["email"] = email
                    flash("Profile updated successfully!", "success")
                    return redirect(url_for("profile"))

        cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
        user = cursor.fetchone()
        return render_template("edit-profile.html", user={"username": user["username"], "email": user["email"]})
    finally:
        cursor.close()

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if request.method == "POST":
            current = request.form.get("current_password", "").strip()
            new_pass = request.form.get("new_password", "").strip()
            confirm = request.form.get("confirm_password", "").strip()

            cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()

            if not check_password_hash(user["password_hash"], current):
                flash("Current password is incorrect.", "error")
            elif len(new_pass) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new_pass != confirm:
                flash("New passwords do not match.", "error")
            elif new_pass == current:
                flash("New password must be different from current.", "error")
            else:
                cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (generate_password_hash(new_pass), session["user_id"]))
                db.commit()
                flash("Password changed successfully!", "success")
                return redirect(url_for("profile"))
        return render_template("change-password.html")
    finally:
        cursor.close()

@app.route("/error")
def error():
    return render_template("error.html", error_message="Sample error.")

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

@app.errorhandler(413)
def too_large(e):
    return render_template("error.html", error_message="File too large. Maximum allowed is 5 MB."), 413


if __name__ == "__main__":
    if init_db():
        # Render ke liye port aur host set karna zaroori hai
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    else:
        print("❌ Server start nahi hua - MySQL setup check karo")