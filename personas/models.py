import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


# ──────────────────────────────────────────────
#  MANAGER DE USUARIO
# ──────────────────────────────────────────────
class UsuarioManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff",     True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol",          "administrador")
        return self.create_user(email, password, **extra_fields)


# ──────────────────────────────────────────────
#  USUARIO BASE
# ──────────────────────────────────────────────
class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ('administrador', 'Administrador'),
        ('profesor',      'Profesor'),
        ('estudiante',    'Estudiante'),
    ]

    username  = None
    email     = models.EmailField(unique=True)
    rol       = models.CharField(max_length=20, choices=ROLE_CHOICES)
    nombre    = models.CharField(max_length=100)
    apellido  = models.CharField(max_length=100)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['rol', 'nombre', 'apellido']
    objects         = UsuarioManager()

    def __str__(self):
        return f"{self.email} ({self.rol})"


# ──────────────────────────────────────────────
#  PERFIL ESTUDIANTE
# ──────────────────────────────────────────────
class Estudiante(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='estudiante'
    )
    colegio = models.CharField(max_length=100, blank=True)
    clases  = models.CharField(max_length=200, blank=True)  # texto legacy

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}"


# ──────────────────────────────────────────────
#  PERFIL PROFESOR
# ──────────────────────────────────────────────
class Profesor(models.Model):
    TURNO_CHOICES = [
        ('mañana', 'Mañana'),
        ('tarde',  'Tarde'),
        ('noche',  'Noche'),
    ]

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='profesor_perfil'
    )
    colegio = models.CharField(max_length=100, blank=True)
    turno   = models.CharField(max_length=20, choices=TURNO_CHOICES, blank=True)
    clases  = models.CharField(max_length=200, blank=True)  # texto legacy

    def __str__(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}"


# ──────────────────────────────────────────────
#  CLASE  (materia con relaciones reales)
# ──────────────────────────────────────────────
class Clase(models.Model):
    nombre      = models.CharField(max_length=100)
    codigo      = models.CharField(max_length=30, unique=True)
    aula        = models.CharField(max_length=50, blank=True)
    color       = models.CharField(max_length=7, default='#3b74f5')
    profesor    = models.ForeignKey(
        Profesor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='mis_clases'
    )
    estudiantes = models.ManyToManyField(
        Estudiante,
        blank=True,
        related_name='mis_clases'
    )
    activa    = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} – {self.nombre}"

    def total_estudiantes(self):
        return self.estudiantes.count()

    def porcentaje_asistencia(self):
        total = Asistencia.objects.filter(clase=self).count()
        if not total:
            return 0
        presentes = Asistencia.objects.filter(clase=self, estado='presente').count()
        return round(presentes / total * 100, 1)


# ──────────────────────────────────────────────
#  SESIÓN QR  (cada "Generar QR" crea una)
# ──────────────────────────────────────────────
class QRSesion(models.Model):
    clase     = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name='sesiones_qr'
    )
    token     = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    fecha     = models.DateField(default=timezone.localdate)
    creada_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField(blank=True, null=True)
    activa    = models.BooleanField(default=True)

    class Meta:
        ordering = ['-creada_en']

    def save(self, *args, **kwargs):
        if not self.expira_en:
            self.expira_en = timezone.now() + timezone.timedelta(seconds=120)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"QR {self.clase} – {self.fecha}"

    @property
    def expirada(self):
        return timezone.now() > self.expira_en

    @property
    def segundos_restantes(self):
        delta = self.expira_en - timezone.now()
        return max(int(delta.total_seconds()), 0)


# ──────────────────────────────────────────────
#  ASISTENCIA
# ──────────────────────────────────────────────
class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ('presente',    'Presente'),
        ('ausente',     'Ausente'),
        ('justificado', 'Justificado'),
    ]

    estudiante    = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='asistencias'
    )
    clase         = models.ForeignKey(
        Clase, on_delete=models.CASCADE, related_name='asistencias'
    )
    sesion_qr     = models.ForeignKey(
        QRSesion, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='asistencias'
    )
    fecha         = models.DateField(default=timezone.localdate)
    estado        = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='ausente')
    registrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('estudiante', 'clase', 'fecha')
        ordering        = ['-fecha', 'estudiante__usuario__apellido']

    def __str__(self):
        return f"{self.estudiante} – {self.clase} – {self.fecha} – {self.estado}"
