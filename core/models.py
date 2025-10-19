from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
      ROLES = [
            
            ('cliente', 'Cliente'),
            ('administrador', 'Administrador'),
            ('cajero', 'Cajero'),
            ('repatidor', 'Repatidor'),
            ('cocina', 'Cocina'),
            
      ]
      
      telefono = models.CharField(max_length=15, blank=True, null=True )
      direccion = models.TextField(blank=True, null=True)
      rol = models.CharField(max_length=20, blank=True, null=True,choices=ROLES)
      email_verificado = models.BooleanField(default=True)
      fecha_creacion = models.DateTimeField(auto_now_add=True)
      activo = models.BooleanField(default=True)
      
      class Meta:
            verbose_name = 'Usuario'
            verbose_name_plural = 'Usuarios'
            
      def __str__(self):
          return f"{self.username} - {self.get_rol_display()}"
      
class Categoria(models.Model):
      nombre = models.CharField(max_length=100, unique=True)
      descripcion = models.CharField(max_length=500, blank=True, null=True)
      activo = models.BooleanField(default=True)
      fecha_creacion = models.DateField(auto_now_add=True)
      
      class Meta:
            verbose_name = 'Categoría'
            verbose_name_plural = 'Categorías'
            ordering = ['nombre']  # ← Agregué ordenamiento
      def __str__(self):
            return self.nombre
      
class Producto(models.Model):
      nombre = models.CharField(max_length=100, unique=True)
      descripcion = models.CharField(max_length=500, blank=True, null=True)
      precio = models.DecimalField(max_digits=10, decimal_places= 2)
      imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
      stock = models.IntegerField(default=0)
      activo = models.BooleanField(default=True)
      categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='productos')
      fecha_creacion = models.DateField(auto_now_add=True)
      fecha_actualizacion = models.DateField(auto_now=True)
      class Meta:
            verbose_name = 'Producto'
            verbose_name_plural = 'Productos'
            
      def __str__(self):
            return f"{self.nombre} - ${self.precio}"
      
      @property
      def disponible(self):
            """Verifica si el producto está disponible para la venta"""
            return self.activo and self.stock > 0
      
class Repartidor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_repartidor')
    vehiculo = models.CharField(max_length=100, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=20, blank=True, null=True)
    disponible = models.BooleanField(default=True)
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    
    class Meta:
        verbose_name = 'Repartidor'
        verbose_name_plural = 'Repartidores'
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {'Disponible' if self.disponible else 'No disponible'}"