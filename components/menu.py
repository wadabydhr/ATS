from nicegui import ui

def render_menu(classes=''):
    with ui.row().classes(f'gap-6 {classes}'):
        ui.link('GERAR RELATÓRIOS', '/dashboard').classes('text-white text-sm hover:underline')
        ui.link('CONFIGURAÇÕES', '/settings').classes('text-white text-sm hover:underline')
        ui.link('LOGOUT', '/logout').classes('text-white text-sm hover:underline')
