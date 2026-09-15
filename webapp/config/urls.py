from django.urls import include, path

from core_admin.admin_site import site

urlpatterns = [
    path("importacao/", include("importacao.urls")),
    path("", site.urls),
]
