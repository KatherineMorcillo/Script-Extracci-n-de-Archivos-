import os
import re
import time
import urllib
import requests
import html
from urllib.parse import unquote
from unidecode import unidecode


def auth(user, password):
    params = {
        "grant_type": "password",
        "client_id": "",
        "client_secret": "",
        "username": user,
        "password": password,
    }

    try:
        response = requests.post('', params=params)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un código de estado HTTP de error
    except requests.exceptions.RequestException as e:
        print(f'Hubo un error: {e}')
        return None

    return response.json()


# Todos los documentos de los Casos Cerrados
# def fetch_all_cases_documents(access_token):
#     url = "https://.../services/data/v51.0/query/?q=SELECT LinkedEntityId, LinkedEntity.Name, ContentDocument.LatestPublishedVersionId, ContentDocumentId, ContentDocument.Title, ContentDocument.FileExtension, ContentDocument.CreatedDate FROM ContentDocumentLink WHERE LinkedEntityId IN (SELECT Id FROM Case WHERE IsClosed = TRUE)"
#     return fetch_data(url, access_token)

#Todos los documentos de los Casos Abiertos
def fetch_all_cases_documents(access_token):
    url = "https://..../services/data/v51.0/query/?q=SELECT LinkedEntityId, LinkedEntity.Name, ContentDocument.LatestPublishedVersionId, ContentDocumentId, ContentDocument.Title, ContentDocument.FileExtension, ContentDocument.CreatedDate FROM ContentDocumentLink WHERE LinkedEntityId IN (SELECT Id FROM Case WHERE IsClosed = FALSE)"
    return fetch_data(url, access_token)


# Cliente asociado al caso
def fetch_one_client_case(access_token, caseId):
    url = f"https://..../services/data/v51.0/query/?q=SELECT CaseNumber, AccountId, Account.Name FROM Case WHERE Id = '{caseId}'"
    return fetch_data(url, access_token)

#  Todos los documentos de las oportunidades Cerradas
# def fetch_all_opportunities_documents(access_token):
#     url = "https://..../services/data/v51.0/query/?q=SELECT LinkedEntityId, LinkedEntity.Name, ContentDocument.LatestPublishedVersionId, ContentDocumentId, ContentDocument.Title, ContentDocument.FileExtension, ContentDocument.CreatedDate FROM ContentDocumentLink WHERE LinkedEntityId IN (SELECT Id FROM Opportunity WHERE RecordType.Name = 'Cliente Ancla' AND StageName IN ('Oppty perdida', 'En ejecución y facturado. Oppty ganada'))"
#     return fetch_data(url, access_token)

#Todos los documentos de las oportunidades Abiertas
def fetch_all_opportunities_documents(access_token):
    url = "https://...../services/data/v51.0/query/?q=SELECT LinkedEntityId, LinkedEntity.Name, ContentDocument.LatestPublishedVersionId, ContentDocumentId, ContentDocument.Title, ContentDocument.FileExtension, ContentDocument.CreatedDate FROM ContentDocumentLink WHERE LinkedEntityId IN (SELECT Id FROM Opportunity WHERE RecordType.Name = 'Cliente Ancla' AND StageName NOT IN ('Oppty perdida', 'En ejecución y facturado. Oppty ganada'))"
    return fetch_data(url, access_token)


# Cliente asociado a la oportunidad
def fetch_one_client_opportunity(access_token, opportunityId):
    url = f"https://.../services/data/v51.0/query/?q=SELECT Name, AccountId, Account.Name FROM Opportunity WHERE Id = '{opportunityId}'"
    return fetch_data(url, access_token)

# Validacion del cliente si existe
def get_name_account(data):
    if data is not None and 'records' in data and len(
            data['records']) > 0:
        account_data = data['records'][0]['Account']
        if account_data is not None:
            account_name = account_data.get('Name', 'Client no encontrado')
        else:
            account_name = 'Cliente no encontrado'
    else:
        account_name = 'Cliente no encontrado'
    return account_name


