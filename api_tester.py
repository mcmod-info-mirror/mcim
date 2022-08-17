import traceback
import requests
urls = [
    "http://127.0.0.1:8000/"
]
for url in urls:
    try:
        res = requests.get(url)
        print(res.status_code, res.text)
    except KeyboardInterrupt:
        exit(1)
    except Exception:
        traceback.print_exc()