from functools import wraps
from urllib import request

from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from personas.models import Usuario, Profesor, Estudiante




def admincrud(request):
    admin = Usuario.objects.filter(rol='Administracion').update(rol='administrador')
    profesores = Usuario.objects.filter(rol='profesor')
    estudiantes = Usuario.objects.filter(rol='estudiante')

    return render(request, 'webapplication/admincrud.html', {
        'admin': admin,
        'profesores': profesores,
        'estudiantes': estudiantes
    })

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        rol = request.POST['rol']

        print("Correo recibido:", email)
        print("Existe:", Usuario.objects.filter(email=email).exists())

        usuario = authenticate(request, username=email, password=password)

        print("Usuario:", usuario)
        print("Rol:", usuario.rol if usuario else None)

        if usuario is None:
            messages.error(request, 'email o Contraseña Incorrectos')
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
            return redirect('alumno_inicio')

    return render(request, 'webapplication/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# ── VISTAS PROFESOR ──

def solo_profesor(vista):
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.rol not in ['profesor', 'administrador']:
            return HttpResponseForbidden('No tienes permiso para acceder aquí.')

        return vista(request, *args, **kwargs)
    return wrapper

@solo_profesor
def inicio(request):
    return render(request, 'webapplication/inicio.html')
@solo_profesor
def clases(request):
    return render(request, 'webapplication/clases.html')
@solo_profesor
def lista(request):
    return render(request, 'webapplication/lista.html')
@solo_profesor
def codeqr(request):
    return render(request, 'webapplication/codeqr.html')
@solo_profesor
def reportes(request):
    return render(request, 'webapplication/reportes.html')


# ── VISTA ADMINISTRADOR ────────────────────────────────────────────────
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




        usuario = Usuario.objects.create_user(
            email=email,
            password=password,
            rol='administrador',
            nombre=nombre,
            apellido=apellido,
        )
        messages.success(request, f'Administrador {nombre} {apellido} creado.')
        grupo_admin = Group.objects.get(name='Administracion')
        usuario.groups.add(grupo_admin)
        return redirect('admincrud')


def editar_admin(request, pk):
    admin = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        admin.nombre = request.POST.get('nombre', admin.nombre)
        admin.apellido = request.POST.get('apellido', admin.apellido)
        email = request.POST.get('email')
        if email:
            admin.email = email


        admin.save()
        messages.success(request, 'Administrador actualizado.')
    return redirect('admincrud')


def eliminar_admin(request, pk):
    admin = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        admin.delete()
        messages.success(request, 'Administrador eliminado.')
    return redirect('admincrud')

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

        # Crear perfil estudiante
        Estudiante.objects.create(
            usuario=usuario,
            colegio=request.POST.get('colegio'),
            clases=request.POST.get('clases')
        )

        messages.success(request, 'Estudiante creado correctamente')
        grupo_estudiante = Group.objects.get(name='Estudiantes')
        usuario.groups.add(grupo_estudiante)
    return redirect('admincrud')

def editar_estudiante(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    estudiante = get_object_or_404(Estudiante, usuario=usuario)

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

def eliminar_estudiante(request, id):
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == 'POST':
        usuario.delete()  # elimina también Estudiante (CASCADE)
        messages.success(request, 'Estudiante eliminado')

    return redirect('admincrud')


def nuevo_profesor(request):
    if request.method == 'POST':

        password = request.POST.get('password')

        if not password:   # ← AQUÍ
            messages.error(request, "La contraseña es obligatoria")
            return redirect('admincrud')

        usuario = Usuario.objects.create_user(
            email=request.POST.get('email'),
            password=password,
            nombre=request.POST.get('nombre'),
            apellido=request.POST.get('apellido'),
            rol='profesor'
        )
        grupo_profesor = Group.objects.get(name='Profesor')
        usuario.groups.add(grupo_profesor)

        Profesor.objects.create(
            usuario=usuario,
            colegio=request.POST.get('colegio'),
            turno=request.POST.get('turno'),
            clases=request.POST.get('clases')
        )

        messages.success(request, 'Profesor creado correctamente')

    return redirect('admincrud')

def editar_profesor(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    profesor = get_object_or_404(Profesor, usuario=usuario)

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

def eliminar_profesor(request, id):
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == 'POST':
        usuario.delete()  # CASCADE elimina profesor
        messages.success(request, 'Profesor eliminado')

    return redirect('admincrud')





def solo_estudiante(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.rol not in ['estudiante', 'profesor', 'administrador']:
            return HttpResponseForbidden('No tienes permiso para acceder aquí.')
        return view_func(request, *args, **kwargs)
    return wrapper