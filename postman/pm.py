import os
import sys
import json
import copy
import logging
import textwrap

from .exceptions import SwaggerVersionError, SwaggerFormatError, InvalidEnvironmentValueError, CustomizableException


class Tracer:

    """
    Responsible to handle logging inside functions on script
    """

    def __init__(self):
        self.messages = []

    def trace(self, msg):
        self.messages.append(msg)

    def log(self):
        for msg in self.messages:
            print(f'>>> {msg}')


class Swagger:

    @staticmethod
    def get_inside_object_properties(swagger, specs):
        """
        Get all properties for all objects inside the given object recursively

        Params:
          - swagger: Swagger JSON
          - specs: JSON Schema of the object

        Returns: JSON Schema of the object
        """

        json_schema = copy.deepcopy(specs)
        if '$ref' in specs:
            json_schema = Swagger.get_json_schema_from_component(
                swagger, specs['$ref'])
        elif 'type' in specs:
            if specs['type'] == 'object':
                properties = specs['properties']

                for prop in properties:
                    if '$ref' in properties[prop]:
                        sub_prop_component_name = properties[prop]['$ref']
                        json_schema['properties'][prop] = Swagger.get_json_schema_from_component(
                            swagger, sub_prop_component_name)
                    elif properties[prop]['type'] == 'object' and 'properties' in properties[prop]:
                        json_schema['properties'][prop] = Swagger.get_inside_object_properties(
                            swagger, specs['properties'][prop])

            if specs['type'] == 'array':
                items = specs['items']

                if '$ref' in specs['items']:
                    json_schema['items'] = Swagger.get_json_schema_from_component(
                        swagger, specs['items']['$ref'])
                else:
                    json_schema['items'] = Swagger.get_inside_object_properties(
                        swagger, specs['items'])

        return json_schema

    @staticmethod
    def get_json_schema_from_component(swagger, component_name):
        """
        Get the JSON Schema defined on Swagger of a given component by it's name

        Params:
          - swagger: Swagger JSON
          - component_name: Name of the component in the format: "#/components/schemas/Object"

        Returns: JSON Schema of the object
        """

        schema_name = component_name.split('/')[-1]
        specs = swagger['components']['schemas'][schema_name]
        return Swagger.get_inside_object_properties(swagger, specs)

    @staticmethod
    def get_server_host_url(swagger, environment):
        """
        Get the host URL defined on Swagger by it's description

        Params:
          - swagger: Swagger JSON
          - environment: Description of the environment defined on swagger

        Returns: String of the environment URL if found
        """

        url = None
        for server in swagger['servers']:
            if 'description' in server and server['description'] == environment:
                url = server['url']

        if not url:
            url = swagger['servers'][0]['url']

        return url

    @staticmethod
    def create_json_body_from_properties(swagger, properties):
        """
        Creates a fake json body from a given object properties defined on json schema of a swagger 

        Params:
          - swagger: Swagger JSON
          - properties: Object properties of the field on JSON Schema

        Returns: JSON body object with fake data
        """

        body = {}
        for prop in properties.keys():

            if '$ref' in properties[prop]:
                body[prop] = Swagger.get_json_body_from_component(
                    swagger, properties[prop]['$ref'])
                continue

            prop_type = properties[prop]['type']
            if prop_type == 'boolean':
                body[prop] = False
            elif prop_type == 'number':
                body[prop] = 0
            elif prop_type == 'array':
                body[prop] = []
                if '$ref' in properties[prop]['items']:
                    subcomponent_name = properties[prop]['items']['$ref']
                    item = Swagger.get_json_body_from_component(
                        swagger, subcomponent_name)
                    body[prop].append(item)
            elif prop_type == 'object':
                subproperties = properties[prop]['properties']
                body[prop] = Swagger.create_json_body_from_properties(
                    swagger, subproperties)
            elif not prop_type and '$ref' in properties[prop]:
                subcomponent_name = properties[prop]['$ref']
                body[prop] = Swagger.get_json_body_from_component(
                    swagger, subcomponent_name)
            else:
                body[prop] = 'string'

        return body

    @staticmethod
    def get_json_body_from_component(swagger, component_name):
        """
        Calls create_json_body_from_properties to create fake json body of a given component

        Params:
          - swagger: Swagger JSON
          - component_name: Name of the component in the format: "#/components/schemas/Object"

        Returns: JSON body object with fake data
        """

        schema = component_name.split('/')[-1]
        specs = swagger['components']['schemas'][schema]
        body = None

        if 'properties' in specs:
            body = Swagger.create_json_body_from_properties(
                swagger, specs['properties'])
        elif 'items' in specs:
            inner_object_properties = Swagger.get_inside_object_properties(
                swagger, specs['items'])
            object_body = Swagger.create_json_body_from_properties(swagger, inner_object_properties['properties'])
            body = [object_body]
        return body


