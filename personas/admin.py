from django.contrib import admin


from personas.models import Estudiante, Usuario , Profesor

admin.site.register(Estudiante)
admin.site.register(Profesor)
admin.site.register(Usuario)
