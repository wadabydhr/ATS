import os
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from nicegui import ui, app
import jwt
from utils.auth import (
    oauth, users_collection, JWT_TOKEN_KEY, JWT_TOKEN_LIFETIME,
    APP_STORAGE_SECRET, get_current_user, BASE_URL
)
from components.header import render_header
from components.footer import render_footer
from components.menu import render_menu
from pages.dashboard import dashboard_page
from pages.settings import settings_page

# === Add Session Middleware ===
app.add_middleware(SessionMiddleware, secret_key=APP_STORAGE_SECRET)

# === Auth Routes (Google OAuth) ===

@app.get("/oauth/google/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, f"{BASE_URL}/oauth/google/redirect")

@app.get("/oauth/google/redirect")
async def auth_redirect(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        return RedirectResponse("/")
    user = users_collection.find_one({"email": userinfo["email"]})
    if not user:
        users_collection.insert_one({
            "email": userinfo["email"],
            "name": userinfo["name"],
            "picture": userinfo.get("picture"),
            "created": datetime.utcnow()
        })
    jwt_token = jwt.encode({
        "email": userinfo["email"],
        "exp": datetime.utcnow() + JWT_TOKEN_LIFETIME
    }, APP_STORAGE_SECRET, algorithm="HS256")
    response = RedirectResponse("/dashboard")
    response.set_cookie(key=JWT_TOKEN_KEY, value=jwt_token, httponly=True, max_age=7*24*3600)
    return response

@ui.page('/logout')
async def logout(request: Request):
    response = RedirectResponse("/")
    response.delete_cookie(JWT_TOKEN_KEY)
    return response

# === Page Definitions ===

@ui.page('/')
async def home(request: Request):
    user = get_current_user(request)
    if user:
        return ui.navigate.to('/dashboard')
    ui.label('Welcome to ATS!').classes('text-2xl mt-8')
    ui.button('Login with Google', on_click=lambda: ui.run_javascript('window.location.replace("/oauth/google/login")'))

@ui.page('/dashboard')
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return ui.navigate.to('/')
    dashboard_page(user)

@ui.page('/settings')
async def settings(request: Request):
    user = get_current_user(request)
    if not user:
        return ui.navigate.to('/')
    settings_page(user)

if __name__ in {'__main__', '__mp_main__'}:
    ui.run()