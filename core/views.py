from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib import messages
from django.db import models
from .forms import ( 
    RegistroForm, LoginForm, PerfilForm, ProductoForm, 
    RecuperarPasswordForm, ResetPasswordForm
)
from .models import Carrito, Producto, Usuario, Categoria, ItemCarrito, Pedido, Slide
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site

# Vista de inicio (landing page)
def home(request):
    slides = Slide.objects.filter(activo=True).order_by('orden')
    contexto = {
        'slides': slides
    }
    return render(request, 'core/home.html', contexto)

# ========== CATÁLOGO DE PRODUCTOS (CLIENTE) ==========

def catalogo_productos_view(request):
    """Vista para que los clientes y visitantes vean el catálogo de productos (HU10)"""
    
    # Inicialmente no mostramos productos (solo categorías)
    productos = Producto.objects.none()
    
    # Búsqueda
    busqueda = request.GET.get('q', '')
    
    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    
    # Ver todo
    ver_todo = request.GET.get('ver_todo')
    
    # Solo mostramos productos si hay algún filtro activo
    if busqueda or categoria_id or ver_todo:
        productos = Producto.objects.filter(activo=True, stock__gt=0).select_related('categoria').order_by('nombre')
        
        if busqueda:
            productos = productos.filter(nombre__icontains=busqueda)
        
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
    
    contexto = {
        'productos': productos,
        'categorias': Categoria.objects.filter(activo=True),
        'busqueda': busqueda,
        'categoria_seleccionada': categoria_id
    }
    return render(request, 'core/catalogo_productos.html', contexto)

# ========== AUTENTICACIÓN ==========

def registro_view(request):
    """Vista de registro de usuarios (HU05)"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Crear carrito automáticamente para el nuevo usuario
            Carrito.objects.create(usuario=user)
            
            # Iniciar sesión automáticamente después del registro
            login(request, user)
            
            messages.success(request, f'¡Bienvenido {user.first_name}! Tu cuenta ha sido creada exitosamente.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    
    return render(request, 'core/registro.html', {'form': form})


def login_view(request):
    """Vista de inicio de sesión (HU06)"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
                
                # Redirigir según el rol del usuario
                if user.rol == 'administrador':
                    return redirect('admin:index')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('home')

