# home/views/auth_views.py
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect


class CustomLoginView(LoginView):
    template_name = "home/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("home")


def custom_logout_view(request):
    logout(request)
    return redirect("login")
