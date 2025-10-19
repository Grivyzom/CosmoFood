from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Repartidor, Producto, Categoria

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
      list_display = ['nombre', 'descripcion', 'precio','stock', 'activo', 'disponible']
      list_filter = ['categoria', 'activo']
      search_fields = ['nombre', 'descripcion']
      list_editable = ['precio', 'stock', 'activo']
      
@admin.register(Repartidor)
class RepatidorAdmin(admin.ModelAdmin):
      list_display = ['usuario', 'vehiculo', 'disponible', 'calificacion_promedio']
      list_filter = ['disponible']
      search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name']