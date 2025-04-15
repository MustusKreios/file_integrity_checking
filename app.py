import os
import time
from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from db import get_db_connection
from hashing import generate_enhanced_hash, enhanced_block_processing, calculate_entropy
from existingAlgo import generate_original_hash, calculate_entropy as calculate_original_entropy
from config import UPLOAD_FOLDER, SECRET_KEY

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_file_info(id_num):
    """Helper function to fetch file info from the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT file_name, file_path, file_hash FROM students WHERE id_num = %s", (id_num,))
                return cur.fetchone()
    except Exception as e:
        flash(f"Database error: {e}")
        return None

def is_valid_file_path(file_path):
    """Ensure the file path is within the UPLOAD_FOLDER."""
    return os.path.commonpath([file_path, app.config["UPLOAD_FOLDER"]]) == app.config["UPLOAD_FOLDER"]

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
    student_id = request.form.get("student_id")

    if not name or not email or not student_id:
        flash("All fields (Name, Email, Student ID) are required!")
        return redirect(url_for("index"))

    if file.filename == "":
        flash("No file selected!")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    # -----------------------
    # ORIGINAL ALGORITHM
    # -----------------------
    start_original = time.time()
    original_hash, original_block_info, original_bits_appended = generate_original_hash(file_path)
    original_time = time.time() - start_original
    original_entropy = calculate_original_entropy(file_path)

    # -----------------------
    # ENHANCED ALGORITHM
    # -----------------------
    start_enhanced = time.time()
    enhanced_hash = generate_enhanced_hash(file_path)
    enhanced_time = time.time() - start_enhanced
    block_info, bits_appended, memory_waste = enhanced_block_processing(file_size)
    enhanced_entropy = calculate_entropy(file_path)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO students (name, email, student_id, file_name, file_path, file_hash) 
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_num
                """, (name, email, student_id, filename, file_path, enhanced_hash))
                new_id = cur.fetchone()[0]
                conn.commit()
                flash(f"File uploaded successfully! ID Number: {new_id}")
    except Exception as e:
        flash(f"Database error: {e}")
        return redirect(url_for("index"))

    return render_template(
        "index.html",
        old_metrics={
            "hash": original_hash,
            "key_time": round(original_time * 1000, 2),  # Convert to ms
            "block_time": original_block_info,  # Block size details
            "entropy": original_entropy,  # Entropy for the original algorithm
            "bits_appended": original_bits_appended  # Bits appended
        },
        enhanced_metrics={
            "hash": enhanced_hash,
            "key_time": round(enhanced_time * 1000, 2),  # Convert to ms
            "block_time": block_info,  # Block size details
            "entropy": enhanced_entropy  # Entropy for the enhanced algorithm
        },
        block_info=block_info,
        wasted_bits=bits_appended,
        memory_waste=memory_waste
    )

@app.route("/download/")
def download_file():
    id_num = request.args.get("id_num", type=int)
    if not id_num:
        flash("❌ No ID provided!")
        return redirect(url_for("index"))

    result = get_file_info(id_num)
    if not result:
        flash("❌ File not found in the database!")
        return redirect(url_for("index"))

    filename, file_path, stored_hash = result
    if not is_valid_file_path(file_path) or not os.path.exists(file_path):
        flash("⚠️ File does not exist on the server!")
        return redirect(url_for("index"))

    recomputed_hash = generate_enhanced_hash(file_path)
    if recomputed_hash != stored_hash:
        flash("❌ File has been tampered with!")
        return render_template("confirm_download.html", id_num=id_num)

    flash("✅ File is authentic!")
    return send_file(file_path, as_attachment=True)

@app.route("/proceed_download")
def proceed_download():
    id_num = request.args.get("id_num", type=int)
    if not id_num:
        flash("❌ No ID provided!")
        return redirect(url_for("index"))

    result = get_file_info(id_num)
    if not result:
        flash("❌ File not found in the database!")
        return redirect(url_for("index"))

    filename, file_path, _ = result
    if not is_valid_file_path(file_path) or not os.path.exists(file_path):
        flash("⚠️ File does not exist on the server!")
        return redirect(url_for("index"))

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)