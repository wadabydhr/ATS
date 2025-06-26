from nicegui import ui
from components.menu import render_menu

def render_header(user):
    with ui.row().classes('w-full bg-primary text-white p-4 items-center'):
        ui.label('BEYOND HR ATS').classes('text-lg font-bold')
        render_menu()  # Insert the menu inside the header
        if user and user.get("name"):
            ui.label(f'Logado como {user["name"]}').classes('ml-auto')
