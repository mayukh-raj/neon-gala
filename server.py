from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2
import os
import cloudinary
import cloudinary.uploader
 
app = Flask(__name__)
 
app.secret_key = os.environ.get("SECRET_KEY", "neongala2025secretkey")
 
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
 
def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn
 
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS designs (
        id SERIAL PRIMARY KEY,
        filename TEXT,
        category TEXT,
        filetype TEXT
    )""")
    conn.commit()
    conn.close()
 
init_db()
 
@app.route("/")
def home():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM designs ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return render_template("index.html", designs=data)
 
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
 
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))
 
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM designs ORDER BY id DESC")
    data = c.fetchall()
    c.execute("SELECT COUNT(*) FROM designs")
    total = c.fetchone()[0]
    conn.close()
    return render_template("admin_dashboard.html", designs=data, total=total)
 
@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    files = request.files.getlist("file")
    category = request.form["category"]
    conn = get_db()
    c = conn.cursor()
    for file in files:
        if file and allowed_file(file.filename):
            filetype = get_filetype(file.filename)
            resource_type = "video" if filetype == "video" else "image"
            result = cloudinary.uploader.upload(file, resource_type=resource_type, format="mp4" if filetype == "video" else None)
            url = result["secure_url"]
            c.execute(
                "INSERT INTO designs (filename, category, filetype) VALUES (%s, %s, %s)",
                (url, category, filetype)
            )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))
 
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM designs WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))
 
if __name__ == "__main__":
    app.run(debug=False)