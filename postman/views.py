import re

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView, CreateView

from .forms import SwaggerForm
from .services import handle_file_upload, handle_swagger_from_text, get_postman_data_from_file, download_file

from .exceptions import CustomizableException

from .pm import PostmanProperties

# Create your views here.


def homepage(request):
    form = SwaggerForm()
    alert = None

    try:
        if request.method == 'POST':
            swagger_text = request.POST.get('swagger_text', '')
            swagger_file = request.FILES.get('swagger_file', None)

            form = SwaggerForm(request.POST, request.FILES)
            SwaggerForm.validate(swagger_text, swagger_file)

            environment = form['environment'].value()
            is_postman_variable = False
            postman_variable_pattern = re.compile('^\{\{(.*?)\}\}$')
            if postman_variable_pattern.match(environment):
                is_postman_variable = True

            props = PostmanProperties(
                form['generate_bad_requests'].value(),
                environment if is_postman_variable else None,
                environment if not is_postman_variable else None,
                form['authorization_type'].value()
            )

            result = None
            if swagger_file is not None:
                result = handle_file_upload(swagger_file, props)

            if form['swagger_text'].value():
                result = handle_swagger_from_text(
                    form['swagger_text'].value(), props)

            return redirect('result', collection_name=result['filename'])
        else:
            form = SwaggerForm()
    except CustomizableException as error:
        alert = error

    if alert is not None:
        return render(request, 'home.html', {'form': form, 'alerts': [alert]})

    return render(request, 'home.html', {'form': form})


def result(request, collection_name):
    if request.method == 'POST':
        return download_file(collection_name)

    pm = get_postman_data_from_file(collection_name)
    metrics = pm['metrics']

    return render(
        request,
        'result.html',
        {
            'collection': pm['collection_str'],
            'endpoints': metrics['endpoints'],
            'resources': metrics['resources'],
            'operations': metrics['operations'],
            'test_requests': metrics['test_requests'],
            'collection_name': collection_name
        }
    )
