# def calculate_treatment(ph, soil_type):
#     targets = {"loamy": 6.5, "sandy": 6.0, "clay": 7.0}
#     target_ph = targets.get(soil_type.lower(), 6.5)
#     diff = ph - target_ph

#     factors = {"loamy": 175, "sandy": 120, "clay": 200}
#     factor = factors.get(soil_type.lower(), 175)

#     if diff > 0:  # Too alkaline
#         sulfur = factor * diff
#         aluminum_sulfate = sulfur * 1.6
#         return {
#             "status": "Too Alkaline",
#             "sulfur_g": round(sulfur, 1),
#             "aluminum_sulfate_g": round(aluminum_sulfate, 1),
#         }
#     elif diff < 0:  # Too acidic
#         lime = abs(diff) * 200
#         return {
#             "status": "Too Acidic",
#             "lime_g": round(lime, 1),
#         }
#     else:
#         return {"status": "Neutral", "message": "No treatment needed"}
def calculate_treatment(ph, soil_type, temperature=None, moisture=None, organic_matter=None):
    # Target pH based on texture
    targets = {"loamy": 6.5, "sandy": 6.0, "clay": 7.0}
    target_ph = targets.get(soil_type.lower(), 6.5)

    # Base factors per 1 pH adjustment
    sulfur_factor = {"loamy": 175, "sandy": 120, "clay": 200}
    lime_factor = {"loamy": 200, "sandy": 200, "clay": 200}

    soil = soil_type.lower()
    diff = ph - target_ph

    # Environmental modifier (kept simple)
    modifier = 1.0

    # Temperature adjustment
    if temperature is not None:
        if temperature >= 25:
            modifier *= 0.9      # reactions faster
        elif temperature <= 10:
            modifier *= 1.1      # slower

    # Moisture adjustment
    if moisture is not None:
        if moisture < 20:
            modifier *= 1.1      # too dry, slower
        elif 35 <= moisture <= 60:
            modifier *= 0.95     # ideal moisture

    # Organic matter adjustment
    if organic_matter is not None:
        if organic_matter >= 8:
            modifier *= 1.12     # high buffering
        elif organic_matter <= 2:
            modifier *= 0.95     # low buffering

    # Clamp modifier
    modifier = max(0.75, min(modifier, 1.35))

    # --- DECISION LOGIC (same as your original) ---
    if diff > 0:  # Too alkaline
        sulfur = sulfur_factor.get(soil, 175) * diff * modifier
        aluminum_sulfate = sulfur * 1.6
        
        return {
            "status": "Too Alkaline",
            "sulfur_g": round(sulfur, 1),
            "aluminum_sulfate_g": round(aluminum_sulfate, 1),
            "modifier": round(modifier, 3),
        }

    elif diff < 0:  # Too acidic
        lime = abs(diff) * lime_factor.get(soil, 200) * modifier
        return {
            "status": "Too Acidic",
            "lime_g": round(lime, 1),
            "modifier": round(modifier, 3),
        }

    else:
        return {
            "status": "Neutral",
            "message": "No treatment needed",
            "modifier": round(modifier, 3),
        }
