import json
import copy
import os
import sys

from .templates import create_request, create_request_name, generate_test_script, create_collection_name
from openapi.openapi import OpenApi
from exceptions import InvalidEnvironmentValueError
from tracer import Tracer


class Postman:

    @staticmethod
    def generate_bad_requests(swagger, component_name, status_code, method, host_url, endpoint, body, test_script,
                              auth_type):
        """
        Generate all bad requests (400) for all required fields, based on it's JSON Schema.
        For each field, the function will generated a request:
          - Without the required field
          - With field empty
          - With field in wrong type

        Params:
          - swagger: Swagger JSON
          - component_name: Name of the component in the format: "#/components/schemas/Object"
          - status_code: HTTP status code of the request
          - method: Request HTTP method (GET, POST, PUT, PATCH, DELETE)
          - host_url: The base url for all requests
          - endpoint: Endpoint of the operation request
          - body: JSON body the request
          - test_script: String with JavaScript to execute test on Postman
          - auth_type: Authorization type to use on headers

        Returns: List of all bad requests generated for all required fields
        """

        schema = component_name.split('/')[-1]
        specs = swagger['components']['schemas'][schema]
        if 'required' not in specs:
            return []

        requests = []
        for required_field in specs['required']:
            prop_type = specs['properties'][required_field]['type']

            # Create test without the field
            bad_request_body = copy.deepcopy(body)
            description = f'sem {required_field}'
            del bad_request_body[required_field]
            req = create_request(status_code, description, method, host_url, endpoint, bad_request_body, test_script,
                                 auth_type)
            requests.append(req)

            # Create test with wrong type in field
            bad_request_body = copy.deepcopy(body)
            description = f'{required_field} tipagem inválida'

            if prop_type in ('boolean', 'number', 'array', 'object'):
                bad_request_body[required_field] = 'tipo inválido'
            else:
                bad_request_body[required_field] = 10

            req = create_request(status_code, description, method, host_url, endpoint, bad_request_body, test_script,
                                 auth_type)
            requests.append(req)

            if prop_type in ('string', 'array', 'object'):
                # Create test with empty field
                bad_request_body = copy.deepcopy(body)
                description = f'{required_field} vazio'
                if prop_type == 'string':
                    bad_request_body[required_field] = ''
                elif prop_type == 'array':
                    bad_request_body[required_field] = []
                elif prop_type == 'object':
                    bad_request_body[required_field] = {}

                req = create_request(status_code, description, method, host_url, endpoint, bad_request_body, test_script,
                                     auth_type)
                requests.append(req)

            # Create bad requests for all sub fields of object or array
            isObjectRef = '$ref' in specs['properties'][required_field]
            isArrayRef = prop_type == 'array' and '$ref' in specs['properties'][required_field]['items']
            if isArrayRef or isObjectRef:
                sub_component_name = None
                if isObjectRef:
                    sub_component_name = specs['properties'][required_field]['$ref']
                elif isArrayRef:
                    sub_component_name = specs['properties'][required_field]['items']['$ref']

                sub_component_json_schema = OpenApi.get_json_schema_from_component(swagger, sub_component_name)
                sub_component_body = OpenApi.get_json_body_from_component(swagger, sub_component_name)
                sub_component_bad_requests = Postman.generate_bad_requests(
                    swagger,
                    sub_component_name,
                    status_code,
                    method,
                    host_url,
                    endpoint,
                    sub_component_body,
                    test_script,
                    auth_type
                )

                for sub_component_bad_req in sub_component_bad_requests:
                    sub_component_json_body = json.loads(sub_component_bad_req['request']['body']['raw'])
                    if isObjectRef:
                        bad_request_body[required_field] = sub_component_json_body
                    elif isArrayRef:
                        bad_request_body[required_field] = [sub_component_json_body]
                    sub_component_bad_req['request']['body']['raw'] = json.dumps(bad_request_body,
                                                                                 separators=(',', ':'))

                requests.extend(sub_component_bad_requests)

        return requests

    @staticmethod
    def get_index_pm_resouce_folder(pm, resource_name):
        """
        Get the resource folder from postman collection.
        If doesn't exist, will create the resource folder

        Params:
          - pm: Postman collection
          - resource_name: Name of the resource

        Returns: Index of the resource
        """

        for index, resource in enumerate(pm['item']):
            if resource['name'] == resource_name:
                return index

        new_resource = {
            "name": resource_name,
            "item": [],
            "protocolProfileBehavior": {},
            "_postman_isSubFolder": True
        }
        pm['item'].append(new_resource)
        return len(pm['item']) - 1

    @staticmethod
    def get_index_pm_operation_folder(pm, resource_name, operation_name):
        """
        Get the roperation folder from postman collection.
        If doesn't exist, will create the operation folder

        Params:
          - pm: Postman collection
          - resource_name: Name of the resource
          - operation_name: Name of the operation

        Returns: Index of the operation
        """

        r_index = Postman.get_index_pm_resouce_folder(pm, resource_name)
        for o_index, operation in enumerate(pm['item'][r_index]['item']):
            if operation['name'] == operation_name:
                return o_index

        new_operation = {
            "name": operation_name,
            "item": [],
            "protocolProfileBehavior": {},
            "_postman_isSubFolder": True
        }

        pm['item'][r_index]['item'].append(new_operation)
        return len(pm['item'][r_index]['item']) - 1

    @staticmethod
    def find_header_by_key_and_delete(headers, key):
        """
        Find and delete a Postman request header by it's key

        Params:
          - headers: List of all headers
          - key: Key of the headers (name)

        Returns: Copy of headers without the key if found
        """

        copy_headers = list(headers)
        index = -1
        for i, head in enumerate(copy_headers):
            if head['key'] == key:
                index = i
        if index != -1:
            del copy_headers[index]
        return copy_headers

    @staticmethod
    def generate(openapi, cmd_args):
        """
        Generate a Postman Collection with requests and test scripts based on OpenApi file

        Params:
          - openapi: OpenApi JSON
          - cmd_args: Arguments passed in command line

        Returns: The name of the postman body collection of the file to be created and the data to be saved
        """

        track = Tracer('postman.pm.Postman.generate')
        pm = {}
        collection_name = create_collection_name(openapi)
        filename = f'{collection_name}.postman_collection.json'
        track.trace('Information about the Postman Collection generated')
        track.trace(f'Name: {collection_name}')
        track.trace(f'File: "{filename}"')
        host_url = cmd_args.host_url if cmd_args.host_url is not None else OpenApi.get_server_host_url(openapi,
                                                                                                       cmd_args.environment)
        if not host_url and cmd_args.environment is not None:
            raise InvalidEnvironmentValueError(
                f'Valor de ambiente definido "{cmd_args.environment}" não está definido no Swagger\n')
        track.trace(f'Host url definida pra todos as requisições: "{host_url}"')
        track.trace(f'Tipo de Autorização/Autenticação definido para o padrão: "{cmd_args.authorization_type}"')

        number_of_endpoints = len(openapi['paths'].keys())
        number_of_operations = 0
        number_of_test_requests = 0

        all_resources = set()

        pm['info'] = {
            "name": collection_name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        }
        pm['item'] = []

        success_body = None
        if cmd_args.file_success_body is not None:
            dirname = os.path.dirname(__file__)
            json_body_filename = os.path.join(dirname, cmd_args.file_success_body)
            try:
                with open(json_body_filename) as json_success_body_file:
                    success_body = json.load(json_success_body_file)
                    track.trace(
                        f'Request de sucesso definido corretamente para o corpo do arquivo: {json_body_filename}\n')
            except FileNotFoundError:
                print(f'=== Erro: Arquivo "{json_body_filename}" não foi encontrado\n')
            except json.decoder.JSONDecodeError:
                print(f'=== Erro: Arquivo "{json_body_filename}" não se encontra no formato JSON ou é inválido\n')
            finally:
                track.trace(f'Error - Unexpected error {sys.exc_info()[0]}')

        paths = openapi['paths']
        for endpoint in paths.keys():
            operations = paths[endpoint]
            for operation in operations.keys():
                number_of_operations += 1
                resource_name = operations[operation]['tags'][0]
                all_resources.add(resource_name)
                operation_name = operations[operation]['summary']
                method = operation.upper()
                r_index = Postman.get_index_pm_resouce_folder(pm, resource_name)
                o_index = Postman.get_index_pm_operation_folder(
                    pm,
                    resource_name, operations[operation]['summary']
                )

                pm_operation_folder = pm['item'][r_index]['item'][o_index]
                need_body_on_request = method in ('POST', 'PATCH', 'PUT')

                if need_body_on_request and cmd_args.generate_body_on_requests and 'requestBody' in operations[operation]:
                    request_component_name = \
                        operations[operation]['requestBody']['content']['application/json']['schema']['$ref']
                    body = OpenApi.get_json_body_from_component(openapi, request_component_name)
                else:
                    body = {}

                responses = operations[operation]['responses']
                for status_code in responses.keys():
                    number_of_test_requests += 1
                    response_description = responses[status_code]['description']
                    response_json_schema = None
                    if 'content' in responses[status_code]:
                        response_schema = responses[status_code]['content']['application/json']['schema']
                        response_json_schema = OpenApi.get_inside_object_properties(openapi, response_schema)

                    test_script = generate_test_script(response_json_schema, status_code)

                    request = None

                    if status_code in ('200', '201') and need_body_on_request and cmd_args.generate_body_on_requests:
                        # Use real data on success test
                        if success_body is not None:
                            request = create_request(status_code, response_description, method, host_url,
                                                             endpoint, success_body, test_script,
                                                             cmd_args.authorization_type)
                        else:
                            request = create_request(status_code, response_description, method, host_url,
                                                             endpoint, body, test_script, cmd_args.authorization_type)
                    elif status_code in ('400', '422'):
                        # Need generate bad requests
                        if need_body_on_request and cmd_args.generate_bad_requests:
                            bad_requests = Postman.generate_bad_requests(
                                openapi,
                                request_component_name,
                                status_code,
                                method,
                                host_url,
                                endpoint,
                                body,
                                test_script,
                                cmd_args.authorization_type
                            )
                            number_of_test_requests += len(bad_requests)
                            pm_operation_folder['item'].extend(bad_requests)
                            continue
                        else:
                            request = create_request(status_code, response_description, method, host_url,
                                                             endpoint, body, test_script, cmd_args.authorization_type)
                    elif status_code == '501':
                        endpoint_not_found = '/endpoint-nao-existe'
                        request = create_request(status_code, response_description, method, host_url,
                                                         endpoint_not_found, body, test_script,
                                                         cmd_args.authorization_type)
                    elif status_code == '401':
                        request = create_request(status_code, 'sem authorization headers', method, host_url,
                                                         endpoint, body, test_script, cmd_args.authorization_type)
                        headers = list(request['request']['header'])

                        # Without OAuth2.0 Client ID
                        request_name = create_request_name('401', 'sem client_id')
                        request['name'] = request_name
                        request['request']['header'] = Postman.find_header_by_key_and_delete(headers, 'client_id')
                        pm_operation_folder['item'].append(request)

                        # Without OAuth2.0 Access Token
                        request = copy.deepcopy(request)
                        request_name = create_request_name('401', 'sem access_token')
                        request['name'] = request_name
                        request['request']['header'] = Postman.find_header_by_key_and_delete(headers, 'access_token')
                        pm_operation_folder['item'].append(request)
                        continue
                    else:
                        request = create_request(status_code, response_description, method, host_url, endpoint,
                                                         body, test_script, cmd_args.authorization_type)

                    if request:
                        pm_operation_folder['item'].append(request)

        track.trace(f'Quantidade de endpoints tratados: {number_of_endpoints}')
        track.trace(f'Quantidade de recursos criados: {len(all_resources)}')
        track.trace(f'Quantidade de operações criadas: {number_of_operations}')
        track.trace(f'Quantidade de requisições criadas: {number_of_test_requests}')

        result = {
            'filename': filename,
            'collection': pm
        }

        track.log()

        return result
