import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

leaf_bp = Blueprint(
    "leaf",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/leaf-static"
)

API_URL = os.environ.get("DETECT_API_URL", "http://localhost:8000")

try:
    from utils import convert_image_to_base64_and_test
    LOCAL_DETECT_AVAILABLE = True
except Exception:
    convert_image_to_base64_and_test = None
    LOCAL_DETECT_AVAILABLE = False


@leaf_bp.route("/", methods=["GET"])
def index():
    return render_template("leaf_index.html", result=None)


@leaf_bp.route("/detect", methods=["POST"])
def detect():
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("leaf.index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("leaf.index"))

    file_bytes = file.read()

    # 1) Try local detector if available
    if LOCAL_DETECT_AVAILABLE:
        try:
            result = convert_image_to_base64_and_test(file_bytes)
            if result:
                return render_template("leaf_index.html", result=result)
        except Exception:
            current_app.logger.exception("Local detection error")

    # 2) Try remote detection API with retries and sensible timeouts
    try:
        session = requests.Session()
        retries = Retry(total=2, backoff_factor=0.5, status_forcelist=(502, 503, 504))
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        files = {"file": (file.filename, file_bytes, file.content_type)}
        resp = session.post(f"{API_URL}/disease-detection-file", files=files, timeout=10)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            current_app.logger.error("Invalid JSON from detection API")
            flash("Detection service returned an unexpected response; try again later.")
            return render_template("leaf_index.html", result=None)

        return render_template("leaf_index.html", result=data)
    except requests.RequestException as e:
        current_app.logger.exception("Error contacting detection API")
        flash(
            "Detection service is unavailable. Start the detection API (uvicorn app:app --reload --port 8000),\n"
            "or set the DETECT_API_URL environment variable to a reachable endpoint."
        )
        return render_template("leaf_index.html", result=None)
