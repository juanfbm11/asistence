from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import  login, logout
from django.http import JsonResponse

from GAA.serializers import EstudianteSerializer, ProfesorSerializer, UsuarioSerializer
from rest_framework import viewsets

from personas.models import Usuario, Profesor, Estudiante, Asistencia

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
    return render(request, 'webapplication/codeqr.html')
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

@rol_requerido('estudiante')
def registrar_asistencia(request, sesion_id):
    usuario = request.user
    try:
        estudiante = Estudiante.objects.get(usuario=usuario)
    except Estudiante.DoesNotExist:
        messages.error(request, "No eres un estudiante registrado.")
        return redirect('inicio')

    # Verificar si ya se registró
    ya_registrado = Asistencia.objects.filter(estudiante=estudiante, sesion_id=sesion_id).exists()

    if request.method == 'POST':
        if ya_registrado:
            messages.warning(request, "Ya has registrado tu asistencia para esta sesión.")
        else:
            Asistencia.objects.create(estudiante=estudiante, sesion_id=sesion_id)
            messages.success(request, "Asistencia registrada con éxito.")
        
        return render(request, 'webapplication/asistencia_exitosa.html', {
            'sesion_id': sesion_id,
            'ya_registrado': ya_registrado
        })

    return render(request, 'webapplication/asistencia_exitosa.html', {
        'sesion_id': sesion_id,
        'ya_registrado': ya_registrado
    })

@rol_requerido('profesor', 'administrador')
def obtener_asistencias(request, sesion_id):
    asistencias = Asistencia.objects.filter(sesion_id=sesion_id).select_related('estudiante__usuario')
    data = []
    for asis in asistencias:
        data.append({
            'nombre': f"{asis.estudiante.usuario.nombre} {asis.estudiante.usuario.apellido}",
            'hora': asis.fecha_registro.strftime("%H:%M")
        })
    return JsonResponse({'asistencias': data})
