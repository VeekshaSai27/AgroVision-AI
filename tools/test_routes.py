import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main_app import create_app

app = create_app()
client = app.test_client()

routes = ["/", "/chatbot/", "/plant/", "/ph/", "/market/", "/health"]

print("Testing routes with Flask test client:\n")
for r in routes:
    try:
        resp = client.get(r)
        status = resp.status_code
        body = resp.get_data(as_text=True)[:400]
        print(f"{r:12} -> {status}")
        if status != 200:
            print("  Response snippet:", body.replace('\n',' ')[:200])
        else:
            # show a short marker of content
            print("  OK - snippet:", body.replace('\n',' ')[:200])
    except Exception as e:
        print(f"{r:12} -> ERROR: {e}")

print('\nDone')
