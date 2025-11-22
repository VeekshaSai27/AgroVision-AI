import importlib, traceback, os, sys

# Ensure project root is on sys.path so package imports resolve when run from tools/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

modules = [
    'chatbot_agribot_miniproject.chatbot.app',
    'market_analaysis_miniproject.Market_Analysis.utils.market_api',
    'ph_analyisis_miniProject.Ph_Analyzer.app',
    'plant_hyperspectral_cnn_miniproject.Plant_disease_detection.app'
]

for m in modules:
    print('\n--- Importing', m, '---')
    try:
        mod = importlib.import_module(m)
        print(m, 'OK')
    except Exception:
        print(m, 'FAILED')
        traceback.print_exc()
