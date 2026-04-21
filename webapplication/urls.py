"""
URL configuration for webapplication project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Autenticación ──
    path('',        views.login_view,  name='login'),    # / → login
    path('logout/', views.logout_view, name='logout'),
    path('sin-permiso/', views.sin_permiso, name='sin_permiso'),

    # ── Profesor
    path('inicio/',   views.inicio,    name='inicio'),
    path('clases/',   views.clases,    name='clases'),
    path('lista/',    views.lista,     name='lista'),
    path('codeqr/',   views.codeqr,    name='codeqr'),
    path('reportes/', views.reportes,  name='reportes'),

    # ── Administrador ──
    path('admincrud/', views.admincrud, name='admincrud'),
    # crear
    path('admincrud/admin/nuevo/', views.nuevo_admin, name='nuevo_admin'),
    path('nuevo-profesor/', views.nuevo_profesor, name='nuevo_profesor'),
    path('nuevo-estudiante/', views.nuevo_estudiante, name='nuevo_estudiante'),
    # editar
    path('admincrud/admin/<int:pk>/editar/', views.editar_admin, name='editar_admin'),
    path('profesor/<int:id>/editar/', views.editar_profesor, name='editar_profesor'),
    path('estudiante/<int:id>/editar/', views.editar_estudiante, name='editar_estudiante'),

    # eliminar
    path('admincrud/admin/<int:pk>/eliminar/', views.eliminar_admin, name='eliminar_admin'),
    path('profesor/<int:id>/eliminar/', views.eliminar_profesor, name='eliminar_profesor'),
    path('estudiante/<int:id>/eliminar/', views.eliminar_estudiante, name='eliminar_estudiante'),
]
