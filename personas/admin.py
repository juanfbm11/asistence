from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from personas.models import Estudiante, Profesor, Usuario


class UsuarioCreationAdminForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'rol')


class UsuarioChangeAdminForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = '__all__'


class ProfesorInline(admin.StackedInline):
    model = Profesor
    extra = 0
    can_delete = False


class EstudianteInline(admin.StackedInline):
    model = Estudiante
    extra = 0
    can_delete = False


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeAdminForm
    add_form = UsuarioCreationAdminForm
    model = Usuario
    ordering = ('email',)
    search_fields = ('email', 'nombre', 'apellido')
    list_display = ('email', 'nombre', 'apellido', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active', 'groups')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informacion personal', {'fields': ('nombre', 'apellido', 'rol')}),
        (
            'Permisos',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'nombre',
                    'apellido',
                    'rol',
                    'password1',
                    'password2',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )
    filter_horizontal = ('groups', 'user_permissions')

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        if obj.rol == 'profesor':
            return [ProfesorInline(self.model, self.admin_site)]
        if obj.rol == 'estudiante':
            return [EstudianteInline(self.model, self.admin_site)]
        return []


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'colegio', 'turno', 'clases')
    search_fields = ('usuario__email', 'usuario__nombre', 'usuario__apellido', 'colegio', 'clases')


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'colegio', 'clases')
    search_fields = ('usuario__email', 'usuario__nombre', 'usuario__apellido', 'colegio', 'clases')
