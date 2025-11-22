# ollama_utils.py
import subprocess
import shutil
import textwrap
import time

# Model and timeouts
MODEL = "tinyllama:latest"
RUN_TIMEOUT = 120     # increase timeout so the small model has enough time on slow machines
RETRIES = 2           # try a couple times (useful if model is initializing)

def _local_fallback_advice(crop, soil_type, ph, status):
    status_lower = (status or "").lower()
    if "alkal" in status_lower:
        return "- Soil pH high. Apply elemental sulfur slowly; water after application. Re-test in 4-8 weeks. Wear gloves."
    if "acid" in status_lower:
        return "- Soil pH low. Apply agricultural lime evenly; re-test in 4-8 weeks. Wear gloves and avoid dust."
    return "- pH near target. No immediate treatment; monitor seasonally."

def _build_prompt(crop, soil_type, ph, status):
    prompt = textwrap.dedent(f"""
        You are an agricultural advisor giving very short, practical advice for smallholder farmers.
        Keep the response under 80 words, in simple bullet points (each starts with '-').
        Include what to apply, safety measures, and monitoring tips. Avoid technical jargon.

        Crop: {crop}
        Soil type: {soil_type}
        Measured pH: {ph} ({status})
    """).strip()
    return prompt

def get_ai_advice(crop, soil_type, ph, status):
    # Quick check: ollama CLI present?
    if shutil.which("ollama") is None:
        return "AI advice unavailable: 'ollama' CLI not found.\n\nFallback:\n" + _local_fallback_advice(crop, soil_type, ph, status)

    prompt = _build_prompt(crop or "Unknown crop", soil_type or "Unknown soil", ph, status or "Status unknown")

    for attempt in range(1, RETRIES + 1):
        try:
            proc = subprocess.run(
                ["ollama", "run", MODEL],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT,
            )

            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip().lower()

            # Successful short-text output
            if proc.returncode == 0 and stdout:
                # truncate enormous outputs just in case
                words = stdout.split()
                if len(words) > 200:
                    return " ".join(words[:160]) + " …"
                return stdout

            # If stderr indicates model downloading / pulling, tell the user
            if "pull" in stderr or "download" in stderr or "downloading" in stderr:
                return f"AI advice unavailable: model '{MODEL}' is downloading. Run:\n\n  ollama pull {MODEL}\n\nand retry after it finishes."

            # If model not found locally, suggest pull
            if "not found" in stderr or "no such" in stderr or "missing" in stderr:
                return f"AI advice unavailable: model '{MODEL}' not found. Try:\n\n  ollama pull {MODEL}\n"

            # If stdout empty but no clear error, and this was a first attempt, wait a bit and retry
            if attempt < RETRIES:
                time.sleep(2)  # short backoff and retry
                continue

            # final fallback after retries
            break

        except subprocess.TimeoutExpired:
            # If timed out, try once more (unless last attempt)
            if attempt < RETRIES:
                time.sleep(2)
                continue
            return f"AI advice unavailable: model '{MODEL}' timed out after {RUN_TIMEOUT} seconds."
        except FileNotFoundError:
            return "AI advice unavailable: 'ollama' CLI not found."
        except Exception as e:
            # unexpected error: return concise message and fallback advice
            return f"AI advice unavailable: {e}\n\nFallback:\n" + _local_fallback_advice(crop, soil_type, ph, status)

    # All attempts failed -> return fallback guidance + troubleshooting
    fallback = _local_fallback_advice(crop, soil_type, ph, status)
    troubleshooting = (
        f"\n\nAI models not reachable. To enable AI advice, run:\n\n  ollama pull {MODEL}\n\n"
        "Then restart the app. If you prefer no AI, the app will still show practical fallback guidance."
    )
    return "AI advice unavailable: tiny model missing or not responding.\n\nFallback:\n" + fallback + troubleshooting
