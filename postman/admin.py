from django.contrib import admin

# Register your models here.

DEFAULT_ENVIROMENT_CHOICES = (
    ( 'Sandbox', 'Sandbox' ),
    ( 'Desenvolvimento', 'Desenvolvimento' ),
    ( 'Homologação', 'Homologação' ),
    ( 'Produção', 'Produção' )
)

DEFAULT_AUTHORIZATION_TYPE_CHOICES = (
    ( 'oauth', 'OAuth 2.0' ),
    ( 'jwt', 'JWT' )
)
