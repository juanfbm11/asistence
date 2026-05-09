from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import  login, logout
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from GAA.serializers import EstudianteSerializer, ProfesorSerializer, UsuarioSerializer
from rest_framework import viewsets

from personas.models import Usuario, Profesor, Estudiante, Clase, QRSesion, Asistencia

from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        rol = request.POST['rol']

        print("Correo recibido:", email)
        print("Existe:", Usuario.objects.filter(email=email).exists())

        try:
            usuario = Usuario.objects.get(email=email)
            if not usuario.check_password(password):
                usuario = None
        except Usuario.DoesNotExist:
            usuario = None

        print("Usuario:", usuario)
        print("Rol:", usuario.rol if usuario else None)

        if usuario is None:
            messages.error(request, 'Email o contraseña incorrectos.')
            return render(request, 'webapplication/login.html')

        if usuario.rol != rol:
            messages.warning(request, f'Este email corresponde al rol de {usuario.rol}.')
            return render(request, 'webapplication/login.html')

        login(request, usuario)

        if usuario.rol == 'administrador':
            return redirect('admincrud')
        elif usuario.rol == 'profesor':
            return redirect('inicio')
        else:
            return redirect('inicio')

    return render(request, 'webapplication/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# ── VISTAS ──

def rol_requerido(*roles_permitidos):
    def decorator(vista):
        @wraps(vista)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.rol not in roles_permitidos:
                return redirect('sin_permiso')  # ← redirige a página de error
            return vista(request, *args, **kwargs)
        return wrapper
    return decorator

def sin_permiso(request):
    return render(request, 'webapplication/sin_permiso.html')


def asegurar_clase_desde_perfil(profesor):
    if not profesor or not profesor.clases:
        return None

    nombre = profesor.clases.strip()
    if not nombre:
        return None

    codigo_base = slugify(nombre).upper()[:20] or 'CLASE'
    codigo = f"P{profesor.id}-{codigo_base}"[:30]
    clase, _ = Clase.objects.get_or_create(
        profesor=profesor,
        nombre__iexact=nombre,
        defaults={
            'nombre': nombre,
            'codigo': codigo,
            'aula': profesor.colegio or '',
        },
    )

    estudiantes = Estudiante.objects.filter(clases__iexact=nombre)
    if estudiantes.exists():
        clase.estudiantes.add(*estudiantes)

    return clase


@rol_requerido('administrador', 'profesor')
def admincrud(request):
    admin = Usuario.objects.filter(rol='administrador')
    profesores = Usuario.objects.filter(rol='profesor')
    estudiantes = Usuario.objects.filter(rol='estudiante')
    es_administrador = request.user.rol == 'administrador'
    es_profesor = request.user.rol == 'profesor'

    return render(request, 'webapplication/admincrud.html', {
        'admin': admin,
        'profesores': profesores,
        'estudiantes': estudiantes,
        'es_administrador': es_administrador,
        'es_profesor': es_profesor,
    })


@rol_requerido('profesor', 'estudiante', 'administrador')
def inicio(request):
    usuario = request.user
    perfil = None

    if usuario.rol == 'profesor':
        perfil = Profesor.objects.filter(usuario=usuario).first()

    elif usuario.rol == 'estudiante':
        perfil = Estudiante.objects.filter(usuario=usuario).first()

    return render(request, 'webapplication/inicio.html', {
        'usuario': usuario,
        'perfil': perfil
    })

@rol_requerido('profesor', 'estudiante', 'administrador')
def clases(request):
    usuario = request.user
    perfil = None

    if usuario.rol == 'profesor':
        perfil = Profesor.objects.filter(usuario=usuario).first()

    elif usuario.rol == 'estudiante':
        perfil = Estudiante.objects.filter(usuario=usuario).first()

    return render(request, 'webapplication/clases.html', {
        'usuario': usuario,
        'perfil': perfil
    })

@rol_requerido('profesor', 'estudiante', 'administrador')
def lista(request):
    usuario = request.user
    perfil = None
    estudiantes = []

    if usuario.rol == 'profesor':
        perfil = Profesor.objects.filter(usuario=usuario).first()
        estudiantes = Estudiante.objects.all()

    elif usuario.rol == 'estudiante':
        perfil = Estudiante.objects.filter(usuario=usuario).first()
        estudiantes = [perfil]

    return render(request, 'webapplication/lista.html', {
        'usuario': usuario,
        'perfil': perfil,
        'estudiantes': estudiantes
    })

@rol_requerido('profesor', 'estudiante', 'administrador')
def codeqr(request):
    usuario = request.user

    if usuario.rol == 'profesor':
        perfil = Profesor.objects.filter(usuario=usuario).first()
        asegurar_clase_desde_perfil(perfil)
        mis_clases = Clase.objects.filter(profesor=perfil, activa=True) if perfil else Clase.objects.none()
    elif usuario.rol == 'estudiante':
        perfil = Estudiante.objects.filter(usuario=usuario).first()
        mis_clases = perfil.mis_clases.filter(activa=True) if perfil else Clase.objects.none()
    else:
        mis_clases = Clase.objects.filter(activa=True)

    clase_id = request.GET.get('clase_id')
    clase = mis_clases.filter(id=clase_id).first() if clase_id else mis_clases.first()

    context = {
        'mis_clases': mis_clases,
        'clase': clase,
        'total_alumnos': 0,
    }

    if clase:
        sesion = clase.sesiones_qr.filter(activa=True, expira_en__gt=timezone.now()).first()
        if not sesion:
            sesion = QRSesion.objects.create(clase=clase)

        qr_url = request.build_absolute_uri(
            reverse('registrar_asistencia_qr', args=[str(sesion.token)])
        )
        context.update({
            'sesion': sesion,
            'sesion_token': str(sesion.token),
            'qr_url': qr_url,
            'expira_en_iso': sesion.expira_en.isoformat(),
            'segundos_restantes': sesion.segundos_restantes,
            'total_alumnos': clase.total_estudiantes(),
        })

    return render(request, 'webapplication/codeqr.html', context)

@rol_requerido('profesor', 'estudiante', 'administrador')
@api_view(['POST'] )
@permission_classes([IsAuthenticated])
def generar_qr(request):
    clase = get_object_or_404(Clase, pk=request.data.get('clase_id'))

    if request.user.rol == 'profesor':
        profesor = Profesor.objects.filter(usuario=request.user).first()
        if clase.profesor_id != getattr(profesor, 'id', None):
            return Response({'detail': 'No tienes permiso para esta clase.'}, status=status.HTTP_403_FORBIDDEN)
    elif request.user.rol != 'administrador':
        return Response({'detail': 'No tienes permiso para generar QR.'}, status=status.HTTP_403_FORBIDDEN)

    clase.sesiones_qr.filter(activa=True).update(activa=False)
    sesion = QRSesion.objects.create(clase=clase)
    return Response({
        'token': str(sesion.token),
        'expira_en': sesion.expira_en.isoformat(),
    }, status=status.HTTP_201_CREATED)

@rol_requerido('profesor', 'estudiante', 'administrador')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_qr(request, token):
    sesion = get_object_or_404(QRSesion.objects.select_related('clase'), token=token)
    asistencias = sesion.asistencias.filter(estado='presente').select_related('estudiante__usuario')
    presentes = [
        {
            'nombre': asistencia.estudiante.usuario.nombre,
            'apellido': asistencia.estudiante.usuario.apellido,
            'email': asistencia.estudiante.usuario.email,
        }
        for asistencia in asistencias
    ]

    return Response({
        'expirada': sesion.expirada,
        'total_escaneados': len(presentes),
        'total_clase': sesion.clase.total_estudiantes(),
        'presentes': presentes,
    })


@rol_requerido('estudiante')
def registrar_asistencia_qr(request, token):
    sesion = get_object_or_404(QRSesion.objects.select_related('clase'), token=token)
    estudiante = get_object_or_404(Estudiante, usuario=request.user)
    ya_registrado = Asistencia.objects.filter(
        estudiante=estudiante,
        clase=sesion.clase,
        fecha=timezone.localdate(),
    ).exists()

    if request.method == 'POST' and not ya_registrado and not sesion.expirada:
        Asistencia.objects.create(
            estudiante=estudiante,
            clase=sesion.clase,
            sesion_qr=sesion,
            estado='presente',
        )
        ya_registrado = True

    return render(request, 'webapplication/asistencia_exitosa.html', {
        'sesion_id': str(sesion.token),
        'ya_registrado': ya_registrado,
        'sesion_expirada': sesion.expirada,
    })


@rol_requerido('profesor', 'administrador')
def reportes(request):
    return render(request, 'webapplication/reportes.html')


# ── VISTA ADMINISTRADOR ────────────────────────────────────────────────
@rol_requerido('administrador')
def nuevo_admin(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email:
            messages.error(request, 'El email es obligatorio.')
            return redirect('admincrud')

        if not password:
            messages.error(request, "La contraseña es obligatoria")
            return redirect('admincrud')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe un usuario con ese email.')
            return redirect('admincrud')

        Usuario.objects.create_user(
            email=email,
            password=password,
            rol='administrador',
            nombre=nombre,
            apellido=apellido,
        )
        messages.success(request, f'administrador {nombre} {apellido} creado.')
        return redirect('admincrud')

    return redirect('admincrud')


@rol_requerido('administrador')
def editar_admin(request, pk):
    admin = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        admin.nombre = request.POST.get('nombre', admin.nombre)
        admin.apellido = request.POST.get('apellido', admin.apellido)
        email = request.POST.get('email')
        if email:
            admin.email = email


        admin.save()
        messages.success(request, 'administrador actualizado.')
    return redirect('admincrud')


@rol_requerido('administrador')
def eliminar_admin(request, pk):
    admin = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        admin.delete()
        messages.success(request, 'administrador eliminado.')
    return redirect('admincrud')

@rol_requerido('administrador', 'profesor')
def nuevo_estudiante(request):
    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        if not password:
            messages.error(request, "La contraseña es obligatoria")
            return redirect('admincrud')


        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario con ese email")
            return redirect('admincrud')
        # Crear usuario base
        usuario = Usuario.objects.create_user(
            email=email,
            password=password,
            nombre=request.POST.get('nombre'),
            apellido=request.POST.get('apellido'),
            rol='estudiante'
        )

        # Crear o actualizar perfil estudiante
        estudiante, _ = Estudiante.objects.get_or_create(usuario=usuario)
        estudiante.colegio = request.POST.get('colegio')
        estudiante.clases = request.POST.get('clases')
        estudiante.save()

        messages.success(request, 'Estudiante creado correctamente')
    return redirect('admincrud')

@rol_requerido('administrador', 'profesor')
def editar_estudiante(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    estudiante, _ = Estudiante.objects.get_or_create(usuario=usuario)

    if request.method == 'POST':
        # Usuario
        usuario.nombre = request.POST.get('nombre')
        usuario.apellido = request.POST.get('apellido')
        usuario.email = request.POST.get('email')
        usuario.save()

        # Perfil estudiante
        estudiante.colegio = request.POST.get('colegio')
        estudiante.clases = request.POST.get('clases')
        estudiante.save()

        messages.success(request, 'Estudiante actualizado correctamente')

    return redirect('admincrud')

@rol_requerido('administrador')
def eliminar_estudiante(request, id):
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == 'POST':
        usuario.delete()  # elimina también Estudiante (CASCADE)
        messages.success(request, 'Estudiante eliminado')

    return redirect('admincrud')


@rol_requerido('administrador', 'profesor')
def nuevo_profesor(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        password = request.POST.get('password')

        if not password:   # ← AQUÍ
            messages.error(request, "La contraseña es obligatoria")
            return redirect('admincrud')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario con ese email")
            return redirect('admincrud')

        usuario = Usuario.objects.create_user(
            email=email,
            password=password,
            nombre=request.POST.get('nombre'),
            apellido=request.POST.get('apellido'),
            rol='profesor'
        )

        profesor, _ = Profesor.objects.get_or_create(usuario=usuario)
        profesor.colegio = request.POST.get('colegio')
        profesor.turno = request.POST.get('turno')
        profesor.clases = request.POST.get('clases')
        profesor.save()

        messages.success(request, 'Profesor creado correctamente')

    return redirect('admincrud')

@rol_requerido('administrador', 'profesor')
def editar_profesor(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    profesor, _ = Profesor.objects.get_or_create(usuario=usuario)


    if request.method == 'POST':
        # Usuario
        usuario.nombre = request.POST.get('nombre')
        usuario.apellido = request.POST.get('apellido')
        usuario.email = request.POST.get('email')
        usuario.save()

        # Perfil profesor
        profesor.colegio = request.POST.get('colegio')
        profesor.turno = request.POST.get('turno')
        profesor.clases = request.POST.get('clases')
        profesor.save()

        messages.success(request, 'Profesor actualizado correctamente')

    return redirect('admincrud')

@rol_requerido('administrador')
def eliminar_profesor(request, id):
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == 'POST':
        usuario.delete()  # CASCADE elimina profesor
        messages.success(request, 'Profesor eliminado')

    return redirect('admincrud')


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by('rol', 'nombre', 'apellido', 'id')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]


class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.select_related('usuario').all().order_by(
        'usuario__nombre',
        'usuario__apellido',
        'id',
    )
    serializer_class = ProfesorSerializer
    permission_classes = [IsAuthenticated]


class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.select_related('usuario').all().order_by(
        'usuario__nombre',
        'usuario__apellido',
        'id',
    )
    serializer_class = EstudianteSerializer
    permission_classes = [IsAuthenticated]
