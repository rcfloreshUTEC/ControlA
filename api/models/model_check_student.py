from django.db import models
from datetime import datetime

class Asistencia(models.Model):
    ID = models.AutoField(primary_key=True)
    carnet = models.CharField(max_length=20)
    fecha_hora = models.DateTimeField(default=datetime.utcnow)
    codMat = models.CharField(max_length=10)
    seccion = models.IntegerField()

    def __str__(self):
        return f'{self.carnet} - {self.fecha_hora}'