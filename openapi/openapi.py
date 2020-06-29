import copy


class OpenApi:

    @staticmethod
    def get_inside_object_properties(openapi, specs):
        """
        Get all properties for all objects inside the given object recursively

        Params:
          - openapi: OpenApi JSON
          - specs: JSON Schema of the object

        Returns: JSON Schema of the object
        """

        json_schema = copy.deepcopy(specs)
        if '$ref' in specs:
            json_schema = OpenApi.get_json_schema_from_component(openapi, specs['$ref'])
        elif 'type' in specs:
            if specs['type'] == 'object':
                properties = specs['properties']

                for prop in properties:
                    if '$ref' in properties[prop]:
                        sub_prop_component_name = properties[prop]['$ref']
                        json_schema['properties'][prop] = OpenApi.get_json_schema_from_component(openapi,
                                                                                                 sub_prop_component_name)
                    elif properties[prop]['type'] == 'object' and 'properties' in properties[prop]:
                        json_schema['properties'][prop] = OpenApi.get_inside_object_properties(openapi,
                                                                                               specs['properties'][
                                                                                                   prop])

            if specs['type'] == 'array':
                items = specs['items']

                if '$ref' in specs['items']:
                    json_schema['items'] = OpenApi.get_json_schema_from_component(openapi, specs['items']['$ref'])
                else:
                    json_schema['items'] = OpenApi.get_inside_object_properties(openapi, specs['items'])

        return json_schema

    @staticmethod
    def get_json_schema_from_component(openapi, component_name):
        """
        Get the JSON Schema defined on Swagger of a given component by it's name

        Params:
          - openapi: OpenApi JSON
          - component_name: Name of the component in the format: "#/components/schemas/Object"

        Returns: JSON Schema of the object
        """

        schema_name = component_name.split('/')[-1]
        specs = openapi['components']['schemas'][schema_name]
        return OpenApi.get_inside_object_properties(openapi, specs)

    @staticmethod
    def get_server_host_url(openapi, environment):
        """
        Get the host URL defined on Swagger by it's description

        Params:
          - openapi: OpenApi JSON
          - environment: Description of the environment defined on swagger

        Returns: String of the environment URL if found
        """

        for server in openapi['servers']:
            if server['description'] == environment:
                return server['url']

        return None

    @staticmethod
    def create_json_body_from_properties(openapi, properties):
        """
        Creates a fake json body from a given object properties defined on json schema of a swagger

        Params:
          - openapi: OpenApi JSON
          - properties: Object properties of the field on JSON Schema

        Returns: JSON body object with fake data
        """

        body = {}
        for prop in properties.keys():

            if '$ref' in properties[prop]:
                body[prop] = OpenApi.get_json_body_from_component(openapi, properties[prop]['$ref'])
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
                    item = OpenApi.get_json_body_from_component(openapi, subcomponent_name)
                    body[prop].append(item)
            elif prop_type == 'object':
                subproperties = properties[prop]['properties']
                body[prop] = OpenApi.create_json_body_from_properties(openapi, subproperties)
            elif not prop_type and '$ref' in properties[prop]:
                subcomponent_name = properties[prop]['$ref']
                body[prop] = OpenApi.get_json_body_from_component(openapi, subcomponent_name)
            else:
                body[prop] = 'string'

        return body

    @staticmethod
    def get_json_body_from_component(openapi, component_name):
        """
        Calls create_json_body_from_properties to create fake json body of a given component

        Params:
          - openapi: OpenApi JSON
          - component_name: Name of the component in the format: "#/components/schemas/Object"

        Returns: JSON body object with fake data
        """

        schema = component_name.split('/')[-1]
        specs = openapi['components']['schemas'][schema]
        body = None

        if 'properties' in specs:
            body = OpenApi.create_json_body_from_properties(openapi, specs['properties'])
        elif 'items' in specs:
            body = OpenApi.get_inside_object_properties(openapi, specs['items'])
        return body

