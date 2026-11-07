from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, JsonResponse
from django.urls import include, path, re_path


def health_check(_request):
    return JsonResponse({"status": "ok"})


def frontend_index(_request):
    index_path = Path(settings.BASE_DIR) / "frontend_dist" / "index.html"
    if not index_path.exists():
        return JsonResponse(
            {
                "erro": (
                    "Frontend não encontrado. Em desenvolvimento, execute "
                    "o Vite separadamente em http://localhost:5173."
                )
            },
            status=404,
        )
    return FileResponse(index_path.open("rb"), content_type="text/html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    path("api/v1/", include("catalogo.urls")),
    path("api/v1/", include("precos.urls")),
    path("api/v1/", include("simulacao.urls")),
    re_path(r"^(?!api/|admin/|health/?$).*$", frontend_index),
]
