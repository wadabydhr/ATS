from nicegui import ui

def render_menu():
    with ui.row().classes('gap-6 ml-auto'):  # Horizontal menu with spacing and margin
        ui.link('GERAR RELATÓRIOS', '/dashboard').classes('text-white text-sm hover:underline')
        ui.link('CONFIGURAÇÕES', '/settings').classes('text-white text-sm hover:underline')
        ui.link('LOGOUT', '/logout').classes('text-white text-sm hover:underline')
