import urllib.request
import json

url = 'http://localhost:5000/compare'
data = json.dumps({"molecule1": "Aspirin", "molecule2": "Metformin", "language": "en"}).encode('utf-8')
headers = {'Content-Type': 'application/json'}
req = urllib.request.Request(url, data=data, headers=headers)

try:
    with urllib.request.urlopen(req) as res:
        print("Status Code:", res.getcode())
        print("Response:", res.read().decode('utf-8')[:200])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Error text:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", str(e))
