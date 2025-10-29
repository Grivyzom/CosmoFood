from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Repartidor, Producto, Categoria, Carrito, ItemCarrito, MetodoPago, Pedido, DetallePedido, Reclamo, Slide

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'rol', 'telefono', 'activo', 'fecha_creacion']
    list_filter = ['rol', 'activo', 'email_verificado']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('telefono', 'direccion', 'rol', 'email_verificado', 'activo')}),
    )
      

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
      list_display = ['nombre', 'activo', 'fecha_creacion']
      list_filter = ['activo']
      search_fields = ['nombre']
      
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
      list_display = ['nombre', 'descripcion', 'precio','stock', 'activo', 'en_promocion', 'disponible']
      list_filter = ['categoria', 'activo', 'en_promocion']
      search_fields = ['nombre', 'descripcion']
      list_editable = ['precio', 'stock', 'activo', 'en_promocion']
      
@admin.register(Repartidor)
class RepatidorAdmin(admin.ModelAdmin):
      list_display = ['usuario', 'vehiculo', 'disponible', 'calificacion_promedio']
      list_filter = ['disponible']
      search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name']
      
@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'total_items', 'total_precio', 'fecha_actualizacion']
    search_fields = ['usuario__username']

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
      list_display = ['carrito', 'producto', 'cantidad', 'subtotal']
      list_filter = ['fecha_agregado']
      
@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
      list_display = ['nombre', 'tipo', 'activo']
      list_filter = ['tipo', 'activo']



@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
      list_display = ['numero_pedido','cliente', 'tipo_orden', 'estado']
      list_filter = ['estado', 'tipo_orden', 'fecha_creacion']
      search_fields = ['numero_pedido', 'cliente__username']
      readonly_fields= ['numero_pedido']
      
@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
      
@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
      list_display = ['id', 'cliente', 'pedido', 'motivo', 'estado', 'fecha_creacion']
      list_filter = ['estado', 'motivo', 'fecha_creacion']
      search_fields = ['cliente__username', 'pedido__numero_pedido']

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
      list_display = ['id', 'titulo', 'orden', 'activo']
      list_filter = ['activo']
      search_fields = ['titulo', 'subtitulo']
      list_editable = ['orden', 'activo']
      ordering = ['orden']