from django.urls import path

from .views import homepage, result

urlpatterns = [
    path('', homepage, name='home'),
    path(r'result/<collection_name>', result, name='result')
]
