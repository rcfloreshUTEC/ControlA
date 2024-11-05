from django.urls import path
from .views.view_check_student import check_student
from .views.api_powermongo import get_mongo_data
from .views.api_fakeinfo import api_fakeinfo


urlpatterns = [
    path('check_student/', check_student, name='check_student'),
    path('mongo-data/', get_mongo_data, name='get_mongo_data'),

    path('api_fakeinfo/', api_fakeinfo, name='api_fakeinfo'),
]