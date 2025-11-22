import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from main_app import create_app
app = create_app()
client = app.test_client()
paths = [
    '/chatbot/static/logo.svg',
    '/ph/static/images/ph_sensor.png',
    '/plant/static/analysis/placeholder.png'
]
for p in paths:
    try:
        r = client.get(p)
        print(p, '->', r.status_code, 'length=', len(r.get_data()))
    except Exception as e:
        print(p, 'ERROR', e)
