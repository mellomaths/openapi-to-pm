import json
import os
import datetime

from django.core.files.storage import default_storage
from django.conf import settings
from django.http import HttpResponse, Http404

from .exceptions import NotJsonFileError, SwaggerFormatError, SwaggerVersionError
from .pm import Postman

def handle_file_upload(file, args):
    filename = file.name
    arrayFilename = filename.split('.')
    extension = arrayFilename[-1]

    if extension != 'json':
        raise NotJsonFileError('Formato de arquivo inválido. Por favor, selecione um arquivo .json')

    full_path = _save_uploaded_file(file)
    with open(full_path) as file:
        data = _validate_swagger_json(file, 'file')
        pm = Postman.generate(data, args)
        _save_postman_collection(pm)        
        
    os.remove(full_path)    
    return pm
        

def handle_swagger_from_text(text, args):
    data = _validate_swagger_json(text, 'string')
    pm = Postman.generate(data, args)
    _save_postman_collection(pm)
    return pm


def get_postman_data_from_file(filename):
    dir_path = _get_media_dir_path()
    full_path = os.path.join(dir_path, filename)

    collection_str = None
    with open(full_path, encoding='utf8') as file:
        collection = json.load(file)
        collection_str = json.dumps(collection, indent=4).encode('utf8').decode('latin1')

    metrics_filename = _metrics_filename(filename)
    metrics_file_path = os.path.join(dir_path, metrics_filename)

    metrics = None
    with open(metrics_file_path, encoding='utf8') as file:
        metrics = json.load(file)

    postman_data = {
        'collection_str': collection_str,
        'metrics': metrics
    }

    return postman_data


def download_file(filename):
    dir_path = _get_media_dir_path()
    full_path = os.path.join(dir_path, filename)
    if os.path.exists(full_path):
        with open(full_path, encoding='utf-8') as file:
            response = HttpResponse(file.read(), content_type='application/json')
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(full_path)
            return response
    raise Http404


def _validate_swagger_json(data, data_type):
    try:
        if data_type == 'string':
            json_data = json.loads(data)
        elif data_type == 'file':
            json_data = json.load(data)

        if 'openapi' not in json_data:
          raise SwaggerFormatError('O arquivo JSON informado não respeita o padrão Swagger OpenAPI 3.0.0')
        elif json_data['openapi'] != '3.0.0':
          raise SwaggerVersionError('A versão do Swagger informado não é suportada. Informe um Swagger Open Api 3.0.0')

    except json.decoder.JSONDecodeError:
        raise NotJsonFileError('Arquivo não se encontra no formato JSON ou é inválido')

    return json_data


def _save_uploaded_file(file):
    dir_path = _get_media_dir_path()
    full_path = os.path.join(dir_path, file.name)

    with open(full_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return full_path


def _get_media_dir_path():
    media_root = settings.MEDIA_ROOT
    if not os.path.exists(media_root):
        os.mkdir(media_root)

    dir_path = media_root
    
    return dir_path


def _metrics_filename(collection_filename):
    collection_name = collection_filename.replace('.postman_collection.json', '')
    return f'{collection_name}.metrics.json'


def _save_postman_collection(pm):
    dir_path = _get_media_dir_path()
    filename = pm['filename']
    collection_file_path = os.path.join(dir_path, filename)
    with open(collection_file_path, 'w', encoding='utf-8') as file:
        json.dump(pm['collection'], file, ensure_ascii=False, indent=4)
    
    metrics_filename = _metrics_filename(filename)
    metrics_file_path = os.path.join(dir_path, metrics_filename)
    with open(metrics_file_path, 'w', encoding='utf-8') as file:
        json.dump(pm['metrics'], file, ensure_ascii=False, indent=4)

