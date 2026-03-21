from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from personas.models import Usuario, Profesor, Estudiante

# ── LOGIN ──────────────────────────────────────────────────────────────
@login_required
def admincrud(request):
    if request.user.rol != 'administrador':
        return redirect('login')

    personas = Usuario.objects.all()
    return render(request, 'webapplication/admincrud.html', {'personas': personas})



def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        rol = request.POST['rol']

        Usuario = authenticate(request, username=email, password=password)

        if Usuario is None:
            messages.error(request, 'email o Contraseña Incorrectos')
            return render(request, 'webapplication/login.html')

        if Usuario.rol != rol:
            messages.warning(request, f'Este correo corresponde al rol de {Usuario.rol}.')
            return render(request, 'webapplication/login.html')

        login(request, Usuario)

        if Usuario.rol == 'administrador':
            return redirect('/admincrud/')
        elif Usuario.rol == 'profesor':
            return redirect('/inicio/')
        else:
            return redirect('alumno_inicio')

    return render(request, 'webapplication/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# ── VISTAS PROFESOR / ALUMNO ───────────────────────────────────────────

def inicio(request):
    return render(request, 'webapplication/inicio.html')

def clases(request):
    return render(request, 'webapplication/clases.html')

def lista(request):
    return render(request, 'webapplication/lista.html')

def codeqr(request):
    return render(request, 'webapplication/codeqr.html')

def reportes(request):
    return render(request, 'webapplication/reportes.html')


# ── VISTA ADMINISTRADOR ────────────────────────────────────────────────
def admincrud(request, ):
    personas = Usuario.objects.all()
    return render(request, 'webapplication/admincrud.html', {'personas':personas})


def nuevo_admin(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email:
            messages.error(request, 'El email es obligatorio.')
            return redirect('admincrud')

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe un usuario con ese email.')
            return redirect('admincrud')




        Usuario.objects.create(
            email=email,
            password=password,
            rol='administrador',
            nombre=nombre,
            apellido=apellido
        )
        messages.success(request, f'Administrador {nombre} {apellido} creado.')
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