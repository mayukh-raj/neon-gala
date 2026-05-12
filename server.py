from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# 🔐 SECRET KEY — use environment variable in production
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

# ☁️ CLOUDINARY CONFIG — loaded from environment variables
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "dgxgpadmb"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "127177625253742"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "l7xR1ZENciKrOTRbfnUHN1rytw4")
)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Neon Gala")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "neongalawebsitebymayukh")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "webm"}
VIDEO_EXTENSIONS = {"mp4", "mov", "webm"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_filetype(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return "video" if ext in VIDEO_EXTENSIONS else "image"

# DB INIT
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS designs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        category TEXT,
        filetype TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# HOME
@app.route("/")
def home():
    conn = get_db()
    data = conn.execute("SELECT * FROM designs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", designs=data)

# ADMIN LOGIN
@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None
    if request.method == "POST":
        if (request.form["username"] == ADMIN_USERNAME and
                request.form["password"] == ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."
    return render_template("admin_login.html", error=error)

# LOGOUT
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    data = conn.execute("SELECT * FROM designs ORDER BY id DESC").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM designs").fetchone()[0]
    conn.close()
    return render_template("admin_dashboard.html", designs=data, total=total)

# UPLOAD
@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    
    files = request.files.getlist("file")
    category = request.form["category"]
    
    conn = get_db()
    for file in files:
        if file and allowed_file(file.filename):
            filetype = get_filetype(file.filename)
            resource_type = "video" if filetype == "video" else "image"
            result = cloudinary.uploader.upload(file, resource_type=resource_type)
            url = result["secure_url"]
            conn.execute(
                "INSERT INTO designs (filename, category, filetype) VALUES (?, ?, ?)",
                (url, category, filetype)
            )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

# DELETE — POST only to prevent accidental deletion via URL
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    conn.execute("DELETE FROM designs WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=False)