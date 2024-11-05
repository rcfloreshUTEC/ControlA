# home/urls.py
from django.urls import path
from .views.auth_views import CustomLoginView, custom_logout_view
from .views.main_views import home_view, user_profile_view

urlpatterns = [
    path("", home_view, name="home"),
    path("user_profile", user_profile_view, name="user_profile"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", custom_logout_view, name="logout"),
]