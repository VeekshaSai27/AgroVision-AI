from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev_secret")

# Backend API URL - default to localhost where FastAPI might run
API_URL = os.environ.get("DETECT_API_URL", "http://localhost:8000")

# Try to import local detection helper. If unavailable, we'll fallback to proxying to the API.
try:
    from utils import convert_image_to_base64_and_test
    LOCAL_DETECT_AVAILABLE = True
except Exception:
    convert_image_to_base64_and_test = None
    LOCAL_DETECT_AVAILABLE = False


@app.route("/", methods=["GET"])
def index():
    return render_template("leaf_index.html", result=None)


@app.route("/detect", methods=["POST"])
def detect():
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))
    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))
    # Read the file bytes once
    file_bytes = file.read()

    # If local detector is available, use it directly (no FastAPI required)
    if LOCAL_DETECT_AVAILABLE:
        try:
            result = convert_image_to_base64_and_test(file_bytes)
            if result is None:
                flash("Local detection failed or returned no result")
                return render_template("leaf_index.html", result=None)
            return render_template("leaf_index.html", result=result)
        except Exception as e:
            flash(f"Local detection error: {str(e)}")
            # Fall through to try proxying to API

    # Fallback: forward the uploaded file to the existing API endpoint
    try:
        files = {"file": (file.filename, file_bytes, file.content_type)}
        resp = requests.post(f"{API_URL}/disease-detection-file", files=files, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            return render_template("leaf_index.html", result=result)
        else:
            flash(f"API returned status {resp.status_code}")
            return render_template("leaf_index.html", result=None)
    except requests.RequestException as e:
        flash(f"Error contacting detection API: {str(e)}")
        return render_template("leaf_index.html", result=None)


if __name__ == "__main__":
    # Run on port 5000 by default
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
