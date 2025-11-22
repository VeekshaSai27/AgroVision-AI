#  AgroVision-AI

An AI-powered multi-functional agricultural assistant designed to help farmers, students, and researchers through intelligent predictions, analysis, crop monitoring, and real-time decision support.

AgroVision-AI integrates **Computer Vision**, **Hyperspectral Imaging**, **Soil Intelligence**, **Local LLMs (Ollama)**, and **Government Market Data APIs** into one unified platform.

---

##  Features

### 1️ Leaf Disease Detection  
Upload a crop leaf image, and the system automatically:  
- Detects the disease using a trained computer vision model  
- Identifies symptoms and affected regions  
- Provides actionable treatment suggestions  
- Shares preventive measures to avoid reinfection  

---

### 2️ Hyperspectral Image Analysis  
Hyperspectral Imaging captures hundreds of wavelengths beyond visible light, enabling deep agricultural insights invisible to the human eye.

Using an uploaded hyperspectral image, the system computes:  
- **NDVI (Normalized Difference Vegetation Index)** – plant health  
- **LCI (Leaf Chlorophyll Index)** – chlorophyll & nutrient status  
- **AI-based analytics** – stress detection, early disease indicators, water deficiency signals  

This gives farmers **data-driven insights** to improve yield and detect problems early.

---

### 3️ Soil pH Analyzer  
A smart decision-support tool that takes the following inputs:  
- Current soil pH value  
- Area & soil volume  
- Soil type  
- Crop type  
- Present temperature  
- Moisture level  
- Percentage of organic matter  
- Soil depth  

The system generates detailed corrective actions, for example:  
- *“Check for signs of pest infestation and remove affected parts immediately. Apply fertilizers at 0.5–1.0 lbs/acre and mix thoroughly before planting.”*  
- *“Water deeply once a week and monitor moisture levels. Avoid heavy rain exposure to prevent nutrient washout.”*  
- *“Consider using cover crops to improve soil structure and reduce weed competition.”*  

It also provides **safety instructions**, such as use of gloves, eye protection, and safe handling of crop additives.

---

### 4️ AI Chatbot  
A smart farm assistant that uses **Ollama LLM models** to give advice based on:  
- The user’s question  
- Current climatic conditions  
- Location  
- Crop type  

**Example:**  
**User:** *“Should I water my plants today?”*  
**Chatbot:** Considers rainfall, humidity, soil dryness & crop type → returns accurate advice.

---

### 5️ Market Price Predictor  
This feature fetches **real-time government data** from **data.gov.in** to help farmers avoid middlemen exploitation.  
It:  
- Takes crop name and location  
- Fetches the latest mandi (market) prices  
- Plots a price graph showing trends  
- Helps farmers make informed selling decisions  

---

##  Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Flask (Python) |
| AI Models | Ollama (Gemma2:2b, Llama3, etc.) |
| ML/AI | Computer Vision, Hyperspectral Analytics, LangChain |
| Frontend | HTML, CSS, JavaScript |
| Data Source | Government API (data.gov.in) |


---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```
### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Start the app
```bash
python main_app.py
```
### 4. Open in browser
```cpp
http://127.0.0.1:5000
```

---

## License
This project is licensed under the MIT License. Feel free to use, fork, and contribute.

## Acknowledgements
Thanks to open-source datasets, tools, and libraries used in this project.
