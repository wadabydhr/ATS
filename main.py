import os
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import ui, app
from authlib.integrations.starlette_client import OAuth
import jwt
from pymongo import MongoClient
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

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

# Add SessionMiddleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=APP_STORAGE_SECRET)

# OAuth configuration
oauth = OAuth()
oauth.register(
    "google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/oauth/google/login")
async def login(request: Request):
    print("Redirecting to Google OAuth...")
    return await oauth.google.authorize_redirect(request, f"{BASE_URL}/oauth/google/redirect")

@app.get("/oauth/google/redirect")
async def auth_redirect(request: Request):
    try:
        print("Received redirect from Google, processing token...")
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        print("Userinfo received:", userinfo)

        if not userinfo:
            print("No userinfo found in token!")
            return RedirectResponse("/")

        # Check if user exists or register new user
        user = users_collection.find_one({"email": userinfo["email"]})
        if not user:
            print("Registering new user:", userinfo["email"])
            users_collection.insert_one({
                "email": userinfo["email"],
                "name": userinfo["name"],
                "picture": userinfo.get("picture"),
                "created": datetime.utcnow()
            })
        else:
            print("User exists:", userinfo["email"])

        # Create JWT
        jwt_token = jwt.encode({
            "email": userinfo["email"],
            "exp": datetime.utcnow() + JWT_TOKEN_LIFETIME
        }, APP_STORAGE_SECRET, algorithm="HS256")
        print("JWT token created")

        # Set browser cookie BEFORE redirect
        response = RedirectResponse("/dashboard")
        response.set_cookie(key=JWT_TOKEN_KEY, value=jwt_token, httponly=True, max_age=7*24*3600)
        print("JWT token stored in browser cookie")

        return response

    except Exception as e:
        print(f"OAuth processing error: {e}")
        return RedirectResponse("/")

def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, APP_STORAGE_SECRET, algorithms=["HS256"])
    except Exception as e:
        print(f"JWT decode failed: {e}")
        return None

def get_current_user(request: Request):
    token = request.cookies.get(JWT_TOKEN_KEY)
    if not token:
        print("No JWT token found in cookies")
        return None
    data = decode_jwt_token(token)
    if not data:
        print("Invalid or expired JWT token")
        return None
    user = users_collection.find_one({"email": data["email"]})
    if user:
        print(f"User retrieved for dashboard: {user['email']}")
    else:
        print("No user found for this JWT email")
    return user

@ui.page("/", title="ATS Home")
async def home(request: Request):
    ui.label("Welcome to the ATS Application!")
    ui.link("Go to Dashboard", "/dashboard")
    ui.button('Login with Google', on_click=lambda: ui.run_javascript('window.location.replace("/oauth/google/login")'))

@ui.page("/dashboard", title="ATS Dashboard")
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        ui.label("Unauthorized. Please log in.")
        ui.button("Login with Google", on_click=lambda: ui.run_javascript('window.location.replace("/oauth/google/login")'))
    else:
        ui.label(f"Hello, {user['name']}!")
        if user.get("picture"):
            ui.image(user["picture"])
        ui.link("Logout", "/logout")

@app.get("/logout")
async def logout(request: Request):
    print("Logging out, clearing JWT")
    response = RedirectResponse("/")
    response.delete_cookie(JWT_TOKEN_KEY)
    return response

if __name__ in {"__main__", "__mp_main__"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(host="0.0.0.0", port=port)