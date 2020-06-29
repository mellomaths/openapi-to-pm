class CustomException(Exception):

    def __init__(self, message):
        super(CustomException, self).__init__(message)


class OpenApiVersionError(CustomException):

    def __init__(self, message="OpenAPI version is not supported. Please inform OpenAPI 3.0.0."):
        super(OpenApiVersionError, self).__init__(message)


class OpenApiFormatError(CustomException):

    def __init__(self, message="The reported file does not follow the OpenAPI formatting standard."):
        super(OpenApiFormatError, self).__init__(message)


class InvalidEnvironmentValueError(CustomException):

    def __init__(self, message="Environment value is not defined in the OpenAPI file."):
        super(InvalidEnvironmentValueError, self).__init__(message)
