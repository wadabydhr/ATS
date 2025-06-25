import os
from datetime import datetime, timedelta
from authlib.integrations.starlette_client import OAuth
from pymongo import MongoClient
import jwt

# === Load environment variables ===
APP_STORAGE_SECRET = os.getenv("APP_STORAGE_SECRET")
JWT_TOKEN_KEY = 'ats_jwt_token'
JWT_TOKEN_LIFETIME = timedelta(days=7)
BASE_URL = os.getenv("BASE_URL")
MONGO_URI = os.getenv("MONGO_URI")

# === MongoDB Setup ===
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["ats_db"]
    users_collection = db["users"]
    mongo_client.admin.command('ping')
except Exception as e:
    print(f"[DB] Connection failed: {e}")
    import sys
    sys.exit(1)

# === OAuth Setup ===
oauth = OAuth()
oauth.register(
    "google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, APP_STORAGE_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def get_current_user(request):
    token = request.cookies.get(JWT_TOKEN_KEY)
    if not token:
        return None
    data = decode_jwt_token(token)
    if not data:
        return None
    user = users_collection.find_one({"email": data["email"]})
    return user