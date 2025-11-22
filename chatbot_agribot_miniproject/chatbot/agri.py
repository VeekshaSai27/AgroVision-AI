# agri.py
import requests
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# ================================
# ✅ Cached global variables to speed up loading
# ================================
cached_location = None
cached_weather = None


# ================================
# ✅ Prompt Template
# ================================
template = """
You are **AgriBot**, a specialist in agriculture, crops, soil, irrigation, fertilizers, pests, diseases, and weather-based farming.

⚠️ RULES:
- If the question is unrelated to farming, reply ONLY:
  **"I am trained to answer questions related to agriculture and farming only."**
- Keep answers clean, focused, and avoid repeating the question.
- DO NOT repeat the weather data or general pest advice unless relevant.
- ALWAYS format the response clearly.

✅ **Answer Format:**
**🌱 Summary:** (2 sentences)
**✅ Steps:** (bulleted steps or numbered steps)
**🧪 Tips:** (simple tips relevant to the crop)
**🌦 Weather Impact:** (1 short line if relevant, else skip)

📊 **Weather:** {weather_data}
📜 **Context:** {context}
👨‍🌾 **Farmer's Question:** {question}

Now provide a clean, helpful, formatted answer.
"""

# ✅ Use small model that works on your laptop
model = OllamaLLM(model="gemma:2b")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


# ================================
# ✅ Fetch Location (cached)
# ================================
def get_location():
    global cached_location

    if cached_location:
        return cached_location

    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        loc = data.get("loc")
        if loc:
            lat, lon = loc.split(",")
            cached_location = (float(lat), float(lon), data.get("city"), data.get("country"))
            return cached_location
    except:
        pass

    cached_location = (None, None, "Unknown", "Unknown")
    return cached_location


# ================================
# ✅ Fetch Weather (cached)
# ================================
def get_weather(lat, lon):
    global cached_weather

    if cached_weather:
        return cached_weather

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
            f"&hourly=temperature_2m,precipitation&forecast_hours=24"
        )
        data = requests.get(url, timeout=5).json()

        w = data.get("current_weather", {})
        info = f"Temp: {w.get('temperature')}°C | Wind: {w.get('windspeed')} km/h\n"

        hourly = data.get("hourly", {})
        info += "\nNext 24 Hours:\n"
        for t, temp, rain in zip(hourly.get("time", [])[:24],
                                 hourly.get("temperature_2m", [])[:24],
                                 hourly.get("precipitation", [])[:24]):
            info += f"{t} | {temp}°C | {rain} mm\n"

        cached_weather = info
        return info

    except:
        cached_weather = "Weather unavailable"
        return cached_weather


# ================================
# ✅ Main Chat Function
# ================================
def agribot_chat(question, context=""):
    lat, lon, city, country = get_location()
    weather = get_weather(lat, lon)

    result = chain.invoke({
        "context": context,
        "question": question,
        "weather_data": weather
    })

    # ✅ Always return dictionary
    clean = str(result).replace("**", "") 
    return {
        "answer": clean,
        "city": city or "Unknown",
        "country": country or "Unknown",
        "weather": weather or "Unavailable"
    }
