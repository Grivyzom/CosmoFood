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

@login_required
def admin_productos_view(request):

    if request.user.rol != 'administrador':
        return redirect('home')
    
    productos = Producto.objects.all().select_related('categoria')
    
    # Filtros
    categoria = request.GET.get('categoria')
    busqueda = request.GET.get('q')
    
    if categoria:
        productos = productos.filter(categoria_id=categoria)
        
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)
    
    return render(request, 'core/admin/productos_lista.html', {
        'productos': productos,
        'categorias': Categoria.objects.filter(activo=True)
        
    })
    
@login_required
def admin_producto_desactivar(request, pk):
    if request.user.rol != 'administrador':
        return redirect('home')
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = False
    producto.save()
    
    messages.success(request, f'Producto "{producto.nombre}" desactivado.')
    return redirect('admin_productos')

@login_required
def admin_producto_editar(request, pk):
    if request.user.rol != 'administrador':
        return redirect('home')
    
    Producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=Producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('admin_productos')
    else:
        form = ProductoForm(instance=Producto)
    return render(request, 'core/admin/producto_form.html',{
        'form': form,
        'producto': Producto
        })
