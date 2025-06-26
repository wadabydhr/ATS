from nicegui import ui
from components.header import render_header
from components.footer import render_footer
from components.menu import render_menu

def dashboard_page(user):
    render_header(user)
    with ui.row().classes('w-full'):
        with ui.column().classes('w-1/4 min-h-[60vh]'):
            render_menu()
        with ui.column().classes('w-full items-start justify-start mt-0'):
            ui.label(f'Usuário - {user["name"]}!').classes('text-2xl mb-4')
            if user.get("picture"):
                ui.image(user["picture"]).classes('w-32 h-32 rounded-full mb-4')
            ui.label('Página para gerar relatórios.').classes('mb-4')
    render_footer()
