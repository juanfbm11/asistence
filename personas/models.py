from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ('administrador', 'Administrador'),
        ('profesor', 'Profesor'),
        ('estudiante', 'Estudiante'),
    ]

    username = None
    email = models.EmailField(unique=True)

    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['rol', 'nombre', 'apellido']

    def __str__(self):
        return f"{self.email} ({self.rol})"


class Estudiante(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)

    colegio = models.CharField(max_length=100)
    clases = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}"


class Profesor(models.Model):
    TURNO_CHOICES = [
        ('mañana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('noche', 'Noche'),
    ]

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='profesor_perfil'
    )

    colegio = models.CharField(max_length=100)
    turno = models.CharField(max_length=20, choices=TURNO_CHOICES)
    clases= models.CharField(max_length=100)

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}"
