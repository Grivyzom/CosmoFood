from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib import messages
from .forms import (
    RegistroForm, LoginForm, PerfilForm, ProductoForm, 
    RecuperarPasswordForm, ResetPasswordForm
)
from .models import Carrito, Producto, Usuario, Categoria
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site

# Vista de inicio (landing page)
def home(request):

    return render(request, 'core/home.html')

# ========== CATÁLOGO DE PRODUCTOS (CLIENTE) ==========

def catalogo_productos_view(request):
    """Vista para que los clientes y visitantes vean el catálogo de productos (HU10)"""
    
    # Solo mostramos productos activos y con stock
    productos = Producto.objects.filter(activo=True, stock__gt=0).select_related('categoria').order_by('nombre')
    
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