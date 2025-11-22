# app.py (Blueprint version)
from flask import Blueprint, render_template, request, redirect, url_for

# Support both direct run and package import
try:
    from .agri import agribot_chat
except ImportError:
    from agri import agribot_chat

chatbot_bp = Blueprint(
    "chatbot", __name__,
    template_folder="templates",
    static_folder="static"
)

CHAT_HISTORY = []


@chatbot_bp.route("/")
def index():
    if CHAT_HISTORY:
        last = CHAT_HISTORY[-1]
        city = last["city"]
        country = last["country"]
        weather = last["weather"]
    else:
        city = "Unknown"
        country = "Unknown"
        weather = "Weather unavailable"

    return render_template(
        "index.html",
        history=CHAT_HISTORY,
        city=city,
        country=country,
        weather=weather
    )


@chatbot_bp.route("/ask", methods=["POST"])
def ask():
    q = (request.form.get("question") or "").strip()
    if not q:
        return redirect(url_for("chatbot.index"))

    if q.lower() in {"exit", "quit", "reset"}:
        CHAT_HISTORY.clear()
        return redirect(url_for("chatbot.index"))

    # Build conversation context
    context = ""
    for item in CHAT_HISTORY:
        context += f"Farmer: {item['question']}\nAgriBot: {item['answer']}\n"

    # Get answer from model
    out = agribot_chat(q, context)

    CHAT_HISTORY.append({
        "question": q,
        "answer": out.get("answer", ""),
        "city": out.get("city", "Unknown"),
        "country": out.get("country", "Unknown"),
        "weather": out.get("weather", "Weather unavailable")
    })

    return redirect(url_for("chatbot.index"))


@chatbot_bp.route("/reset", methods=["POST"])
def reset():
    CHAT_HISTORY.clear()
    return redirect(url_for("chatbot.index"))
