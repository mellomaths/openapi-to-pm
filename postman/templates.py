import json
import textwrap

from datetime import datetime


def create_collection_name(openapi):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    default_collection_name = f'OpenAPI2PostmanCollection-{timestamp}'
    collection_name = openapi.get('info', {}).get('title', '')
    if not collection_name:
        collection_name = default_collection_name

    return collection_name


def create_request_name(status_code, description):
    """
    Create the request name

    Params:
      - status_code: HTTP status code of the request
      - description: It's description

    Returns: String with the name of request
    """
    return f'{status_code} ({description})'


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

    name = create_request_name(status_code, description)

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
