import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main_app import create_app

app = create_app()
print('\n=== URL MAP ===')
for r in app.url_map.iter_rules():
    print(r.rule, '->', r.endpoint)
print('===============\n')
