# Custom exceptions for raising
class CustomizableException(Exception):
  pass

class SwaggerVersionError(CustomizableException):
  pass

class SwaggerFormatError(CustomizableException):
  pass

class InvalidEnvironmentValueError(CustomizableException):
  pass

class NotJsonFileError(CustomizableException):
    pass

class InvalidFormError(CustomizableException):
  pass
