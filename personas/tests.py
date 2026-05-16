from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from personas.models import Asistencia, Clase, Estudiante, Profesor, QRSesion, Usuario


@override_settings(ALLOWED_HOSTS=['testserver', '127.0.0.1'])
class WebApplicationTests(TestCase):
    def crear_usuario(self, email, rol, password='123456', nombre='Usuario', apellido='Prueba'):
        return Usuario.objects.create_user(
            email=email,
            password=password,
            rol=rol,
            nombre=nombre,
            apellido=apellido,
        )

    def setUp(self):
        self.api_client = APIClient()
        self.admin = self.crear_usuario(
            email='admin@test.com',
            rol='administrador',
            nombre='Admin',
        )
        self.profesor_user = self.crear_usuario(
            email='profesor@test.com',
            rol='profesor',
            nombre='Profe',
            apellido='Uno',
        )
        self.profesor = Profesor.objects.create(
            usuario=self.profesor_user,
            colegio='TDEA',
            turno='mañana',
            clases='informatica',
        )
        self.estudiante_user = self.crear_usuario(
            email='estudiante@test.com',
            rol='estudiante',
            nombre='Estudiante',
            apellido='Uno',
        )
        self.estudiante = Estudiante.objects.create(
            usuario=self.estudiante_user,
            colegio='TDEA',
            clases='informatica',
        )

    def test_login_get_carga_pagina(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'webapplication/login.html')

    def test_login_profesor_redirige_a_inicio(self):
        response = self.client.post(reverse('login'), {
            'email': 'profesor@test.com',
            'password': '123456',
            'rol': 'profesor',
        })
        self.assertRedirects(response, reverse('inicio'))

    def test_vista_protegida_redirige_si_no_hay_sesion(self):
        response = self.client.get(reverse('inicio'))
        self.assertRedirects(response, reverse('login'))

    def test_profesor_puede_cargar_vistas_principales(self):
        self.client.force_login(self.profesor_user)

        for url_name in ['inicio', 'clases', 'lista', 'admincrud', 'reportes']:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_codeqr_crea_clase_y_sesion_qr_desde_dato_legacy(self):
        self.client.force_login(self.profesor_user)

        response = self.client.get(reverse('codeqr'))

        self.assertEqual(response.status_code, 200)
        clase = Clase.objects.get(profesor=self.profesor, nombre='informatica')
        self.assertEqual(clase.estudiantes.count(), 1)
        self.assertTrue(QRSesion.objects.filter(clase=clase, activa=True).exists())
        self.assertContains(response, 'informatica')

    def test_estado_qr_devuelve_totales(self):
        self.client.force_login(self.profesor_user)
        clase = Clase.objects.create(
            nombre='informatica',
            codigo='INF-001',
            profesor=self.profesor,
        )
        clase.estudiantes.add(self.estudiante)
        sesion = QRSesion.objects.create(clase=clase)

        response = self.client.get(reverse('estado_qr', args=[sesion.token]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_clase'], 1)
        self.assertEqual(response.json()['total_escaneados'], 0)

    def test_regenerar_qr_desactiva_sesion_anterior(self):
        self.client.force_login(self.profesor_user)
        clase = Clase.objects.create(
            nombre='matematicas',
            codigo='MAT-001',
            profesor=self.profesor,
        )
        sesion_anterior = QRSesion.objects.create(clase=clase)

        response = self.client.post(
            reverse('generar_qr'),
            {'clase_id': clase.id},
            content_type='application/json',
        )

        sesion_anterior.refresh_from_db()
        self.assertEqual(response.status_code, 201)
        self.assertFalse(sesion_anterior.activa)
        self.assertEqual(QRSesion.objects.filter(clase=clase, activa=True).count(), 1)

    def test_estudiante_registra_asistencia_desde_qr(self):
        clase = Clase.objects.create(
            nombre='informatica',
            codigo='INF-002',
            profesor=self.profesor,
        )
        clase.estudiantes.add(self.estudiante)
        sesion = QRSesion.objects.create(clase=clase)
        self.client.force_login(self.estudiante_user)

        response = self.client.post(reverse('registrar_asistencia_qr', args=[sesion.token]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Asistencia.objects.filter(
            estudiante=self.estudiante,
            clase=clase,
            sesion_qr=sesion,
            estado='presente',
        ).exists())

    def test_admin_puede_crear_profesor(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('nuevo_profesor'), {
            'nombre': 'Nuevo',
            'apellido': 'Profesor',
            'email': 'nuevo.profesor@test.com',
            'password': '123456',
            'colegio': 'TDEA',
            'turno': 'tarde',
            'clases': 'historia',
        })

        self.assertRedirects(response, reverse('admincrud'))
        usuario = Usuario.objects.get(email='nuevo.profesor@test.com')
        self.assertEqual(usuario.rol, 'profesor')
        self.assertTrue(Profesor.objects.filter(usuario=usuario, clases='historia').exists())

    def test_api_requiere_autenticacion(self):
        response = self.api_client.get(reverse('usuario-list'))

        self.assertIn(response.status_code, [401, 403])

    def test_api_lista_usuarios_autenticado(self):
        self.api_client.force_authenticate(user=self.admin)

        response = self.api_client.get(reverse('usuario-list'))

        self.assertEqual(response.status_code, 200)
        emails = [usuario['email'] for usuario in response.json()]
        self.assertIn('admin@test.com', emails)
        self.assertIn('profesor@test.com', emails)
        self.assertIn('estudiante@test.com', emails)

    def test_api_crea_profesor_con_perfil(self):
        self.api_client.force_authenticate(user=self.admin)

        response = self.api_client.post(reverse('profesor-list'), {
            'nombre': 'Api',
            'apellido': 'Profesor',
            'email': 'api.profesor@test.com',
            'password': '123456',
            'colegio': 'TDEA',
            'turno': 'tarde',
            'clases': 'fisica',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        usuario = Usuario.objects.get(email='api.profesor@test.com')
        self.assertEqual(usuario.rol, 'profesor')
        self.assertTrue(Profesor.objects.filter(
            usuario=usuario,
            colegio='TDEA',
            turno='tarde',
            clases='fisica',
        ).exists())

    def test_api_crea_estudiante_con_perfil(self):
        self.api_client.force_authenticate(user=self.admin)

        response = self.api_client.post(reverse('estudiante-list'), {
            'nombre': 'Api',
            'apellido': 'Estudiante',
            'email': 'api.estudiante@test.com',
            'password': '123456',
            'colegio': 'TDEA',
            'clases': 'fisica',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        usuario = Usuario.objects.get(email='api.estudiante@test.com')
        self.assertEqual(usuario.rol, 'estudiante')
        self.assertTrue(Estudiante.objects.filter(
            usuario=usuario,
            colegio='TDEA',
            clases='fisica',
        ).exists())

    def test_api_qr_genera_y_consulta_estado(self):
        self.api_client.force_authenticate(user=self.profesor_user)
        self.api_client.force_login(self.profesor_user)
        clase = Clase.objects.create(
            nombre='quimica',
            codigo='QUI-001',
            profesor=self.profesor,
        )
        clase.estudiantes.add(self.estudiante)

        generar_response = self.api_client.post(
            reverse('generar_qr'),
            {'clase_id': clase.id},
            format='json',
        )

        self.assertEqual(generar_response.status_code, 201)
        token = generar_response.json()['token']

        estado_response = self.api_client.get(reverse('estado_qr', args=[token]))

        self.assertEqual(estado_response.status_code, 200)
        estado_data = estado_response.json()
        self.assertEqual(estado_data['total_clase'], 1)
        self.assertEqual(estado_data['total_escaneados'], 0)
        self.assertEqual(estado_data['presentes'], [])
