import ssl, certifi
print("OpenSSL version:", ssl.OPENSSL_VERSION)
print("Certifi CA bundle:", certifi.where())

import os
from datetime import datetime, timedelta
from fastapi import Request, FastAPI
from fastapi.responses import RedirectResponse
from nicegui import ui, app
from authlib.integrations.starlette_client import OAuth
import jwt
from pymongo import MongoClient
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

# Load environment variables
load_dotenv()

# Diagnostic: Print env on startup
print("=== ATS Startup ===")
for var in ['APP_STORAGE_SECRET', 'MONGO_URI', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'BASE_URL']:
    print(f"{var} = {'SET' if os.getenv(var) else 'NOT SET'}")
print("===================")

# Configuration
APP_STORAGE_SECRET = os.getenv("APP_STORAGE_SECRET")
JWT_TOKEN_KEY = 'ats_jwt_token'
JWT_TOKEN_LIFETIME = timedelta(days=7)
BASE_URL = os.getenv("BASE_URL")

# MongoDB connection
try:
    print("[DB] Connecting to MongoDB...")
    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    # Force a connection to verify credentials and network
    mongo_client.admin.command('ping')
    db = mongo_client["ats_db"]
    users_collection = db["users"]
    print("[DB] Connection successful.")
except Exception as e:
    print(f"[DB] Connection failed: {e}")
    import sys
    sys.exit(1)


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

# Add a global exception handler for diagnostics
fastapi_app = app._get_fastapi_app() if hasattr(app, "_get_fastapi_app") else app
@fastapi_app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"[EXCEPTION] Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    return RedirectResponse("/")

@app.get("/oauth/google/login")
async def login(request: Request):
    print("[OAUTH] Redirecting to Google OAuth...")
    try:
        resp = await oauth.google.authorize_redirect(request, f"{BASE_URL}/oauth/google/redirect")
        print("[OAUTH] authorize_redirect completed.")
        return resp
    except Exception as e:
        print(f"[OAUTH] authorize_redirect error: {e}")
        raise

@app.get("/oauth/google/redirect")
async def auth_redirect(request: Request):
    print("[OAUTH] In redirect handler.")
    try:
        token = await oauth.google.authorize_access_token(request)
        print(f"[OAUTH] Token received: {token}")
        userinfo = token.get("userinfo")
        print(f"[OAUTH] Userinfo: {userinfo}")

        if not userinfo:
            print("[OAUTH] No userinfo found in token!")
            return RedirectResponse("/")

        # Check if user exists or register new user
        user = users_collection.find_one({"email": userinfo["email"]})
        print(f"[OAUTH] User from DB: {user}")
        if not user:
            print(f"[OAUTH] Registering new user: {userinfo['email']}")
            users_collection.insert_one({
                "email": userinfo["email"],
                "name": userinfo["name"],
                "picture": userinfo.get("picture"),
                "created": datetime.utcnow()
            })
        else:
            print(f"[OAUTH] User already exists: {userinfo['email']}")

        # Create JWT
        jwt_token = jwt.encode({
            "email": userinfo["email"],
            "exp": datetime.utcnow() + JWT_TOKEN_LIFETIME
        }, APP_STORAGE_SECRET, algorithm="HS256")
        print(f"[OAUTH] JWT token created: {jwt_token}")

        # Set browser cookie BEFORE redirect
        response = RedirectResponse("/dashboard")
        response.set_cookie(key=JWT_TOKEN_KEY, value=jwt_token, httponly=True, max_age=7*24*3600)
        print("[OAUTH] JWT token set in browser cookie.")

        return response

    except Exception as e:
        print(f"[OAUTH] Exception in redirect flow: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/")

def decode_jwt_token(token: str):
    print(f"[JWT] Decoding token: {token}")
    try:
        result = jwt.decode(token, APP_STORAGE_SECRET, algorithms=["HS256"])
        print(f"[JWT] Decoded data: {result}")
        return result
    except Exception as e:
        print(f"[JWT] decode failed: {e}")
        return None

def get_current_user(request: Request):
    print("[AUTH] Getting current user from cookie")
    token = request.cookies.get(JWT_TOKEN_KEY)
    if not token:
        print("[AUTH] No JWT token found in cookies")
        return None
    data = decode_jwt_token(token)
    if not data:
        print("[AUTH] Invalid or expired JWT token")
        return None
    user = users_collection.find_one({"email": data["email"]})
    if user:
        print(f"[AUTH] User retrieved for dashboard: {user['email']}")
    else:
        print("[AUTH] No user found for this JWT email")
    return user

@ui.page("/", title="ATS Home")
async def home(request: Request):
    print("[PAGE] Home loaded")
    ui.label("Welcome to the ATS Application!")
    ui.link("Go to Dashboard", "/dashboard")
    ui.button('Login with Google', on_click=lambda: ui.run_javascript('window.location.replace("/oauth/google/login")'))

@ui.page("/dashboard", title="ATS Dashboard")
async def dashboard(request: Request):
    print("[PAGE] Dashboard loaded")
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
    print("[LOGOUT] Logging out, clearing JWT")
    response = RedirectResponse("/")
    response.delete_cookie(JWT_TOKEN_KEY)
    return response

if __name__ in {"__main__", "__mp_main__"}:
    print("[MAIN] Starting app")
    port = int(os.environ.get("PORT", 8080))
    ui.run(host="0.0.0.0", port=port)
