import requests
import json

url = "http://127.0.0.1:5000/api/detect/file"
headers = {'Content-Type': 'application/json; charset=utf-8'}
data = {"filepath": r"d:\falldown\back\uploads\跌倒视频5.mp4"}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False).encode('utf-8'))
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")