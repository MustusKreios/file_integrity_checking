import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from db import get_db_connection
from hashing import generate_enhanced_hash
from config import UPLOAD_FOLDER, SECRET_KEY

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file selected!")
        return redirect(url_for("index"))

    file = request.files["file"]
    name = request.form.get("name")
    email = request.form.get("email")
    student_id = request.form.get("student_id")  # Ensure this is stored correctly

    if not name or not email or not student_id:
        flash("All fields (Name, Email, Student ID) are required!")
        return redirect(url_for("index"))

    if file.filename == "":
        flash("No file selected!")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Compute Hash
    file_size = os.path.getsize(file_path)
    file_hash = generate_enhanced_hash(filename, file_size)

    # Save to database
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO students (name, email, student_id, file_name, file_path, file_hash) 
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_num
                """, (name, email, student_id, filename, file_path, file_hash))
                new_id = cur.fetchone()[0]  # Get the newly inserted id_num
                conn.commit()
                flash(f"File uploaded successfully! ID Number: {new_id}")  # Show ID for retrieval
    except Exception as e:
        flash(f"Database error: {e}")
        return redirect(url_for("index"))

    return redirect(url_for("index"))

@app.route("/download/")
def download_file():
    id_num = request.args.get("id_num", type=int)  # Extract id_num from query parameters
    if not id_num:
        flash("❌ No ID provided!")
        return redirect(url_for("index"))

    print(f"🔍 Fetching file for ID: {id_num}")  # Debugging

    # Fetch file details from DB
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT file_name, file_path, file_hash FROM students WHERE id_num = %s", (id_num,))
            result = cur.fetchone()
            print(f"🔎 Query Result: {result}")  # Debugging

    if not result:
        flash("❌ File not found in the database!")
        return redirect(url_for("index"))

    filename, file_path, stored_hash = result
    print(f"📁 File Path: {file_path}")  # Debugging

    if not os.path.exists(file_path):
        flash("⚠️ File does not exist on the server!")
        return redirect(url_for("index"))

    # Recompute Hash
    file_size = os.path.getsize(file_path)
    new_hash = generate_enhanced_hash(filename, file_size)

    # Compare Hashes
    if new_hash != stored_hash:
        flash("❌ File has been tampered with!")
        return render_template("confirm_download.html", id_num=id_num)  # Pass id_num to the template

    flash("✅ File is authentic!")
    return send_file(file_path, as_attachment=True)

@app.route("/proceed_download")
def proceed_download():
    id_num = request.args.get("id_num", type=int)  # Extract id_num from query parameters
    if not id_num:
        flash("❌ No ID provided!")
        return redirect(url_for("index"))

    # Fetch file details from DB
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT file_name, file_path FROM students WHERE id_num = %s", (id_num,))
            result = cur.fetchone()

    if not result:
        flash("❌ File not found in the database!")
        return redirect(url_for("index"))

    filename, file_path = result

    if not os.path.exists(file_path):
        flash("⚠️ File does not exist on the server!")
        return redirect(url_for("index"))

    # Proceed with the download
    return send_file(file_path, as_attachment=True)



if __name__ == "__main__":
    app.run(debug=True)
