from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UsuarioManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "administrador")
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ('administrador', 'administrador'),
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
    objects = UsuarioManager()

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
