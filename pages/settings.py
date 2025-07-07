from nicegui import ui
from components.header import render_header
from components.footer import render_footer
from components.menu import render_menu
from pymongo import MongoClient
from bson.objectid import ObjectId
import re
import os

# MongoDB connection for Render.com or local
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://hirokiwada:BYNDHR19hiw@byndhr-cluster.1zn6ljk.mongodb.net/?retryWrites=true&w=majority&appName=BYNDHR-CLUSTER"
)
MONGO_DB = os.getenv("MONGODB_DB", "report_generator")
MONGO_COLLECTION = os.getenv("MONGODB_COMPANIES_COLLECTION", "companies")

def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]

def get_all_companies():
    collection = get_mongo_collection()
    return list(collection.find({}, {
        "_id": 1,
        "company_name": 1,
        "company_CNPJ": 1,
        "company_address_CEP": 1,
        "company_address_number": 1,
        "company_address_additional": 1,
        "company_address_city": 1,
        "company_address_state": 1,
    }))

def add_company(data):
    collection = get_mongo_collection()
    if collection.find_one({"company_CNPJ": data["company_CNPJ"]}):
        return False, "Empresa com este CNPJ já existe."
    result = collection.insert_one(data)
    return True, f"Empresa adicionada com id {result.inserted_id}"

def update_company(company_id, data):
    collection = get_mongo_collection()
    result = collection.update_one(
        {"_id": ObjectId(company_id)},
        {"$set": data}
    )
    return result.modified_count > 0

def delete_company(company_id):
    collection = get_mongo_collection()
    result = collection.delete_one({"_id": ObjectId(company_id)})
    return result.deleted_count > 0

def validate_cnpj(cnpj):
    return bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}/\d{4}-\d{2}", cnpj))

def validate_cep(cep):
    return bool(re.fullmatch(r"\d{5}-\d{3}", cep))

def validate_state(state):
    return bool(re.fullmatch(r"[A-Za-z]{2}", state))

def required_label(text):
    return ui.html(f'<span style="color: #e53935;">*</span> {text}').classes('font-bold')

