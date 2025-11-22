import os
from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from .model_hyperspectral import run_hyperspectral_analysis

plant_bp = Blueprint(
    "plant", __name__,
    template_folder="templates",
    static_folder="static"
)

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE, "static", "uploads")
OUT_DIR = os.path.join(BASE, "static", "analysis")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

ALLOWED = {"npy"}
def allowed(fn): return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED

@plant_bp.route("/")
def index():
    return render_template("plant_index.html")

@plant_bp.route("/analyze", methods=["POST"])
def analyze():
    data_file = request.files.get("cube")
    label_file = request.files.get("labels")

    if not data_file or not allowed(data_file.filename):
        return redirect(url_for("plant.index"))

    data_path = os.path.join(UPLOAD_DIR, secure_filename(data_file.filename))
    data_file.save(data_path)

    label_path = None
    if label_file and allowed(label_file.filename):
        label_path = os.path.join(UPLOAD_DIR, secure_filename(label_file.filename))
        label_file.save(label_path)

    result = run_hyperspectral_analysis(data_path, label_path, OUT_DIR)
    # blueprint-aware static URL:
    plot_url = url_for("plant.static", filename=f"analysis/{result['plot_file']}")
    return render_template("plant_result.html", result=result, plot_url=plot_url)
