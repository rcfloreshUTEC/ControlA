from django.db import models

class CargaInscripcion(models.Model):
    Carnet = models.CharField(max_length=12)
    CodMat = models.CharField(max_length=10)
    Seccion = models.IntegerField()
    Ciclo = models.CharField(max_length=20)
    CodInscripcion = models.CharField(max_length=15, null=True, blank=False)

    def __str__(self):
        return f"{self.Carnet} - {self.CodMat}"


