from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
      ROLES = [
            
            ('cliente', 'Cliente'),
            ('administrador', 'Administrador'),
            ('cajero', 'Cajero'),
            ('repartidor', 'Repartidor'),
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
  
  
class Carrito(models.Model):
      usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="carrito")
      fecha_creacion = models.DateTimeField(auto_now_add=True)
      fecha_actualizacion = models.DateTimeField(auto_now=True)
      class Meta:
            verbose_name = 'Carrito'
            verbose_name_plural = 'Carritos'
            
      def __str__(self):
            return f"Carrito de {self.usuario.username}"
      
      @property
      def total_items(self): 
            return sum(item.cantidad for item in self.items.all())
      
      @property
      def total_precio(self):
            return sum(item.subtotal for item in self.items.all())

class ItemCarrito(models.Model):
      carrito = models. ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
      producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
      cantidad = models.PositiveIntegerField(default=1)
      fecha_agregado = models.DateTimeField(auto_now_add=True)

      class Meta:
            verbose_name = 'Item del Carrito'
            verbose_name_plural = 'Items del Carrito'
            unique_together = ['carrito', 'producto']
      def __str__(self):
            return f"{self.cantidad} x {self.producto.nombre}"
      
      @property
      def subtotal(self):
            return self.producto.precio * self.cantidad
      
class MetodoPago(models.Model):
      """Metodos de pagos disponibles"""
      TIPO_CHOICES = [
            ('efectivo', 'Efectivo'),
            ('tarjeta', 'Tarjeta'),
            ('transferencia', 'Transferencia'),
            ('webpay', 'Webpay'),
      ]
      
      nombre = models.CharField(max_length=50)
      tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
      activo = models.BooleanField(default=True)
      
      class Meta:
            verbose_name = 'Método de Pago'
            verbose_name_plural = 'Métodos de Pago'
            
      def __str__(self):
            return self.nombre
      
# Se crea la clase pedido y se le hereda (models.Model) lo que significa que django
# Creará automaticamente la tabla Pedido en la BD para guardar los pedidos      
class Pedido(models.Model):
      
      # Definimos opciones de estado para el pedido
      ESTADO_CHOICES= [
            # El primer valor se almacena BD, el 
            # El segundo valor es el que se muestra forms/admin 
            ('pendiente', 'Pendiente'),
            ('confirmado', 'Confirmado'),
            ('en_preparacion', 'En Preparación'),
            ('listo', 'Listo para Entregar'),
            ('en_camino', 'En Camino'),
            ('entregado', 'Entregado'),
            ('cancelado', 'Cancelado'),
      ]
      
      # Definimos opciones de tipo de orden para el pedido
      TIPO_ORDEN_CHOICES =[
            ('local', 'Para Comer en Local'),
            ('retiro', 'Para Retirar'),
            ('delivery', 'Delivery a Domicilio '),
      ]
      
      #ForeignKey: relación muchos-a-uno.
      # Un pedido pertenece a un Usuario.
      # Si el usuario se elimina (on_delete=models.CASCADE), también se borran sus pedidos.
      # related_name='pedidos' permite acceder desde el usuario a todos sus pedidos:
      # usuario.pedidos.all()
      cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pedidos')
      repartidor = models.ForeignKey(Repartidor, on_delete=models.SET_NULL,null=True)
      metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
      
      numero_pedido = models.CharField(max_length=20,unique=True, editable=True)
      tipo_orden = models.CharField(max_length=20, choices=TIPO_ORDEN_CHOICES,default='local')
      estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
      
      direccion_entrega = models.CharField(max_length=1200,null=True, blank=True)
      referencia_direccion = models.CharField(max_length=200, blank=True, null=True)
      
      subtotal = models.DecimalField(max_digits=10, decimal_places=2)
      costo_envio = models.DecimalField(max_digits=10, decimal_places=2)
      total = models.DecimalField(max_digits=10, decimal_places=2)
      
      notas_cliente = models.TextField(blank=True, null=True)
      notas_cocina = models.TextField(blank=True, null=True)
      
      fecha_creacion = models.DateTimeField(auto_now_add=True)
      fecha_confirmacion = models.DateTimeField(null=True, blank=True)
      fecha_preparacion =models.DateTimeField (null=True, blank=True)
      fecha_listo = models.DateTimeField(null=True, blank=True)
      fecha_entrega = models.DateTimeField(null=True, blank=True)
      
      
    #  verbose_name: nombre legible singular (para el panel admin).

    #  verbose_name_plural: plural del nombre.

    #  ordering: orden por defecto al consultar (-fecha_creacion → más recientes primero).
      
      class Meta:
            verbose_name = 'Pedido'
            verbose_name_plural = 'Pedidos'
            ordering = ['-fecha_creacion']
            
      def __str__(self):
            return f"#{self.numero_pedido} - Pedido de {self.cliente.username}"
      
      def save(self, *args, **kwargs):
            if not self.numero_pedido:
                  import random
                  import string
                  
                  self.numero_pedido = ''.join(random.choices(string.digits, k=8))
            super().save(*args, **kwargs)
            
class DetallePedido(models.Model):
      pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
      producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
      cantidad = models.PositiveIntegerField()
      precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
      subtotal = models.DecimalField(max_digits=10, decimal_places=2)
      
      class Meta:
            verbose_name = 'Detalle del Pedido'
            verbose_name_plural = 'Detalles del Pedido'
      def __str__(self):
            return f"{self.cantidad}x {self.producto.nombre} - {self.pedido.numero_pedido}"
      def save(self, *args, **kwargs):
            self.subtotal = self.precio_unitario * self.cantidad
            super().save(*args, **kwargs)
      
      
class Reclamo(models.Model):
      MOTIVO_CHOICES = [
            ('pedido_incorrecto', 'Pedido Incorrecto'),
            ('producto_danado', 'Producto Dañado'),
            ('demora_excesiva', 'Demora Excesiva'),
            ('mala_atencion', 'Mala Atención'),
            ('otro', 'Otro'),
      ]
      
      ESTADO_CHOICES = [
            ('nuevo', 'Nuevo'),
            ('en_revision', 'En Revisión'),
            ('respondido', 'Respondido'),
            ('resuelto', 'Resuelto'),
            ('cerrado', 'Cerrado'),
      ]
      
      cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE)
      pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
      
      motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES,)
      descripcion = models.TextField()
      estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='nuevo')
      
      respuesta = models.TextField(blank=True, null=True)
      atendido_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamos_atendidos')
      
      fecha_creacion = models.DateTimeField(auto_now_add=True)
      fecha_respuesta = models.DateTimeField(null=True, blank=True)
      
      class Meta:
            verbose_name = 'Reclamo'
            verbose_name_plural = 'Reclamos'
            ordering = ['-fecha_creacion']
            
      def __str__(self):
            return f"#{self.id} Reclamo - {self.cliente.username}"