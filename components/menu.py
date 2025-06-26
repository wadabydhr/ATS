from nicegui import ui

def render_menu(classes=''):
    with ui.row().classes(f'gap-6 {classes}'):
        ui.link('Dashboard', '/dashboard').classes('text-white text-sm hover:underline')
        ui.link('Settings', '/settings').classes('text-white text-sm hover:underline')
        ui.link('Logout', '/logout').classes('text-white text-sm hover:underline')
