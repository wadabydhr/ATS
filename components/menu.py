from nicegui import ui

def render_menu():
    with ui.row().classes('gap-4 ml-8'):  # Horizontal menu with spacing and margin
        ui.link('GERAR RELATÓRIOS', '/dashboard')
        ui.link('CONFIGURAÇÕES', '/settings')
        ui.link('LOGOUT', '/logout')
