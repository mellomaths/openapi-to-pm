import os
import sys
import json

from config import CommandLineConfig
from exceptions import OpenApiVersionError, OpenApiFormatError, CustomException
from tracer import Tracer
from postman.pm import Postman


if __name__ == '__main__':
    this_filename = __file__
    tracer = Tracer('cli.py')
    tracer.trace('start.')
    tracer.trace('OpenAPI 2 Postman CLI.')
    cmd_config = CommandLineConfig(this_filename)
    args = cmd_config.get_arguments()
    directory_name = os.path.dirname(this_filename)

    openapi_filename = os.path.join(directory_name, args.openapi[0])

    tracer.trace(f'Handle the file {openapi_filename}.')
    has_success = False
    try:
        with open(openapi_filename) as file:
            data = json.load(file)

            version = data.get('openapi', None)
            if not version:
                raise OpenApiFormatError()
            elif version != '3.0.0':
                raise OpenApiVersionError()

            pm = Postman.generate(data, args)
            pm_collection_filename = pm['filename']
            with open(pm_collection_filename, 'w', encoding='utf-8') as file_result:
                json.dump(pm['collection'], file_result, ensure_ascii=False, indent=4)
                tracer.trace(f'Postman Collection file - {pm_collection_filename}.')
                has_success = True
    except FileNotFoundError as err:
        tracer.trace(f'Error - File {openapi_filename} was not found.')
    except json.decoder.JSONDecodeError as err:
        tracer.trace(f'Error - The file {openapi_filename} is not a JSON file.')
    except CustomException as err:
        tracer.trace(f'Error - {err}')
    finally:
        tracer.trace(f'Error - Unexpected error {sys.exc_info()[0]}')

    if has_success:
        tracer.trace(f'Execution ended successfully.')
        tracer.trace(f'Please check if the JSON file was saved and import the collection into Postman.')

    tracer.trace('end.')
