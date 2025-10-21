from django.urls import path
from . import views

urlpatterns = [
    # Página de inicio
    path('', views.home, name='home'),
    
    # Autenticación
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),
    path('reset/<uidb64>/<token>/', views.reset_password_view, name='reset_password'),

    # Catálogo de productos (público)
    path('productos/', views.catalogo_productos_view, name='catalogo_productos'),

    # Perfil
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    
    # Carrito de compras
    path('carrito/', views.ver_carrito_view, name='ver_carrito'),
    
    # Admin
    path('admin/productos/', views.admin_productos_lista, name='admin_productos_lista'),
    path('admin/productos/crear/', views.admin_producto_crear, name='admin_producto_crear'),
    path('admin/productos/<int:pk>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('admin/productos/<int:pk>/desactivar/', views.admin_producto_desactivar, name='admin_producto_desactivar'),
]