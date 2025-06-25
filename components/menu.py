from nicegui import ui

def render_menu():
    with ui.column().classes('p-2'):
        ui.link('Dashboard', '/dashboard')
        ui.link('Settings', '/settings')
        ui.link('Logout', '/logout')