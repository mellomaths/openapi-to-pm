import argparse


class CommandLineConfig:

    creator = 'Matheus Mello de Lima (@mellomaths)'
    description = 'Generate a Postman collection with tests scripts bases on a OpenAPI 3.0 JSON file.'

    def __init__(self, cli_filename):
        self.usage = f'python3 {cli_filename} path/to/openapi.json -e Sandbox -u http://localhost:8080 -gen-badreq'
        self.parser = self.config_argument_parser()

    def config_argument_parser(self):
        parser = argparse.ArgumentParser(
            description=f'description: {self.description}',
            usage=self.usage,
            epilog=f'by: {self.creator}'
        )

        # Required
        parser.add_argument(
            'openapi',
            metavar='openapi',
            type=str,
            nargs=1,
            help='Relative path to OpenAPI file.'
        )

        # Optionals
        parser.add_argument(
            '-e',
            '--env',
            dest='environment',
            help='Environment defined on OpenAPI file to send all requests (default: urls will be empty).'
        )

        parser.add_argument(
            '-gen-badreq',
            '--generate-bad-requests',
            dest='generate_bad_requests',
            type=CommandLineConfig.str2bool,
            help='Will generate bad requests for POST and PUT operations based on schema defined in the OpenAPI file.',
            nargs='?',
            const=True,
            default=False
        )

        return parser

    def get_arguments(self):
        args = self.parser.parse_args()
        return args

    @staticmethod
    def str2bool(v):
        """
        Convert String to Boolean
        """

        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    @staticmethod
    def log(message):
        print(f'\n=== {message}')

