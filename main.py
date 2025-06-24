import os
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import ui, app
from authlib.integrations.starlette_client import OAuth
import jwt
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
APP_STORAGE_SECRET = os.getenv("APP_STORAGE_SECRET")
JWT_TOKEN_KEY = 'ats_jwt_token'
JWT_TOKEN_LIFETIME = timedelta(days=7)
BASE_URL = os.getenv("BASE_URL")

# MongoDB connection
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client["ats_db"]
users_collection = db["users"]

# OAuth configuration
oauth = OAuth()
oauth.register(
    "google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# OAuth login route
@app.get("/oauth/google/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, f"{BASE_URL}/oauth/google/redirect")

# OAuth redirect callback
@app.get("/oauth/google/redirect")
async def auth_redirect(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if not userinfo:
            return RedirectResponse("/")

        # Check if user exists
        user = users_collection.find_one({"email": userinfo["email"]})
        if not user:
            # Register user
            users_collection.insert_one({
                "email": userinfo["email"],
                "name": userinfo["name"],
                "picture": userinfo.get("picture"),
                "created": datetime.utcnow()
            })

        # Create JWT
        jwt_token = jwt.encode({
            "email": userinfo["email"],
            "exp": datetime.utcnow() + JWT_TOKEN_LIFETIME
        }, APP_STORAGE_SECRET, algorithm="HS256")

        app.storage.browser[JWT_TOKEN_KEY] = jwt_token
        return RedirectResponse("/dashboard")

    except Exception as e:
        print(f"OAuth Error: {e}")
        return RedirectResponse("/")

# JWT decode utility
def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, APP_STORAGE_SECRET, algorithms=["HS256"])
    except:
        return None

# Retrieve current user based on JWT
def get_current_user():
    token = app.storage.browser.get(JWT_TOKEN_KEY)
    if not token:
        return None
    data = decode_jwt_token(token)
    if not data:
        del app.storage.browser[JWT_TOKEN_KEY]
        return None
    return users_collection.find_one({"email": data["email"]})

# Home page
@ui.page("/", title="ATS Home")
async def home():
    ui.label("Welcome to the ATS Application!")
    ui.link("Go to Dashboard", "/dashboard")
    ui.link("Login with Google", "/oauth/google/login")

# Protected dashboard
@ui.page("/dashboard", title="ATS Dashboard")
async def dashboard():
    user = get_current_user()
    if not user:
        ui.label("Unauthorized. Please log in.")
        ui.link("Login with Google", "/oauth/google/login")
    else:
        ui.label(f"Hello, {user['name']}!")
        if user.get("picture"):
            ui.image(user["picture"])
        ui.link("Logout", "/logout")

# Logout route
@app.get("/logout")
async def logout(request: Request):
    del app.storage.browser[JWT_TOKEN_KEY]
    return RedirectResponse("/")

# Start the server
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    ui.run(host="0.0.0.0", port=port)
