from django.urls import include, path
from . import views
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from webapplication.views import EstudianteViewSet, ProfesorViewSet, UsuarioViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'profesores', ProfesorViewSet, basename='profesor')
router.register(r'estudiantes', EstudianteViewSet, basename='estudiante')

urlpatterns = [
    # ── Autenticación ──
    path('api/', include(router.urls)),
    path('',        views.login_view,  name='login'),    # / → login
    path('logout/', views.logout_view, name='logout'),
    path('sin-permiso/', views.sin_permiso, name='sin_permiso'),

    # ── Profesor
    path('inicio/',   views.inicio,    name='inicio'),
    path('clases/',   views.clases,    name='clases'),
    path('lista/',    views.lista,     name='lista'),
    path('codeqr/',   views.codeqr,    name='codeqr'),
    path('reportes/', views.reportes,  name='reportes'),
    path('api/qr/generar/', views.generar_qr, name='generar_qr'),
    path('api/qr/<uuid:token>/estado/', views.estado_qr, name='estado_qr'),
    path('asistencia/registrar/', views.registrar_asistencia_qr, name='registrar_asistencia_qr'),
    path('asistencia/registrar/<uuid:token>/', views.registrar_asistencia_qr, name='registrar_asistencia_qr_token'),

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


    path('api/auth/token/', obtain_auth_token),
     path('reportes/exportar/', views.exportar_pdf,name='exportar_pdf'),
]

