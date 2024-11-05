from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home_view(request):
    context = {
        'page_name': 'Inicio',
    }
    return render(request, "home/home.html", context)



@login_required
def user_profile_view(request):
    context = {
        'page_name': 'Perfil de Usuario',
    }
    return render(request, "home/userprofile.html", context)