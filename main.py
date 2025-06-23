import os
from nicegui import ui
from dotenv import load_dotenv
from descope import DescopeClient
from fastapi import Request

load_dotenv()
DESCOPE_PROJECT_ID = os.getenv('DESCOPE_PROJECT_ID')
descope_client = DescopeClient(project_id=DESCOPE_PROJECT_ID)

def get_user_from_cookie(request: Request):
    jwt = request.cookies.get("DS")
    if not jwt:
        return None
    try:
        user = descope_client.validate_session_jwt(jwt)
        return user
    except Exception:
        return None

@ui.page('/')
async def main(request: Request):  # <-- inject Request here
    user = get_user_from_cookie(request)
    if user:
        ui.label(f"Welcome, {user.get('name') or user.get('loginId', 'User')}!").classes('text-2xl')
        ui.button('Logout', on_click=lambda: ui.open('/logout'))
        ui.label('Applicant Tracking System dashboard goes here.')
    else:
        ui.label('Sign in to access the ATS dashboard.').classes('text-xl')
        ui.html(f'''
        <iframe src="https://auth.descope.com/{DESCOPE_PROJECT_ID}?flow=sign-up-or-in"
                style="border:none;width:400px;height:600px"></iframe>
        ''')

@ui.page('/logout')
def logout():
    ui.notify('Logged out!')
    ui.run_javascript('document.cookie = "DS=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;"')
    ui.open('/')

ui.run(title='ATS with Descope Auth')