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
    
    # Dashboard principal del admin
    path('panel/', views.admin_dashboard_view, name='admin_dashboard'),

    # Gestión de Productos (CRUD)
    path('panel/productos/', views.admin_productos_lista, name='admin_productos_lista'),
    path('panel/productos/crear/', views.admin_producto_crear, name='admin_producto_crear'),
    path('panel/productos/<int:pk>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('panel/productos/<int:pk>/desactivar/', views.admin_producto_desactivar, name='admin_producto_desactivar'),

    # Gestión de Pedidos
    path('panel/pedidos/', views.admin_pedidos_lista_view, name='admin_pedidos_lista'),
    path('panel/pedidos/<int:pk>/', views.admin_pedido_detalle_view, name='admin_pedido_detalle'),
    
    # Punto de Venta (POS)
    path('panel/pos/', views.pos_view, name='pos_view'),
    
    # Gestión de Reclamos
    path('panel/reclamos/', views.admin_reclamos_lista, name='admin_reclamos_lista'),
    path('panel/reclamos/<int:pk_reclamo>/', views.admin_reclamo_detalle, name='admin_reclamo_detalle'),
    
    # Gestión de Repartidores
    path('panel/repartidores/', views.admin_repartidores_lista, name='admin_repartidores_lista'), 
    path('panel/repartidores/crear/', views.admin_repartidor_crear, name='admin_repartidor_crear'), 
    path('panel/repartidores/<int:pk_usuario>/editar/', views.admin_repartidor_editar, name='admin_repartidor_editar'), 
    path('panel/repartidores/<int:pk_usuario>/toggle/', views.admin_repartidor_toggle_disponible, name='admin_repartidor_toggle'),
    
    # Vista del Repartidor (HU18)
    path('repartidor/pedidos/', views.repartidor_pedidos_view, name='repartidor_pedidos'),
    
    # Búsqueda de Pedido (AJAX)
    path('panel/buscar-pedido/', views.buscar_pedido_view, name='buscar_pedido'),
]