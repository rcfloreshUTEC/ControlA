from django.urls import path
from .views.view_agregar_asistencia import agregar_asistencia

urlpatterns = [

    path('agregar_asistencia/', agregar_asistencia, name='agregar_asistencia'),
]