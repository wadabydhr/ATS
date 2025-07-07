from nicegui import ui
from components.header import render_header
from components.footer import render_footer
from components.menu import render_menu

def settings_page(user):
    render_header(user)
    with ui.row().classes('w-full'):
        with ui.column().classes('w-1/4 min-h-[60vh]'):
            render_menu()
        with ui.column().classes('w-3/4 p-4'):
            ui.label('Settings').classes('text-2xl mb-4')
            ui.label(f'Name: {user['name']}')
            ui.label(f'Email: {user['email']}')
    render_footer()