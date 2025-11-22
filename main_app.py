# import os
# from flask import Flask, render_template, jsonify
# from dotenv import load_dotenv

# # ✅ Import Blueprints from each sub-project
# from chatbot_agribot_miniproject.chatbot.app import chatbot_bp
# from market_api_using_data_gov.agri_market_app.backend.app import market_bp
# from ph_analyisis_miniProject.Ph_Analyzer.app import ph_bp
# from plant_hyperspectral_cnn_miniproject.Plant_disease_detection.app import plant_bp

# # Load environment variables from .env if available
# load_dotenv()


# def create_app():
#     app = Flask(
#         __name__,
#         template_folder="templates",  # home.html lives here
#         static_folder="static"        # for hero image, etc.
#     )

#     # Secret key for session / CSRF
#     app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

#     # ✅ Register blueprints with prefixes
#     app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
#     app.register_blueprint(market_bp,  url_prefix="/market")
#     app.register_blueprint(ph_bp,      url_prefix="/ph")
#     app.register_blueprint(plant_bp,   url_prefix="/plant")

#     # ✅ Main landing page
#     @app.route("/")
#     def home():
#         return render_template("home.html")

#     # ✅ Health check route
#     @app.route("/health")
#     def health():
#         return jsonify({"status": "ok"}), 200

#     # ✅ Log all routes on startup for debugging
#     print("\n🔗 Registered Routes:")
#     with app.app_context():
#         for rule in app.url_map.iter_rules():
#             print(f"{rule.endpoint:35s} -> {rule}")
#     print("✅ App initialized successfully!\n")

#     return app


# if __name__ == "__main__":
#     app = create_app()
#     port = int(os.getenv("PORT", 5000))
#     app.run(host="0.0.0.0", port=port, debug=True)

# main_app.py (modified)
# main_app.py (use this whole file or replace top portion and KEEP your create_app())
import os
import sys
import traceback
import importlib.util
import requests
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

# ✅ Import existing blueprints
from chatbot_agribot_miniproject.chatbot.app import chatbot_bp
from market_api_using_data_gov.agri_market_app.backend.app import market_bp
from ph_analyisis_miniProject.Ph_Analyzer.app import ph_bp
from plant_hyperspectral_cnn_miniproject.Plant_disease_detection.app import plant_bp
load_dotenv()

# =====================================================================
#   AUTO–DETECT & IMPORT leaf_frontend_bp.py 
# =====================================================================

def find_leaf_bp_file(start_dir=None, target_name="leaf_frontend_bp.py"):
    """
    Recursively search for leaf_frontend_bp.py anywhere inside the project.
    Returns absolute path to the file or None.
    """
    if start_dir is None:
        start_dir = os.path.dirname(__file__)

    for root, dirs, files in os.walk(start_dir):
        if target_name in files:
            return os.path.join(root, target_name)
    return None


def load_blueprint_from_path(file_path, module_name="leaf_frontend_bp"):
    """
    Loads the blueprint module directly from file path.
    Returns (blueprint, error_traceback).
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        # Ensure the module's directory is on sys.path while executing so
        # local imports (like `from utils import ...`) resolve correctly.
        module_dir = os.path.dirname(file_path)
        inserted = False
        if module_dir and module_dir not in sys.path:
            sys.path.insert(0, module_dir)
            inserted = True
        try:
            spec.loader.exec_module(module)
        finally:
            if inserted:
                try:
                    sys.path.remove(module_dir)
                except ValueError:
                    pass

        bp = getattr(module, "leaf_bp", None)
        return bp, None
    except Exception:
        return None, traceback.format_exc()


# Try to load leaf blueprint
leaf_bp = None
leaf_path = find_leaf_bp_file()

print("\n================ LEAF BLUEPRINT LOADING ================")
if leaf_path:
    print(f"[INFO] Found leaf_frontend_bp.py at:\n  {leaf_path}")

    leaf_bp, err = load_blueprint_from_path(leaf_path)

    if leaf_bp is not None:
        print("[INFO] leaf_bp loaded successfully.")
    else:
        print("[ERROR] Could not load leaf_bp!\nTraceback:\n")
        print(err)
else:
    print("[WARN] leaf_frontend_bp.py NOT FOUND anywhere under project.")
print("========================================================\n")

# =====================================================================
#   FLASK APP FACTORY
# =====================================================================

def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # Register existing blueprints
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(market_bp,  url_prefix="/market")
    app.register_blueprint(ph_bp,      url_prefix="/ph")
    app.register_blueprint(plant_bp,   url_prefix="/plant")

    # Register Leaf blueprint
    if leaf_bp:
        try:
            app.register_blueprint(leaf_bp, url_prefix="/plant/leaf")
            print("[INFO] Registered leaf blueprint at /plant/leaf")
        except Exception:
            print("[ERROR] Could not register leaf blueprint:")
            traceback.print_exc()
    else:
        print("[WARN] leaf blueprint NOT registered (file missing or error loading).")

    # Quick health check for detection API (informational only)
    try:
        detect_api = os.environ.get("DETECT_API_URL", "http://localhost:8000")
        r = requests.get(detect_api, timeout=2)
        print(f"[INFO] Detection API at {detect_api} responded: {r.status_code}")
    except Exception:
        print("[WARN] Detection API at http://localhost:8000 is not reachable.\n" \
              "If you rely on the local detection API start it with: uvicorn app:app --reload --port 8000")

    # Home Route
    @app.route("/")
    def home():
        return render_template("home.html")

    # Health Route
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # Print all routes
    print("\n🔗 REGISTERED ROUTES")
    with app.app_context():
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint:35s} -> {rule}")
    print("========================================================")
    print("✅ App initialized successfully!\n")

    return app

# =====================================================================
#   RUN SERVER
# =====================================================================

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
