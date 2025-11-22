from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from.utils import calculate_treatment
from.ollama_utils import get_ai_advice

ph_bp = Blueprint(
    "ph", __name__,
    template_folder="templates",
    static_folder="static"
)

@ph_bp.route("/")
def index():
    return render_template("ph_index.html")

@ph_bp.route("/analyze", methods=["POST"])
def analyze():
    ph = float(request.form.get("ph", 7.0))
    volume = float(request.form.get("volume", 10))
    area = float(request.form.get("area", 100))
    soil_type = request.form.get("soil", "Loamy")
    crop = request.form.get("crop", "Tomato")

    result = calculate_treatment(ph, soil_type)
    ai_advice = get_ai_advice(crop, soil_type, ph, result["status"])

    return render_template(
        "ph_result.html",
        ph=ph,
        volume=volume,
        area=area,
        soil=soil_type,
        crop=crop,
        result=result,
        ai_advice=ai_advice,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
