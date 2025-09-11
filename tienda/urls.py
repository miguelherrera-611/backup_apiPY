from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Personalización del admin por defecto
admin.site.site_header = "🎮 GAMERLY Administration"
admin.site.site_title = "GAMERLY Admin"
admin.site.index_title = "Panel de Control Gaming"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('productos.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)