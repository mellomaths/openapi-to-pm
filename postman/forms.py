from django import forms

from .admin import DEFAULT_ENVIROMENT_CHOICES, DEFAULT_AUTHORIZATION_TYPE_CHOICES
from .exceptions import InvalidFormError

class SwaggerForm(forms.Form):

    generate_bad_requests = forms.BooleanField(required=False, initial=True, label='Gerar bad requests para os campos obrigatórios')
    # generate_body_on_requests = forms.BooleanField(required=False, initial=True, label='Gerar requests com corpo JSON na requisição')

    swagger_text = forms.CharField(widget=forms.Textarea, label='', required=False)
    swagger_file = forms.FileField(label='', required=False)

    # environment = forms.ChoiceField(required=False, choices=DEFAULT_ENVIROMENT_CHOICES, label='Ambiente')
    environment = forms.CharField(label='Ambiente', required=False)

    authorization_type = forms.ChoiceField(required=False, choices=DEFAULT_AUTHORIZATION_TYPE_CHOICES, label='Tipo de autenticação usado na API')

    @staticmethod
    def validate(swagger_text, swagger_file):
        if not swagger_text and not swagger_file:
            raise InvalidFormError('Por favor, cole o arquivo Swagger na area informada ou faça o upload do arquivo.')

        if len(swagger_text) > 0 and swagger_file is not None:
            raise InvalidFormError('Informe o Swagger pelo campo de texto ou por upload de arquivos.')
        
        return True
