from django.apps import AppConfig


class PersonasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personas'

    def ready(self):
        # import personas.signals  # noqa: F401
        pass
