# TEST FILE: Hardcoded Credentials (CWE-798)
import requests

DB_PASSWORD = "admin123"
API_KEY = "sk-hardcoded-secret-key-12345"

def connect_db():
    return f"postgresql://admin:password123@localhost/mydb"

def call_api():
    headers = {"Authorization": "Bearer hardcoded-token-abc123"}
    return requests.get("https://api.example.com/data", headers=headers)
