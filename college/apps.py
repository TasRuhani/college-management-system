from django.apps import AppConfig

class CollegeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'college'

    # Add this method to connect the signals when the app is ready
    def ready(self):
        import college.signals