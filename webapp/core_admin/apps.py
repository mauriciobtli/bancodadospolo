from django.apps import AppConfig


class CoreAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core_admin"
    verbose_name = "Cadastro do Observatório"

    def ready(self) -> None:
        import core_admin.admin  # noqa: F401  registra os ModelAdmins no AdminSite
