from nicegui import ui
from components.header import render_header
from components.footer import render_footer
from components.menu import render_menu
from pymongo import MongoClient
from bson.objectid import ObjectId
import re
import os

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
            ]

            def get_table_data():
                companies = get_all_companies()
                return [
                    {
                        'company_name': c.get('company_name', ''),
                        'company_CNPJ': c.get('company_CNPJ', ''),
                        'company_address_CEP': c.get('company_address_CEP', ''),
                        'company_address_number': c.get('company_address_number', ''),
                        'company_address_additional': c.get('company_address_additional', ''),
                        'company_address_city': c.get('company_address_city', ''),
                        'company_address_state': c.get('company_address_state', ''),
                        '_id': str(c.get('_id', '')),
                    } for c in companies
                ]

            selected_row = {'data': None}

            def refresh_table():
                company_table.rows = get_table_data()
                company_table.update()
                selected_row['data'] = None
                action_row.visible = False

            def open_edit_dialog(row):
                company_id = row['_id']
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
                            edit_city = ui.input('Cidade', value=company.get('company_address_city', '')).classes('w-full