def recuperar_password_view(request):
    """Vista para solicitar recuperación de contraseña (HU07)"""
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                usuario = Usuario.objects.get(email=email)
                
                # Generar token
                token = default_token_generator.make_token(usuario)
                uid = urlsafe_base64_encode(force_bytes(usuario.pk))
                
                # Construir URL de reset
                current_site = get_current_site(request)
                reset_url = f"http://{current_site.domain}/reset/{uid}/{token}/"
                
                # Enviar email
                mensaje = f"""
                            Hola {usuario.first_name},

                            Recibimos una solicitud para restablecer tu contraseña en Cosmofood.

                            Para crear una nueva contraseña, haz clic en el siguiente enlace:
                            {reset_url}

                            Este enlace expirará en 24 horas.

                            Si no solicitaste este cambio, ignora este correo.

                            Saludos,
                            El equipo de Cosmofood
                """
                
                send_mail(
                    subject='Recuperación de Contraseña - Cosmofood',
                    message=mensaje,
                    from_email='cosmofood@grivyzom.com',
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Te hemos enviado un correo con instrucciones para restablecer tu contraseña.')
                return redirect('login')
            except Usuario.DoesNotExist:
                messages.error(request, 'No existe una cuenta con ese correo electrónico.')
    else:
        form = RecuperarPasswordForm()
    
    return render(request, 'core/recuperar_password.html', {'form': form})

def reset_password_view(request, uidb64, token):
    """Vista para restablecer contraseña con token (HU07)"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None
    
    if usuario is not None and default_token_generator.check_token(usuario, token):
        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                usuario.set_password(form.cleaned_data['password1'])
                usuario.save()
                messages.success(request, '¡Tu contraseña ha sido restablecida! Ahora puedes iniciar sesión.')
                return redirect('login')
        else:
            form = ResetPasswordForm()
        return render(request, 'core/reset_password.html', {'form': form, 'validlink': True})
    else:
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        # Es mejor mostrar un mensaje en una página en lugar de redirigir directamente
        # para que el usuario entienda qué pasó.
        return render(request, 'core/reset_password.html', {'validlink': False})

# ========== PERFIL DE USUARIO ==========

@login_required
def perfil_view(request):
    """Vista para ver datos personales (HU08)"""
    return render(request, 'core/perfil.html', {'usuario': request.user})

@login_required
def editar_perfil_view(request):
    """Vista para editar datos personales (HU09)"""
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'core/editar_perfil.html', {'form': form})

# ========== PEDIDOS DE USUARIO ==========

@login_required
def mis_pedidos_view(request):
    """Vista para que el usuario vea su historial de pedidos."""
    pedidos = Pedido.objects.filter(cliente=request.user).prefetch_related('detalles', 'detalles__producto').order_by('-fecha_creacion')
    
    contexto = {
        'pedidos': pedidos
    }
    return render(request, 'core/mis_pedidos.html', contexto)

# ========== CARRITO DE COMPRAS ==========

@login_required
def ver_carrito_view(request):
    """Vista para que el usuario vea su carrito de compras (HU11)"""
    # El carrito se crea automáticamente al registrarse.
    # Usamos un try-except como medida de seguridad por si algo fallara.
    try:
        carrito = request.user.carrito
        items = carrito.items.all().select_related('producto')
    except Carrito.DoesNotExist:
        # Si el carrito no existe por alguna razón, lo creamos.
        carrito = Carrito.objects.create(usuario=request.user)
        items = []

    contexto = {
        'carrito': carrito,
        'items': items
    }
    return render(request, 'core/carrito.html', contexto)

@login_required
def agregar_al_carrito_view(request):

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        cantidad = int(request.POST.get('cantidad', 1))

        producto = get_object_or_404(Producto, id=product_id)

        # Validar que el producto esté activo y haya suficiente stock
        if not producto.activo:
            messages.error(request, f'El producto "{producto.nombre}" no está disponible actualmente.')
            return redirect('catalogo_productos')
        if producto.stock < cantidad:
            messages.error(request, f'No hay suficiente stock de "{producto.nombre}". Solo quedan {producto.stock} unidades.')
            return redirect('catalogo_productos')

        carrito, created = Carrito.objects.get_or_create(usuario=request.user)

        item_carrito, item_created = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': 0} # Inicializamos en 0 si es nuevo para sumar correctamente
        )
        item_carrito.cantidad += cantidad
        item_carrito.save()

        messages.success(request, f'"{producto.nombre}" ha sido agregado al carrito. Cantidad actual: {item_carrito.cantidad}.')
        return redirect('catalogo_productos')
    return redirect('catalogo_productos') # Redirigir si no es POST

@login_required
def actualizar_cantidad_carrito_view(request):
    """
    Vista para aumentar o disminuir la cantidad de un item en el carrito.
    """
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        item = get_object_or_404(ItemCarrito, id=item_id)
        
        # Seguridad: Verificar que el item pertenece al carrito del usuario actual
        if item.carrito.usuario != request.user:
            messages.error(request, "Acción no permitida.")
            return redirect('ver_carrito')

        if action == 'increase':
            # Validar stock antes de aumentar
            if item.producto.stock > item.cantidad:
                item.cantidad += 1
                item.save()
            else:
                messages.warning(request, f'No hay más stock disponible para "{item.producto.nombre}".')
        elif action == 'decrease':
            item.cantidad -= 1
            if item.cantidad > 0:
                item.save()
            else:
                # Si la cantidad llega a 0, eliminamos el item
                item.delete()
                messages.info(request, f'"{item.producto.nombre}" ha sido eliminado del carrito.')
    
    return redirect('ver_carrito')

@login_required
def eliminar_item_carrito_view(request):
    """Vista para eliminar un item completo del carrito."""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item = get_object_or_404(ItemCarrito, id=item_id)

        if item.carrito.usuario == request.user:
            nombre_producto = item.producto.nombre
            item.delete()
            messages.success(request, f'"{nombre_producto}" ha sido eliminado de tu carrito.')
        else:
            messages.error(request, "Acción no permitida.")
    return redirect('ver_carrito')

# ========== GESTIÓN DE PRODUCTOS (ADMIN) ==========

@login_required
def admin_productos_lista(request):
    """Listar todos los productos (HU01)"""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('home')
    
    productos = Producto.objects.all().select_related('categoria').order_by('nombre')
    
    # Búsqueda
    busqueda = request.GET.get('q', '')
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)
    
    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    contexto = {
        'productos': productos,
        'categorias': Categoria.objects.filter(activo=True),
        'busqueda': busqueda,
        'categoria_seleccionada': categoria_id
    }
    return render(request, 'core/admin/productos_lista.html', contexto)

@login_required
def admin_producto_crear(request):
    """Crear nuevo producto (HU02)"""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'El producto "{producto.nombre}" ha sido creado exitosamente.')
            return redirect('admin_productos_lista')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ProductoForm()
    
    contexto = {
        'form': form,
        'titulo': 'Crear Nuevo Producto'
    }
    return render(request, 'core/admin/producto_form.html', contexto)

@login_required
def admin_producto_editar(request, pk):
    """Editar un producto existente (HU03)"""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
    
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'El producto "{producto.nombre}" ha sido actualizado exitosamente.')
            return redirect('admin_productos_lista')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ProductoForm(instance=producto)
        
    contexto = {
        'form': form,
        'producto': producto,
        'titulo': f'Editar Producto: {producto.nombre}'
    }
    return render(request, 'core/admin/producto_form.html', contexto)

@login_required
def admin_producto_desactivar(request, pk):
    """Desactiva un producto (HU04)"""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
        
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        producto.activo = not producto.activo # Alterna el estado
        producto.save()
        
        estado = "activado" if producto.activo else "desactivado"
        messages.success(request, f'El producto "{producto.nombre}" ha sido {estado}.')
    
    return redirect('admin_productos_lista')

# ========== GESTIÓN DE PEDIDOS (ADMIN) ==========

@login_required
def admin_pedidos_lista_view(request):
    """Vista para que el admin vea y filtre todos los pedidos."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('home')

    pedidos = Pedido.objects.all().select_related('cliente').order_by('-fecha_creacion')

    # Búsqueda
    busqueda = request.GET.get('q', '')
    if busqueda:
        pedidos = pedidos.filter(
            models.Q(numero_pedido__icontains=busqueda) |
            models.Q(cliente__username__icontains=busqueda) |
            models.Q(cliente__first_name__icontains=busqueda) |
            models.Q(cliente__last_name__icontains=busqueda)
        )

    # Filtro por estado
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    contexto = {
        'pedidos': pedidos,
        'busqueda': busqueda,
        'estado_seleccionado': estado_filtro,
        'estados_posibles': Pedido.ESTADO_CHOICES,
    }
    return render(request, 'core/admin/pedidos_lista.html', contexto)

@login_required
def admin_pedido_detalle_view(request, pk):
    """Vista para que el admin vea el detalle de un pedido y cambie su estado."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('home')

    pedido = get_object_or_404(Pedido.objects.prefetch_related('detalles', 'detalles__producto'), pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in [estado[0] for estado in Pedido.ESTADO_CHOICES]:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'El estado del pedido #{pedido.numero_pedido} ha sido actualizado a "{pedido.get_estado_display()}".')
            return redirect('admin_pedido_detalle', pk=pedido.pk)
        else:
            messages.error(request, 'Estado no válido.')

    contexto = {
        'pedido': pedido,
        'estados_posibles': Pedido.ESTADO_CHOICES,
    }
    return render(request, 'core/admin/pedido_detalle.html', contexto)