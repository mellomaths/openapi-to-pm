import os
import json
import argparse

from postman.pm import Postman

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='description: Gera uma collection para testes no Postman em formato JSON dado um swagger 3.0',
        usage=f'python3 {__file__} caminho/para/swagger.json -sb caminho/para/exemplo.json -e Desenvolvimento -u http://localhost:3000 -gen-body -gen-badreq',
        epilog='por: Matheus Mello de Lima (@mellomaths)'
    )

    # Required
    parser.add_argument(
        'swagger',
        metavar='swagger',
        type=str,
        nargs='+',
        help='Caminho para o arquivo swagger')

    # Optionals
    parser.add_argument(
        '-sb',
        '--success-body',
        dest='file_success_body',
        help='Nome do arquivo de exemplo de corpo da requisição com valores que seja executada com sucesso. Usar somente em caso de POST, PATCH ou PUT (requisições que obrigatoriamente possuam um corpo)'
    )

    parser.add_argument(
        '-auth',
        '--authorization-type',
        dest='authorization_type',
        help='Tipo de Authorization a ser usada nos headers das requisições (Examplo: oauth)',
        default='oauth'
    )

    parser.add_argument(
        '-e',
        '--env',
        dest='environment',
        help='Ambiente definido no Swagger para qual todos os request estarão apontando (default: urls não preenchidas)')

    parser.add_argument(
        '-u',
        '--url',
        dest='host_url',
        help='Customização de uma host url para os requests (default: usar a definida pelo ambiente)'
    )

    parser.add_argument(
        '-gen-body',
        '--generate-body',
        dest='generate_body_on_requests',
        type=CommandLine.str2bool,
        help='Se passado, todos os request serão gerados com corpo de acordo com os schemas definido no Swagger (default: false)',
        nargs='?',
        const=True,
        default=False
    )

    parser.add_argument(
        '-gen-badreq',
        '--generate-bad-requests',
        dest='generate_bad_requests',
        type=CommandLine.str2bool,
        help='Se passado, serão gerados um bad request para cada campo obrigatório de acordo com os schemas definido no Swagger (default: false)',
        nargs='?',
        const=True,
        default=False
    )

    args = parser.parse_args()
    dirname = os.path.dirname(__file__)
    success_collections = []

    duplicates = Helper.get_duplicates(args.swagger)
    if len(duplicates) > 0:
        print(
            f'\n--- OBS: Os seguintes arquivos foram informados mais de uma vez: {duplicates}')

    if len(args.swagger) > 1 and (args.file_success_body or args.environment or args.host_url):
        print(f'\n=== Erro: Os parametros --success-body --env --url só são válidos quando é passado um único arquivo Swagger para ser tratado')
        sys.exit(2)

    for swagger in set(args.swagger):
        filename = os.path.join(dirname, swagger)
        print(f'\n>>> Tratando o arquivo "{swagger}"')

        try:
            with open(filename) as file:
                data = json.load(file)

                if 'openapi' not in data:
                    raise SwaggerFormatError(
                        'O arquivo JSON informado não respeita o padrão Swagger')
                elif data['openapi'] != '3.0.0':
                    raise SwaggerVersionError(
                        'A versão do Swagger informado não é suportada. Informe um Swagger Open Api 3.0.0')

                pm = Postman.generate(data, args)
                with open(pm['filename'], 'w', encoding='utf-8') as file_result:
                    json.dump(pm['collection'], file_result,
                              ensure_ascii=False, indent=4)

            success_collections.append(swagger)
            print()
        except FileNotFoundError:
            print(f'=== Erro: Arquivo "{swagger}" não foi encontrado\n')
        except json.decoder.JSONDecodeError:
            print(
                f'=== Erro: Arquivo "{swagger}" não se encontra no formato JSON ou é inválido\n')
        except CustomizableException as error:
            print(f'=== Erro: {error}\n')
        except Exception as error:
            logging.exception(
                f'=== Erro: Ocorreu um problema inesperado. Favor verifique\n')

    hasError = len(args.swagger) != len(success_collections)
    hasSuccess = len(success_collections) > 0
    if hasError and hasSuccess:
        print('\n>>> Execução finalizada com sucesso parcial')
    elif hasError and not hasSuccess:
        print('\n>>> Execução finalizada com erros')
    else:
        print('\n>>> Execução finalizada com sucesso')

    print(
        f'>>> Foram criadas {len(success_collections)} collections para o Postman')
    print('>>> Verifique se foram criados os arquivos informados no log acima')
    print('>>> Importe a collection no Postman e realize seus testes')