def settings_page(user):
    render_header(user)

    with ui.row().classes('w-full items-start mt-0 pt-0'):
        with ui.column().classes('w-1/4 min-h-[60vh] items-start pt-0 mt-0'):
            render_menu()
        with ui.column().classes('w-3/4 p-4 items-start pt-0 mt-0'):
            ui.label('Configurações - CRUD de Empresas (COMPANY)').classes('text-2xl font-bold mb-2 mt-0 pt-0')
            ui.label('Empresas cadastradas').classes('text-lg font-bold mb-2 mt-2')

            columns = [
                {'name': 'company_name', 'label': 'Empresa', 'field': 'company_name'},
                {'name': 'company_CNPJ', 'label': 'CNPJ', 'field': 'company_CNPJ'},
                {'name': 'company_address_CEP', 'label': 'CEP', 'field': 'company_address_CEP'},
                {'name': 'company_address_number', 'label': 'Número', 'field': 'company_address_number'},
                {'name': 'company_address_additional', 'label': 'Complemento', 'field': 'company_address_additional'},
                {'name': 'company_address_city', 'label': 'Cidade', 'field': 'company_address_city'},
                {'name': 'company_address_state', 'label': 'UF', 'field': 'company_address_state'},
                {'name': 'edit', 'label': 'Editar', 'field': 'edit'},
                {'name': 'delete', 'label': 'Excluir', 'field': 'delete'},
            ]

            table_rows = []

            def refresh_table():
                company_table.rows.clear()
                table_rows.clear()
                companies = get_all_companies()
                for company in companies:
                    row_dict = {
                        'company_name': company.get('company_name', ''),
                        'company_CNPJ': company.get('company_CNPJ', ''),
                        'company_address_CEP': company.get('company_address_CEP', ''),
                        'company_address_number': company.get('company_address_number', ''),
                        'company_address_additional': company.get('company_address_additional', ''),
                        'company_address_city': company.get('company_address_city', ''),
                        'company_address_state': company.get('company_address_state', ''),
                        'edit': None,   # will be set after table is rendered
                        'delete': None, # will be set after table is rendered
                        '_id': str(company.get('_id', '')),
                    }
                    table_rows.append(row_dict)
                    company_table.add_row(row_dict)

            def open_edit_dialog(company_id):
                company = next((c for c in get_all_companies() if str(c['_id']) == str(company_id)), None)
                if not company:
                    ui.notify('Empresa não encontrada', color='negative')
                    return

                with ui.dialog() as dialog, ui.card():
                    ui.label('Editar empresa').classes('text-lg font-bold mb-2')
                    with ui.row().classes('w-full'):
                        with ui.column().classes('w-1/2'):
                            edit_name = ui.input('Nome da empresa', value=company.get('company_name', '')).classes('w-full')
                            edit_cnpj = ui.input('CNPJ (000.000.000/0000-00)', value=company.get('company_CNPJ', '')).classes('w-full').props('mask=###.###.###/####-##')
                            edit_cep = ui.input('CEP (00000-000)', value=company.get('company_address_CEP', '')).classes('w-full').props('mask=#####-###')
                            edit_number = ui.input('Número', value=company.get('company_address_number', '')).classes('w-full')
                        with ui.column().classes('w-1/2'):
                            edit_additional = ui.input('Complemento', value=company.get('company_address_additional', '')).classes('w-full')
                            edit_city = ui.input('Cidade', value=company.get('company_address_city', '')).classes('w-full')
                            edit_state = ui.input('UF', value=company.get('company_address_state', '')).classes('w-20').props('maxlength=2')
                    edit_msg = ui.label().classes('mt-2 text-red-500')

                    def save_edit():
                        if not (
                            edit_name.value and edit_cnpj.value and edit_cep.value and edit_city.value and edit_state.value
                        ):
                            edit_msg.text = "Preencha todos os campos obrigatórios."
                            return
                        if not validate_cnpj(edit_cnpj.value):
                            edit_msg.text = "CNPJ inválido. Use o formato 000.000.000/0000-00."
                            return
                        if not validate_cep(edit_cep.value):
                            edit_msg.text = "CEP inválido. Use o formato 00000-000."
                            return
                        if not validate_state(edit_state.value):
                            edit_msg.text = "UF inválido. Use dois caracteres."
                            return
                        data = {
                            "company_name": edit_name.value,
                            "company_CNPJ": edit_cnpj.value,
                            "company_address_CEP": edit_cep.value,
                            "company_address_number": edit_number.value,
                            "company_address_additional": edit_additional.value,
                            "company_address_city": edit_city.value,
                            "company_address_state": edit_state.value.upper(),
                        }
                        updated = update_company(company_id, data)
                        if updated:
                            ui.notify('Empresa atualizada', color='positive')
                            dialog.close()
                            refresh_table()
                            patch_table_actions()
                        else:
                            edit_msg.text = "Nenhuma alteração feita ou erro ao atualizar empresa."

                    ui.button('Salvar', on_click=save_edit).props('color=primary')
                    ui.button('Cancelar', on_click=dialog.close).props('color=secondary')
                dialog.open()

            def delete_row(company_id):
                if delete_company(company_id):
                    ui.notify('Empresa excluída', color='positive')
                    refresh_table()
                    patch_table_actions()
                else:
                    ui.notify('Erro ao excluir empresa', color='negative')

            with ui.element('div').classes('w-full'):
                company_table = ui.table(
                    columns=columns,
                    rows=[],
                    row_key='_id',
                    pagination=10
                ).classes('w-full max-w-full')

            def patch_table_actions():
                for i, row in enumerate(table_rows):
                    row_id = row['_id']
                    # Remove `size` argument, only allowed: (label, on_click, icon, color, etc)
                    company_table.rows[i]['edit'] = ui.button('✎', on_click=lambda rid=row_id: open_edit_dialog(rid), icon='edit', color='primary').classes('q-mr-xs')
                    company_table.rows[i]['delete'] = ui.button('🗑', on_click=lambda rid=row_id: delete_row(rid), icon='delete', color='negative')
                company_table.update()

            refresh_table()
            patch_table_actions()

            # --- Formulario de Adição por último ---
            ui.separator()
            ui.label('Adicionar nova empresa').classes('text-lg font-bold mb-2 mt-8')
            with ui.row().classes('w-full'):
                with ui.column().classes('w-1/2'):
                    required_label('Nome da empresa')
                    name = ui.input('', placeholder='Nome da empresa').classes('w-full')
                    required_label('CNPJ (000.000.000/0000-00)')
                    cnpj = ui.input('', placeholder='000.000.000/0000-00').classes('w-full').props('mask=###.###.###/####-##')
                    required_label('CEP (00000-000)')
                    cep = ui.input('', placeholder='00000-000').classes('w-full').props('mask=#####-###')
                    ui.label('Número')
                    number = ui.input('', placeholder='Número').classes('w-full')
                with ui.column().classes('w-1/2'):
                    ui.label('Complemento')
                    additional = ui.input('', placeholder='Complemento').classes('w-full')
                    required_label('Cidade')
                    city = ui.input('', placeholder='Cidade').classes('w-full')
                    required_label('UF')
                    state = ui.input('', placeholder='UF').classes('w-20').props('maxlength=2')

            msg = ui.label().classes('mt-2 text-red-500')

            def submit():
                if not (
                    name.value and cnpj.value and cep.value and city.value and state.value
                ):
                    msg.text = "Preencha todos os campos obrigatórios."
                    return
                if not validate_cnpj(cnpj.value):
                    msg.text = "CNPJ inválido. Use o formato 000.000.000/0000-00."
                    return
                if not validate_cep(cep.value):
                    msg.text = "CEP inválido. Use o formato 00000-000."
                    return
                if not validate_state(state.value):
                    msg.text = "UF inválido. Use dois caracteres."
                    return
                data = {
                    "company_name": name.value,
                    "company_CNPJ": cnpj.value,
                    "company_address_CEP": cep.value,
                    "company_address_number": number.value,
                    "company_address_additional": additional.value,
                    "company_address_city": city.value,
                    "company_address_state": state.value.upper(),
                }
                ok, feedback = add_company(data)
                if ok:
                    msg.text = ''
                    ui.notify(feedback, color='positive')
                    refresh_table()
                    patch_table_actions()
                    name.value = cnpj.value = cep.value = number.value = additional.value = city.value = state.value = ''
                else:
                    msg.text = feedback

            ui.button('Adicionar', on_click=submit).classes('mt-2')

    render_footer()