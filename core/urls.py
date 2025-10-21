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
    path('mis-pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    
    # Carrito de compras
    path('carrito/', views.ver_carrito_view, name='ver_carrito'),
    path('carrito/agregar/', views.agregar_al_carrito_view, name='agregar_al_carrito'),
    path('carrito/actualizar/', views.actualizar_cantidad_carrito_view, name='actualizar_carrito'),
    path('carrito/eliminar/', views.eliminar_item_carrito_view, name='eliminar_item_carrito'),
    
    # Admin
    path('admin/productos/', views.admin_productos_lista, name='admin_productos_lista'),
    path('admin/productos/crear/', views.admin_producto_crear, name='admin_producto_crear'),
    path('admin/productos/<int:pk>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('admin/productos/<int:pk>/desactivar/', views.admin_producto_desactivar, name='admin_producto_desactivar'),
    path('admin/pedidos/', views.admin_pedidos_lista_view, name='admin_pedidos_lista'),
    path('admin/pedidos/<int:pk>/', views.admin_pedido_detalle_view, name='admin_pedido_detalle'),
]