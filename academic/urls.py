from django.urls import path
from academic.views.view_carga_academica import upload_carga_academica
from academic.views.view_carga_inscripcion import upload_carga_inscripcion

urlpatterns = [
    path('upload_carga_academica/', upload_carga_academica, name='upload_carga_academica'),
    path('upload_carga_inscripcion/', upload_carga_inscripcion, name='upload_carga_inscripcion'),
]