class Postman:

    @staticmethod
    def create_request_name(status_code, description):
        """
        Create the request name

        Params:
          - status_code: HTTP status code of the request
          - description: It's description

        Returns: String with the name of request
        """
        return f'{status_code} ({description})'

    @staticmethod
    def create_request(status_code, description, method, host_url, endpoint, body, test_script, auth_type):
        """
        Create a Postman request with body and test script

        Params:
          - status_code: HTTP status code of the request
          - description: It's description
          - method: Request HTTP method (GET, POST, PUT, PATCH, DELETE)
          - host_url: The base url for all requests
          - endpoint: Endpoint of the operation request
          - body: JSON body the request
          - test_script: String with JavaScript to execute test on Postman
          - auth_type: Authorization type to use on headers

        Returns: Object representing a request on Postman with body and test
        """

        name = Postman.create_request_name(status_code, description)

        headers = []

        if method in ('POST', 'PATCH', 'PUT'):
            headers.append({
                "key": "Content-Type",
                "name": "Content-Type",
                "type": "text",
                "value": "application/json"
            })

        if auth_type == 'oauth':
            headers.append({
                "key": "client_id",
                "type": "text",
                "value": "{{client_id}}"
            })
            headers.append({
                "key": "access_token",
                "type": "text",
                "value": "{{access_token}}"
            })

        paths = endpoint.split('/')

        request = {
            "name": name,
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [test_script]
                    }
                }
            ],
            "request": {
                "method": method,
                "header": headers,
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(body, separators=(',', ': '), indent=4)
                },
                "url": {
                    "raw": f'{host_url}/{endpoint}',
                    "host": [
                        host_url
                    ],
                    "path": paths
                }
            },
            "response": []
        }

        return request

    @staticmethod
    def generate_test_script(json_schema, status_code):
        """
        Generate a generic test script in JavaScript to execute on Postman

        Params:
          - json_schema: Response JSON Schema expected
          - status_code: Status code expected on request

        Returns: String with the JavaScript Postman test script
        """

        test_script = f"""\
    const statusCodeExpected = {status_code};

    pm.test('Status code is ' + statusCodeExpected, function() {{
      pm.response.to.have.status(statusCodeExpected);
    }});

    pm.test('Header Content-Type definido', function() {{
      pm.response.to.have.header('Content-Type');
    }});

    pm.test('Content-Type igual a application/json', function() {{
      const headers = pm.response.headers.all();

      for (let i = 0; i < headers.length; i++) {{
        const head = headers[i];
        if (head.key === 'Content-Type') {{
          pm.expect(head.value).to.include('application/json');
        }}
      }}
    }});
    """

        if json_schema:
            test_script += f"""
    const jsonResponseBody = pm.response.json();

    const jsonSchema = {json_schema};

    pm.test('JSON Schema validado', function() {{
      pm.expect(tv4.validate(jsonResponseBody, jsonSchema)).to.be.true;
    }});
    """

        return textwrap.dedent(test_script)

    @staticmethod
    def generate_bad_requests(swagger, component_name, status_code, method, host_url, endpoint, body, test_script, auth_type):
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
            try:
                prop_type = specs['properties'][required_field]['type']
            except KeyError:
                raise SwaggerFormatError(
                    f'Campo obrigatório {required_field} no component {schema} não tem tipagem definida no Swagger')

            # Create test without the field
            bad_request_body = copy.deepcopy(body)
            description = f'sem {required_field}'
            del bad_request_body[required_field]
            req = Postman.create_request(
                status_code, description, method, host_url, endpoint, bad_request_body, test_script, auth_type)
            requests.append(req)

            # Create test with wrong type in field
            bad_request_body = copy.deepcopy(body)
            description = f'{required_field} tipagem inválida'

            if prop_type in ('boolean', 'number', 'array', 'object'):
                bad_request_body[required_field] = 'tipo inválido'
            else:
                bad_request_body[required_field] = 10

            req = Postman.create_request(
                status_code, description, method, host_url, endpoint, bad_request_body, test_script, auth_type)
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

                req = Postman.create_request(
                    status_code, description, method, host_url, endpoint, bad_request_body, test_script, auth_type)
                requests.append(req)

            # Create bad requests for all sub fields of object or array
            isObjectRef = '$ref' in specs['properties'][required_field]
            isArrayRef = prop_type == 'array' and '$ref' in specs[
                'properties'][required_field]['items']
            if isArrayRef or isObjectRef:
                sub_component_name = None
                if isObjectRef:
                    sub_component_name = specs['properties'][required_field]['$ref']
                elif isArrayRef:
                    sub_component_name = specs['properties'][required_field]['items']['$ref']

                sub_component_json_schema = Swagger.get_json_schema_from_component(
                    swagger, sub_component_name)
                sub_component_body = Swagger.get_json_body_from_component(
                    swagger, sub_component_name)
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
                    sub_component_json_body = json.loads(
                        sub_component_bad_req['request']['body']['raw'])
                    if isObjectRef:
                        bad_request_body[required_field] = sub_component_json_body
                    elif isArrayRef:
                        bad_request_body[required_field] = [
                            sub_component_json_body]
                    sub_component_bad_req['request']['body']['raw'] = json.dumps(
                        bad_request_body, separators=(',', ':'))

                requests.extend(sub_component_bad_requests)

        return requests

    @staticmethod
    def generate_query_param_bad_requests(swagger, parameters, status_code, method, host_url, endpoint, test_script, auth_type):
        pass

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
    def generate(swagger, props):
        """
        Generate the postman collection, requests and tests receiving the swagger file data

        Params:
          - swagger: Swagger JSON
          - props: Arguments passed in command line

        Returns: The name of the postman body collection of the file to be created and the data to be saved
        """

        print(props)

        track = Tracer()
        pm = {}
        collection_name = swagger['info']['title'].strip()
        collection_name_template = collection_name.replace(' ', '_')
        filename = f'{collection_name_template}.postman_collection.json'
        track.trace('Informações sobre a Collection do Postman')
        track.trace(f'Nome da Collection: {collection_name}')
        track.trace(f'Arquivo com a collection do Postman: "{filename}"')
        host_url = props.host_url if props.host_url is not None else Swagger.get_server_host_url(
            swagger, props.environment)
        if not host_url and not props.environment:
            raise InvalidEnvironmentValueError(
                f'Valor de ambiente definido "{props.environment}" não está definido no Swagger\n')
        track.trace(
            f'Host url definida pra todos as requisições: "{host_url}"')
        track.trace(
            f'Tipo de Autorização/Autenticação definido para o padrão: "{props.authorization_type}"')

        number_of_endpoints = len(swagger['paths'].keys())
        number_of_operations = 0
        number_of_test_requests = 0

        all_resources = set()

        pm['info'] = {
            "name": collection_name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        }
        pm['item'] = []

        success_body = None
        if props.file_success_body is not None:
            dirname = os.path.dirname(__file__)
            json_body_filename = os.path.join(dirname, props.file_success_body)
            try:
                with open(json_body_filename) as json_success_body_file:
                    success_body = json.load(json_success_body_file)
                    track.trace(
                        f'Request de sucesso definido corretamente para o corpo do arquivo: {json_body_filename}\n')
            except FileNotFoundError:
                print(
                    f'=== Erro: Arquivo "{json_body_filename}" não foi encontrado\n')
            except json.decoder.JSONDecodeError:
                print(
                    f'=== Erro: Arquivo "{json_body_filename}" não se encontra no formato JSON ou é inválido\n')
            except CustomizableException as error:
                print(f'=== Erro: {error}\n')
            except Exception as error:
                logging.exception(
                    f'=== Erro: Ocorreu um problema inesperado. Favor verifique\n')
                print(error)

        paths = swagger['paths']
        for endpoint in paths.keys():
            operations = paths[endpoint]
            for operation in operations.keys():
                number_of_operations += 1
                resource_name = operations[operation]['tags'][0]
                all_resources.add(resource_name)

                operation_name = None
                if 'summary' in operations[operation]:
                    operation_name = operations[operation]['summary']
                elif 'description' in operations[operation]:
                    operation_name = operations[operation]['description']
                else:
                    operation_name = f'Operação {number_of_operations}'

                method = operation.upper()
                r_index = Postman.get_index_pm_resouce_folder(
                    pm, resource_name)
                o_index = Postman.get_index_pm_operation_folder(
                    pm,
                    resource_name,
                    operation_name
                )

                pm_operation_folder = pm['item'][r_index]['item'][o_index]
                need_body_on_request = method in ('POST', 'PATCH', 'PUT')

                if need_body_on_request and props.generate_body_on_requests and 'requestBody' in operations[operation]:
                    request_component_name = operations[operation]['requestBody'][
                        'content']['application/json']['schema']['$ref']
                    body = Swagger.get_json_body_from_component(
                        swagger, request_component_name)
                else:
                    body = {}

                responses = operations[operation]['responses']
                for status_code in responses.keys():
                    number_of_test_requests += 1
                    response_description = responses[status_code]['description']
                    response_json_schema = None
                    if 'content' in responses[status_code]:
                        response_schema = responses[status_code]['content']['application/json']['schema']
                        response_json_schema = Swagger.get_inside_object_properties(
                            swagger, response_schema)

                    test_script = Postman.generate_test_script(
                        response_json_schema, status_code)

                    request = None

                    if status_code in ('200', '201') and need_body_on_request and props.generate_body_on_requests:
                        # Use real data on success test
                        if success_body is not None:
                            request = Postman.create_request(
                                status_code, response_description, method, host_url, endpoint, success_body, test_script, props.authorization_type)
                        else:
                            request = Postman.create_request(
                                status_code, response_description, method, host_url, endpoint, body, test_script, props.authorization_type)
                    elif status_code in ('400', '422'):
                        # Need generate bad requests
                        if need_body_on_request and props.generate_bad_requests:
                            bad_requests = Postman.generate_bad_requests(
                                swagger,
                                request_component_name,
                                status_code,
                                method,
                                host_url,
                                endpoint,
                                body,
                                test_script,
                                props.authorization_type
                            )
                            number_of_test_requests += len(bad_requests)
                            pm_operation_folder['item'].extend(bad_requests)
                            continue
                        elif method == 'GET' and props.generate_bad_requests and 'parameters' in operations[operation]:
                            parameters = operations[operation]['parameters']
                            # Gerar requests com erro no query param
                            pass
                        else:
                            request = Postman.create_request(
                                status_code, response_description, method, host_url, endpoint, body, test_script, props.authorization_type)
                    elif status_code == '501':
                        endpoint_not_found = '/endpoint-nao-existe'
                        request = Postman.create_request(
                            status_code, response_description, method, host_url, endpoint_not_found, body, test_script, props.authorization_type)
                    elif status_code == '401':
                        request = Postman.create_request(
                            status_code, 'sem authorization headers', method, host_url, endpoint, body, test_script, props.authorization_type)
                        headers = list(request['request']['header'])

                        # Without OAuth2.0 Client ID
                        request_name = Postman.create_request_name(
                            '401', 'sem client_id')
                        request['name'] = request_name
                        request['request']['header'] = Postman.find_header_by_key_and_delete(
                            headers, 'client_id')
                        pm_operation_folder['item'].append(request)

                        # Without OAuth2.0 Access Token
                        request = copy.deepcopy(request)
                        request_name = Postman.create_request_name(
                            '401', 'sem access_token')
                        request['name'] = request_name
                        request['request']['header'] = Postman.find_header_by_key_and_delete(
                            headers, 'access_token')
                        pm_operation_folder['item'].append(request)
                        continue
                    else:
                        request = Postman.create_request(
                            status_code, response_description, method, host_url, endpoint, body, test_script, props.authorization_type)

                    if request:
                        pm_operation_folder['item'].append(request)

        track.trace(f'Quantidade de endpoints tratados: {number_of_endpoints}')
        track.trace(f'Quantidade de recursos criados: {len(all_resources)}')
        track.trace(f'Quantidade de operações criadas: {number_of_operations}')
        track.trace(
            f'Quantidade de requisições criadas: {number_of_test_requests}')

        metrics = {
            'endpoints': number_of_endpoints,
            'resources': len(all_resources),
            'operations': number_of_operations,
            'test_requests': number_of_test_requests
        }

        result = {
            'filename': filename,
            'collection': pm,
            'metrics': metrics
        }

        track.log()

        return result


class PostmanProperties:

    def __init__(self, generate_bad_requests, host_url, environment, authorization_type):
        self.generate_bad_requests = generate_bad_requests
        self.generate_body_on_requests = True
        self.host_url = host_url
        self.environment = environment
        self.authorization_type = authorization_type
        self.file_success_body = None

    def __repr__(self):
        return f"""
        Postman Properties:::

        Generate_Bad_Requests = {self.generate_bad_requests}
        Generate_Body_On_Requests = {self.generate_body_on_requests}
        Host_Url = {self.host_url}
        Environment = {self.environment}
        Authorization_Type = {self.authorization_type}
        File_Success_Body = {self.file_success_body}
        """
