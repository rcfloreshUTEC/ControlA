from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def upload_carga_academica(request):

    context = {
        'page_name': 'Carga Inscripci&oacute;n',
    }

    return render(request, 'academic/academico.html', context)