from nicegui import ui

def render_header(user):
    with ui.row().classes('w-full bg-primary text-white p-4 items-center'):
        ui.label('ATS SaaS System').classes('text-lg font-bold')
        if user and user.get("name"):
            ui.label(f'Logged in as {user["name"]}').classes('ml-auto')