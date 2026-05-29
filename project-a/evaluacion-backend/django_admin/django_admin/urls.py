from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path

def healthz(request):
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "error"}, status=503)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', healthz),
]
