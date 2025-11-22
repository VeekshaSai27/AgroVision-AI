from flask import Blueprint, render_template, request, jsonify
import logging

from .api_service import get_prices, get_states, get_commodities

market_bp = Blueprint(
    "market",
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

logging.basicConfig(level=logging.INFO)


@market_bp.route("/")
def index():
    return render_template("market.html")


@market_bp.route("/api/prices")
def api_prices():
    commodity = request.args.get("commodity")
    state = request.args.get("state")

    try:
        limit = int(request.args.get("limit") or 500)
        offset = int(request.args.get("offset") or 0)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid limit/offset"}), 400

    result = get_prices(commodity=commodity, state=state, limit=limit, offset=offset)

    if isinstance(result, dict) and result.get("error"):
        return jsonify({"success": False, "error": result["error"]}), 500

    return jsonify({"success": True, "records": result})


@market_bp.route("/api/states")
def api_states():
    result = get_states(limit=1000)

    if isinstance(result, dict) and result.get("error"):
        return jsonify({"success": False, "error": result["error"]}), 500

    return jsonify({"success": True, "states": result})


@market_bp.route("/api/commodities")
def api_commodities():
    state = request.args.get("state")

    result = get_commodities(limit=1000, state=state)

    if isinstance(result, dict) and result.get("error"):
        return jsonify({"success": False, "error": result["error"]}), 500

    return jsonify({"success": True, "commodities": result})
