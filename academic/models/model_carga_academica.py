from django.db import models

class CargaAcademica(models.Model):
    Escuela = models.CharField(max_length=50)
    CodMat = models.CharField(max_length=10)
    Nombre = models.CharField(max_length=100)
    Docente = models.CharField(max_length=100)
    CodEmp = models.CharField(max_length=10, null=True, blank=True)
    Seccion = models.CharField(max_length=10)
    Hora = models.CharField(max_length=20)
    Dias = models.CharField(max_length=50)
    Cupo = models.IntegerField()
    Inscritos = models.IntegerField()
    Aula = models.CharField(max_length=50, null=True, blank=True)  # Permitir nulos
    Estado = models.CharField(max_length=20)
    Paralela = models.CharField(max_length=10)
    Ciclo = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.CodMat} - {self.Nombre}"