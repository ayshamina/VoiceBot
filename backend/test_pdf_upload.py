import httpx

url = "http://127.0.0.1:8000/api/v1/knowledge/upload"
headers = {
    "Authorization": "Bearer test_admin_token"
}

try:
    with open("bridgeon_info.pdf", "rb") as f:
        files = {"file": ("bridgeon_info.pdf", f, "application/pdf")}
        response = httpx.post(url, headers=headers, files=files, timeout=30.0)
        print("Status code:", response.status_code)
        print("Response json:", response.json())
except Exception as e:
    print("Error:", e)
