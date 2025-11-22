# 🌾 Hyperspectral Crop Analyzer

Flask web app for hyperspectral cube analysis:
- Computes NDVI, LCI, and vegetation health
- Trains a light 1D CNN if labels are provided
- Uses **TinyLlama 1.1B** for JSON-based AI summaries

## ⚙️ Run

```bash
pip install -r requirements.txt
ollama pull tinyllama:1.1b
python app.py
