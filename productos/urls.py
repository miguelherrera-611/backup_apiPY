from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para API REST
router = DefaultRouter()
router.register(r'productos', views.ProductoViewSet)
router.register(r'categorias', views.CategoriaViewSet)

urlpatterns = [
    # Páginas web
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),  # NUEVA RUTA
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil_view, name='perfil'),  # NUEVA RUTA
    path('logout/', views.logout_view, name='logout'),

    # AJAX para admin
    path('ajax/crear-producto/', views.crear_producto, name='crear_producto'),
    path('ajax/eliminar-producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),

    # AJAX para perfil de usuario - NUEVAS RUTAS
    path('ajax/actualizar-perfil/', views.actualizar_perfil, name='actualizar_perfil'),
    path('ajax/cambiar-password/', views.cambiar_password, name='cambiar_password'),

    # Carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('ajax/carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('ajax/carrito/actualizar/<int:item_id>/', views.actualizar_item_carrito, name='actualizar_item_carrito'),
    path('ajax/carrito/eliminar/<int:item_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('ajax/carrito/limpiar/', views.limpiar_carrito, name='limpiar_carrito'),

    # API REST
    path('api/', include(router.urls)),
    path('api/mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('api/carrito-info/', views.carrito_info, name='carrito_info'),
    path('api/estadisticas/', views.estadisticas_publicas, name='estadisticas_publicas'),
    path('api-auth/', include('rest_framework.urls')),
]