def sanitize_filename(filename):
    # Reemplazar caracteres no alfanuméricos y espacios con guiones bajos
    cleaned_filename = re.sub(r'[^\w\s.-]', '_', filename)
    cleaned_filename = re.sub(r'\s+', '_', cleaned_filename)
    cleaned_filename = cleaned_filename.strip('_-')
    max_length = 255
    cleaned_filename = cleaned_filename[:max_length]
    return cleaned_filename


def fetch_file_content(access_token, LatestPublishedVersionId, file_name, file_extension, linked_entity_id, sub_folder):
    url = f'https://.../data/v51.0/sobjects/ContentVersion/{LatestPublishedVersionId}/VersionData'

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Crear el directorio si no existe
        directory = urllib.parse.unquote(unidecode(os.path.join(f'Documentos - {sub_folder}', sanitize_filename(linked_entity_id))))
        os.makedirs(directory, exist_ok=True)

        # Decodificar y codificar correctamente los nombres de archivo y extensiones
        file_name = urllib.parse.unquote(unidecode(sanitize_filename(file_name)))
        file_extension = file_extension

        # Validación .snote --> .html
        if file_extension == 'snote':
            file_extension = 'html'

        # Combinar las partes para construir la ruta de archivo
        file_name_with_extension = f"{file_name}.{file_extension}"
        file_path = os.path.join(directory, file_name_with_extension)

        try:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Archivo {file_name_with_extension} guardado en el directorio {file_path}")
        except FileNotFoundError:
            # Registra el error en un archivo de registro de errores
            error_message = f"{sub_folder} - no creado {file_path}\n"
            with open("errores.log", "a") as error_log:
                error_log.write(error_message)
            print(f"El archivo {file_name_with_extension} no se encontró en la ubicación especificada. {file_path}")

    else:
        print(f"Fallo al obtener el contenido del archivo, código de estado: {response.status_code}")

def fetch_data(url, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza una excepción si la respuesta tiene un código de estado HTTP de error
    except requests.exceptions.RequestException as e:
        print(f'Hubo un error: {e}')
        return None


    if 'application/json' in response.headers['Content-Type']:
        return response.json()
    else:
        return response.content


if __name__ == '__main__':

    auth_data = auth('santiago.suarez@parservicios.com', 'Ssr17287712fkHAn4KczFZFHJ7f3ijjwbXmV')

    access_token = auth_data['access_token'] if auth_data is not None else None

    if access_token:
        # Casos
        documents = fetch_all_cases_documents(access_token)
        if documents is not None and 'records' in documents:
            for document in documents['records']:
                if document.get('ContentDocument'):
                    clientInformation = fetch_one_client_case(access_token,document['LinkedEntityId'])
                    # Obtener nombre del cliente
                    client_name = get_name_account(clientInformation)
                    # (access_token, LatestPublishedVersionId, file_extension, linked_entity_id)
                    fetch_file_content(access_token, document['ContentDocument'].get('LatestPublishedVersionId'), document['ContentDocument'].get('Title'), document['ContentDocument'].get('FileExtension'),f"{document['LinkedEntity'].get('Name')} - {client_name}",'casos')
                    time.sleep(3)
                else:
                    print("No ContentDocument data available for this record.")

        #Oportunidades
        documentsOp = fetch_all_opportunities_documents(access_token)
        if documentsOp is not None and 'records' in documentsOp:
            for documentOp in documentsOp['records']:
                if documentOp.get('ContentDocument'):
                    # (access_token, LatestPublishedVersionId, file_extension, linked_entity_id)
                    clientInformation = fetch_one_client_opportunity(access_token,documentOp['LinkedEntityId'])
                    # Obtener nombre del cliente
                    client_name = get_name_account(clientInformation)

                    fetch_file_content(access_token, documentOp['ContentDocument'].get('LatestPublishedVersionId'),
                                       documentOp['ContentDocument'].get('Title'),
                                       documentOp['ContentDocument'].get('FileExtension'),
                                       f"{documentOp['LinkedEntityId']} - {documentOp['LinkedEntity'].get('Name')}", f"oportunidades/{sanitize_filename(client_name)}")
                    time.sleep(3)
                else:
                    print("No ContentDocument data available for this record.")
