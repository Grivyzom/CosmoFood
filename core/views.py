from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib import messages
from django.db import models
from django.db import transaction
from django.http import JsonResponse
from .forms import ( 
    RegistroForm, LoginForm, PerfilForm, ProductoForm,
    RecuperarPasswordForm, ResetPasswordForm
)
from .models import Carrito, Producto, Usuario, Categoria, ItemCarrito, Pedido, Slide,MetodoPago, DetallePedido,Reclamo,Repartidor
from .forms import RepartidorForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.db.models import Sum    
from datetime import timedelta
import json


def home(request):
    slides = Slide.objects.filter(activo=True).order_by('orden')
    # Obtener productos en promoción (máximo 6 para el carrusel)
    productos_promocion = Producto.objects.filter(
        activo=True,
        en_promocion=True,
        stock__gt=0
    ).select_related('categoria').order_by('-fecha_actualizacion')[:6]

    contexto = {
        'slides': slides,
        'productos_promocion': productos_promocion
    }
    return render(request, 'core/home.html', contexto)


def catalogo_productos_view(request):
    """Vista para que los clientes y visitantes vean el catálogo de productos (HU10)"""
    
    productos = Producto.objects.none()
    
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
                    return redirect('admin_dashboard')
                elif user.rol == 'repartidor':
                    return redirect('repartidor_pedidos')
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

# ========== DASHBOARD (ADMIN) ==========

@login_required
def admin_dashboard_view(request):
    """Muestra el panel principal del administrador con estadísticas clave."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('home')

    # --- Manejo de Creación de Categoría desde el Modal ---
    if request.method == 'POST' and request.POST.get('action') == 'crear_categoria':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('activo') == 'on'
        
        if nombre:
            try:
                Categoria.objects.create(
                    nombre=nombre,
                    descripcion=descripcion if descripcion else None,
                    activo=activo
                )
                messages.success(request, f'La categoría "{nombre}" ha sido creada exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al crear la categoría: {str(e)}')
        else:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
        
        return redirect('admin_dashboard')

    # --- Cálculos para las Tarjetas KPI ---
    today = timezone.now().date()

    # 1. Ventas de Hoy
    ventas_hoy = Pedido.objects.filter(
        fecha_creacion__date=today,
        estado__in=['confirmado', 'en_preparacion', 'listo', 'en_camino', 'entregado']
    ).aggregate(total_ventas=Sum('total'))['total_ventas'] or 0

    # 2. Pedidos de Hoy
    pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=today).count()

    # 3. Clientes Totales
    total_clientes = Usuario.objects.filter(rol='cliente').count()

    # 4. Productos Activos
    total_productos_activos = Producto.objects.filter(activo=True).count()

    # 5. Pedidos pendientes para la lista
    pedidos_recientes = Pedido.objects.filter(
        estado__in=['confirmado', 'en_preparacion']
    ).order_by('-fecha_creacion')[:5] # Los 5 más recientes

    # --- Cálculo para el Gráfico "Ventas de la Semana" ---
    # Diccionario para traducir días al español
    dias_espanol = {
        'Mon': 'Lun', 'Tue': 'Mar', 'Wed': 'Mié', 
        'Thu': 'Jue', 'Fri': 'Vie', 'Sat': 'Sáb', 'Sun': 'Dom'
    }
    
    dias = []
    ventas_por_dia = []
    for i in range(7):
        dia = today - timedelta(days=i)
        dia_ingles = dia.strftime('%a')  # Obtiene día en inglés (Mon, Tue, etc.)
        dia_espanol = dias_espanol.get(dia_ingles, dia_ingles)  # Traduce al español
        dias.append(dia_espanol)
        ventas_dia = Pedido.objects.filter(
            fecha_creacion__date=dia,
            estado__in=['confirmado', 'en_preparacion', 'listo', 'en_camino', 'entregado']
        ).aggregate(total=Sum('total'))['total'] or 0
        ventas_por_dia.append(float(ventas_dia))
    dias.reverse()
    ventas_por_dia.reverse()

    detalles_hoy = DetallePedido.objects.filter(
        pedido__fecha_creacion__date=today,
        pedido__estado__in=['confirmado', 'en_preparacion', 'listo', 'en_camino', 'entregado']
    )
    productos_populares_hoy = detalles_hoy.values('producto__nombre') \
                                          .annotate(cantidad_vendida=Sum('cantidad')) \
                                          .order_by('-cantidad_vendida')[:5]
    productos_bajo_stock = Producto.objects.filter(
        activo=True,
        stock__lte=10
    ).select_related('categoria').order_by('stock', 'nombre')[:10]  # Los 10 con menos stock

    contexto = {
        'ventas_hoy': ventas_hoy,
        'pedidos_hoy': pedidos_hoy,
        'total_clientes': total_clientes,
        'total_productos_activos': total_productos_activos,
        'pedidos_recientes': pedidos_recientes,
        'titulo': 'Dashboard',
        # Datos para gráfico de ventas
        'chart_labels': json.dumps(dias),
        'chart_data': json.dumps(ventas_por_dia),
        # --- NUEVA VARIABLE AÑADIDA ---
        'productos_populares': productos_populares_hoy,
        'productos_bajo_stock': productos_bajo_stock,  # Nueva variable
    }

    return render(request, 'core/admin/dashboard.html', contexto)



# ========== GESTIÓN DE PRODUCTOS (ADMIN) ==========

@login_required
def admin_productos_lista(request):
    """Listar todos los productos (HU01) y mostrar estadísticas."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('home')
    
    # Obtenemos la base de productos (todos)
    productos_base = Producto.objects.all().select_related('categoria')
    
    # --- Cálculo de Estadísticas para las Tarjetas ---
    total_productos = productos_base.count()
    productos_activos = productos_base.filter(activo=True).count()
    stock_bajo = productos_base.filter(activo=True, stock__lte=10).count() 
    total_categorias = Categoria.objects.filter(activo=True).count()
    # --- FIN Cálculo ---

    # Aplicamos filtros sobre la base
    productos_filtrados = productos_base # Empezamos con todos
    
    # Búsqueda
    busqueda = request.GET.get('q', '')
    if busqueda:
        productos_filtrados = productos_filtrados.filter(
            models.Q(nombre__icontains=busqueda) | 
            models.Q(descripcion__icontains=busqueda) 
        )
    
    # Filtro por categoría (usando el ID)
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        try:
            productos_filtrados = productos_filtrados.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            pass 
            
    # Filtro por estado (activo/inactivo/stock bajo)
    status_filter = request.GET.get('status', 'all') 
    if status_filter == 'active':
        productos_filtrados = productos_filtrados.filter(activo=True)
    elif status_filter == 'inactive':
        productos_filtrados = productos_filtrados.filter(activo=False)
    elif status_filter == 'low-stock':
         productos_filtrados = productos_filtrados.filter(activo=True, stock__lte=10)
         
    # Ordenamiento
    sort_by = request.GET.get('sort', 'nombre') 
    if sort_by == 'precio':
        productos_filtrados = productos_filtrados.order_by('precio')
    elif sort_by == 'stock':
        productos_filtrados = productos_filtrados.order_by('stock')
    elif sort_by == 'categoria':
        productos_filtrados = productos_filtrados.order_by('categoria__nombre')
    else: 
        productos_filtrados = productos_filtrados.order_by('nombre')
        
    contexto = {
        'productos': productos_filtrados, 
        'categorias': Categoria.objects.filter(activo=True).order_by('nombre'),
        'busqueda': busqueda,
        'categoria_seleccionada': categoria_id, 
        'status_filter': status_filter, 
        'sort_by': sort_by, 
        
        # --- Enviamos las estadísticas ---
        'total_productos': total_productos,
        'productos_activos': productos_activos,
        'stock_bajo': stock_bajo,
        'total_categorias': total_categorias,
        'titulo': 'Gestión de Productos' 
    }
    return render(request, 'core/admin/productos_lista.html', contexto)

# --- CRUD de Productos ---

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
        # Pasamos las categorías al formulario para el dropdown
        form = ProductoForm()
        form.fields['categoria'].queryset = Categoria.objects.filter(activo=True).order_by('nombre') 
    
    contexto = {
        'form': form,
        'titulo': 'Crear Nuevo Producto'
    }
    return render(request, 'core/admin/producto_form.html', contexto) # Usa la plantilla correcta

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
        form.fields['categoria'].queryset = Categoria.objects.filter(activo=True).order_by('nombre')
        
    contexto = {
        'form': form,
        'producto': producto,
        'titulo': f'Editar Producto: {producto.nombre}'
    }
    return render(request, 'core/admin/producto_form.html', contexto)

@login_required
def admin_producto_desactivar(request, pk):
    """Activa o Desactiva un producto (HU04)""" # Texto actualizado
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
        
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        producto.activo = not producto.activo # Alterna el estado
        producto.save()
        
        estado = "activado" if producto.activo else "desactivado"
        messages.success(request, f'El producto "{producto.nombre}" ha sido {estado}.')
    
    # Redirigimos de vuelta a la lista (mejor que al home)
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
def admin_pedido_detalle_view(request, pk): # Renombramos pk a pk_pedido para claridad
    """Vista para que el admin vea el detalle de un pedido, cambie su estado Y ASIGNE REPARTIDOR.""" # Docstring actualizado
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('admin_pedidos_lista')

    pedido = get_object_or_404(Pedido.objects.select_related('cliente', 'metodo_pago', 'repartidor__usuario') # Incluimos repartidor__usuario
                                           .prefetch_related('detalles', 'detalles__producto'), pk=pk) # Renombrado pk_pedido

    # --- Lógica de Actualización (POST) ---
    if request.method == 'POST':
        # Determinar qué acción se está realizando (cambiar estado o asignar repartidor)
        action = request.POST.get('action')

        if action == 'cambiar_estado':
            nuevo_estado = request.POST.get('estado')
            if nuevo_estado in [estado[0] for estado in Pedido.ESTADO_CHOICES]:
                pedido.estado = nuevo_estado
                # Opcional: Actualizar timestamps según el estado
                if nuevo_estado == 'confirmado' and not pedido.fecha_confirmacion:
                     pedido.fecha_confirmacion = timezone.now()
                elif nuevo_estado == 'en_preparacion' and not pedido.fecha_preparacion:
                     pedido.fecha_preparacion = timezone.now()
                # ... (añadir lógica similar para otros estados si es necesario) ...
                pedido.save()
                messages.success(request, f'Estado del pedido #{pedido.numero_pedido} actualizado a "{pedido.get_estado_display()}".')
            else:
                messages.error(request, 'Estado no válido.')

        elif action == 'asignar_repartidor':
            repartidor_usuario_id = request.POST.get('repartidor_asignado')
            if repartidor_usuario_id:
                try:
                    # Buscamos el *perfil* Repartidor por el ID del *Usuario* asociado
                    repartidor_a_asignar = Repartidor.objects.get(usuario_id=int(repartidor_usuario_id), disponible=True)
                    pedido.repartidor = repartidor_a_asignar
                    # Opcional: Cambiar estado a 'En Camino' al asignar? Depende del flujo.
                    # pedido.estado = 'en_camino'
                    pedido.save()
                    messages.success(request, f'Repartidor "{repartidor_a_asignar.usuario.username}" asignado al pedido #{pedido.numero_pedido}.')
                except (Repartidor.DoesNotExist, ValueError):
                    messages.error(request, 'Repartidor seleccionado no válido o no disponible.')
            else: # Si se selecciona "Ninguno"
                 pedido.repartidor = None
                 pedido.save()
                 messages.info(request, f'Repartidor desasignado del pedido #{pedido.numero_pedido}.')

        # Redirigir siempre a la misma página de detalle después de una acción POST
        return redirect('admin_pedido_detalle', pk=pedido.pk) # Renombrado pk_pedido

    # --- Lógica para Mostrar (GET) ---
    else:
        # Obtenemos repartidores disponibles para el dropdown
        repartidores_disponibles = Repartidor.objects.filter(disponible=True).select_related('usuario').order_by('usuario__username')

        contexto = {
            'pedido': pedido,
            'estados_posibles': Pedido.ESTADO_CHOICES,
            'repartidores_disponibles': repartidores_disponibles, # Pasamos la lista a la plantilla
            'titulo': f'Detalle Pedido #{pedido.numero_pedido}'
        }
        return render(request, 'core/admin/pedido_detalle.html', contexto)

# ========== PUNTO DE VENTA (POS - HU24, HU25) ==========

@login_required
def pos_view(request):
    """Muestra la interfaz del Punto de Venta y procesa ventas locales."""
    # Solo Cajero o Administrador pueden acceder
    if request.user.rol not in ['cajero', 'administrador']:
        messages.error(request, 'No tienes permisos para acceder al POS.')
        return redirect('home')

    if request.method == 'POST':
        # --- Procesar la Venta ---
        try:
            # Recuperar datos enviados por JavaScript
            items_json = request.POST.get('items')
            total_venta = float(request.POST.get('total', 0))
            metodo_pago_nombre = request.POST.get('metodo_pago')
            # Obtener nombre de referencia del input opcional
            nombre_referencia = request.POST.get('nombre_referencia', '')

            # Validaciones básicas de datos recibidos
            if not items_json or total_venta <= 0 or not metodo_pago_nombre:
                messages.error(request, 'Faltan datos para registrar la venta.')
                return redirect('pos_view')

            items = json.loads(items_json)

            # Buscamos o creamos el método de pago local
            metodo_pago_obj, created = MetodoPago.objects.get_or_create(
                nombre=metodo_pago_nombre,
                defaults={'tipo': 'local', 'activo': True}
            )

            # Usamos una transacción para asegurar que todo se guarde correctamente o nada
            with transaction.atomic():
                # --- Obtener Usuario Genérico ---
                try:
                    # Busca el usuario con username 'clientelocal'
                    usuario_generico = Usuario.objects.get(username='clientelocal')
                except Usuario.DoesNotExist:
                    # Si no existe, muestra advertencia y usa al usuario logueado como fallback
                    messages.warning(request, "Usuario 'clientelocal' no encontrado. Asignando pedido al usuario actual.")
                    usuario_generico = request.user
                # --- Fin Obtener Usuario ---

                # Crear el objeto Pedido en la base de datos
                nuevo_pedido = Pedido.objects.create(
                    cliente=usuario_generico,                 # <-- USA USUARIO GENÉRICO
                    nombre_referencia_cliente=nombre_referencia, # <-- GUARDA NOMBRE REFERENCIA
                    metodo_pago=metodo_pago_obj,
                    tipo_orden='local',                       # Tipo de orden para POS
                    estado='en_preparacion',                  # <-- ESTADO INICIAL CORRECTO
                    subtotal=total_venta,                     # Asume que el total JS es el subtotal
                    costo_envio=0,                            # Sin costo de envío para POS
                    total=total_venta,                        # Total igual a subtotal
                )

                # Crear los Detalles del Pedido y descontar stock para cada item
                for item_data in items:
                    producto = Producto.objects.select_for_update().get(pk=item_data['id'])
                    cantidad = int(item_data['cantidad'])

                    if producto.stock < cantidad:
                        raise ValueError(f"Stock insuficiente para {producto.nombre}")

                    DetallePedido.objects.create(
                        pedido=nuevo_pedido,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                    )
                    producto.stock -= cantidad
                    producto.save()

            messages.success(request, f'Venta #{nuevo_pedido.numero_pedido} registrada exitosamente.')
            return redirect('pos_view') # Redirige de vuelta al POS

        # --- Manejo de Errores Específicos ---
        except Producto.DoesNotExist:
            messages.error(request, 'Error: Uno de los productos seleccionados ya no existe.')
            return redirect('pos_view')
        except ValueError as e:
             messages.error(request, f'Error al registrar venta: {e}')
             return redirect('pos_view')
        except Usuario.DoesNotExist:
             messages.error(request, "Error crítico: No se pudo asignar un cliente al pedido. Contacta al administrador.")
             return redirect('pos_view')
        except Exception as e:
            messages.error(request, f'Error inesperado al registrar venta: {e}')
            return redirect('pos_view')

    # --- Si la petición es GET (Mostrar la interfaz) ---
    else:
        # Cambiado: Mostrar todos los productos activos, sin importar el stock
        # El stock se validará al agregar al carrito
        productos_pos = Producto.objects.filter(activo=True).select_related('categoria').order_by('categoria__nombre', 'nombre')
        categorias_pos = Categoria.objects.filter(activo=True, productos__in=productos_pos).distinct().order_by('nombre')

        contexto = {
            'productos_pos': productos_pos,
            'categorias_pos': categorias_pos,
            'titulo': 'Punto de Venta (POS)'
        }
        # Asegúrate que el nombre de la plantilla sea correcto ('pos.html' o 'pos_view.html')
        return render(request, 'core/admin/pos.html', contexto)
    
# ========== GESTIÓN DE RECLAMOS (ADMIN - HU21, HU22) ==========

@login_required
def admin_reclamos_lista(request):
    """Muestra una lista de todos los reclamos de clientes."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('admin_dashboard') # O 'home'

    # Obtenemos todos los reclamos, con info del cliente y pedido asociado
    # Ordenamos por fecha (más nuevos primero) y luego por estado (nuevos primero)
    reclamos = Reclamo.objects.select_related('cliente', 'pedido').order_by('estado', '-fecha_creacion')

    # --- Opcional: Filtro por Estado ---
    estado_filtro = request.GET.get('estado', '') # Obtiene el parámetro 'estado' de la URL
    if estado_filtro:
        reclamos = reclamos.filter(estado=estado_filtro)
    # --- Fin Filtro ---

    contexto = {
        'reclamos': reclamos,
        'estados_posibles': Reclamo.ESTADO_CHOICES, # Pasa las opciones de estado para el filtro
        'estado_seleccionado': estado_filtro,       # Pasa el estado actual seleccionado
        'titulo': 'Gestión de Reclamos'
    }
    return render(request, 'core/admin/reclamos_lista.html', contexto) # Nueva plantilla

@login_required
def admin_reclamo_detalle(request, pk_reclamo):
    """Muestra el detalle de un reclamo y permite actualizar estado/respuesta."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('admin_reclamos_lista') # Vuelve a la lista de reclamos

    # Obtenemos el reclamo específico o error 404
    reclamo = get_object_or_404(Reclamo.objects.select_related('cliente', 'pedido', 'atendido_por'), pk=pk_reclamo)

    # Si se envía el formulario (método POST) para actualizar
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        respuesta_admin = request.POST.get('respuesta', '').strip() # Obtiene la respuesta y quita espacios extra

        # Validar que el estado sea válido
        if nuevo_estado not in [estado[0] for estado in Reclamo.ESTADO_CHOICES]:
            messages.error(request, 'Estado seleccionado no válido.')
        else:
            # Actualizar los campos del reclamo
            reclamo.estado = nuevo_estado
            reclamo.respuesta = respuesta_admin
            reclamo.atendido_por = request.user # Guarda quién respondió
            reclamo.fecha_respuesta = timezone.now() # Guarda la fecha de respuesta
            reclamo.save() # Guarda los cambios en la BD

            messages.success(request, f'Reclamo #{reclamo.id} actualizado exitosamente.')
            # Redirige de nuevo a la misma página de detalle para ver los cambios
            return redirect('admin_reclamo_detalle', pk_reclamo=reclamo.pk)

    # Si es GET (o si hubo error en POST), muestra la página de detalle
    contexto = {
        'reclamo': reclamo,
        'estados_posibles': Reclamo.ESTADO_CHOICES, # Pasa opciones para el dropdown
        'titulo': f'Detalle Reclamo #{reclamo.id}'
    }
    return render(request, 'core/admin/reclamo_detalle.html', contexto) # Nueva plantilla

# ========== GESTIÓN DE REPARTIDORES (ADMIN) ==========

@login_required
def admin_repartidores_lista(request):
    """Muestra la lista de todos los repartidores registrados."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para acceder aquí.')
        return redirect('admin_dashboard') 

    # Obtenemos todos los repartidores, incluyendo la info del usuario asociado
    repartidores = Repartidor.objects.all().select_related('usuario').order_by('usuario__username')

    contexto = {
        'repartidores': repartidores,
        'titulo': 'Gestión de Repartidores'
    }
    return render(request, 'core/admin/repartidores_lista.html', contexto) # Nueva plantilla

@login_required
def admin_repartidor_crear(request):
    """Muestra y procesa el formulario para crear un nuevo repartidor."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('admin_repartidores_lista')

    if request.method == 'POST':
        # Usaremos un formulario específico para Repartidor
        form = RepartidorForm(request.POST)
        if form.is_valid():
            # Creamos primero el Usuario asociado
            try:
                usuario = Usuario.objects.create(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    telefono=form.cleaned_data['telefono'],
                    # Creamos una contraseña temporal o la asignamos si viene del form
                    password=make_password(form.cleaned_data['password']),
                    rol='repartidor' # Asignamos el rol correcto
                )
                # Luego creamos el Repartidor asociado a ese usuario
                Repartidor.objects.create(
                    usuario=usuario,
                    vehiculo=form.cleaned_data.get('vehiculo'), # Usamos .get por si es opcional
                    placa_vehiculo=form.cleaned_data.get('placa_vehiculo'),
                    disponible=form.cleaned_data.get('disponible', True) # Por defecto disponible
                )
                messages.success(request, f'Repartidor "{usuario.username}" creado exitosamente.')
                return redirect('admin_repartidores_lista')
            except Exception as e: # Captura errores (ej: username duplicado)
                messages.error(request, f'Error al crear repartidor: {e}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Muestra el formulario vacío
        form = RepartidorForm()

    contexto = {
        'form': form,
        'titulo': 'Crear Nuevo Repartidor'
    }
    return render(request, 'core/admin/repartidor_form.html', contexto) # Nueva plantilla

@login_required
def admin_repartidor_editar(request, pk_usuario): # Usamos el PK del Usuario
    """Muestra y procesa el formulario para editar un repartidor existente."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('admin_repartidores_lista')

    # Obtenemos el Usuario (que debe tener rol repartidor)
    usuario_repartidor = get_object_or_404(Usuario, pk=pk_usuario, rol='repartidor')
    # Obtenemos el perfil Repartidor asociado (puede que no exista si hubo error antes)
    repartidor_perfil = Repartidor.objects.filter(usuario=usuario_repartidor).first()

    if request.method == 'POST':
        # 'instance=usuario_repartidor' precarga datos del Usuario
        # 'instance_perfil=repartidor_perfil' es un argumento extra para nuestro form
        form = RepartidorForm(request.POST, instance=usuario_repartidor, instance_perfil=repartidor_perfil, initial={'username': usuario_repartidor.username}) # Pasamos initial username
        if form.is_valid():
            try:
                # Guardamos cambios en el Usuario
                usuario_repartidor.email = form.cleaned_data['email']
                usuario_repartidor.first_name = form.cleaned_data['first_name']
                usuario_repartidor.last_name = form.cleaned_data['last_name']
                usuario_repartidor.telefono = form.cleaned_data['telefono']
                # Opcional: Cambiar contraseña si se proporciona
                password = form.cleaned_data.get('password')
                if password:
                    usuario_repartidor.set_password(password)
                usuario_repartidor.save()

                # Guardamos o creamos/actualizamos el perfil Repartidor
                if repartidor_perfil:
                    repartidor_perfil.vehiculo = form.cleaned_data.get('vehiculo')
                    repartidor_perfil.placa_vehiculo = form.cleaned_data.get('placa_vehiculo')
                    repartidor_perfil.disponible = form.cleaned_data.get('disponible')
                    repartidor_perfil.save()
                else: # Si no existía el perfil, lo creamos
                     Repartidor.objects.create(
                        usuario=usuario_repartidor,
                        vehiculo=form.cleaned_data.get('vehiculo'),
                        placa_vehiculo=form.cleaned_data.get('placa_vehiculo'),
                        disponible=form.cleaned_data.get('disponible', True)
                    )

                messages.success(request, f'Repartidor "{usuario_repartidor.username}" actualizado.')
                return redirect('admin_repartidores_lista')
            except Exception as e:
                 messages.error(request, f'Error al actualizar repartidor: {e}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Muestra el form precargado
        form = RepartidorForm(instance=usuario_repartidor, instance_perfil=repartidor_perfil, initial={'username': usuario_repartidor.username})

    contexto = {
        'form': form,
        'repartidor_usuario': usuario_repartidor, # Pasamos el usuario para info
        'titulo': f'Editar Repartidor: {usuario_repartidor.username}'
    }
    return render(request, 'core/admin/repartidor_form.html', contexto)

@login_required
def admin_repartidor_toggle_disponible(request, pk_usuario): # Usamos PK del Usuario
    """Cambia el estado 'disponible' de un repartidor."""
    if request.user.rol != 'administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('admin_repartidores_lista')

    if request.method == 'POST':
        usuario_repartidor = get_object_or_404(Usuario, pk=pk_usuario, rol='repartidor')
        repartidor_perfil = Repartidor.objects.filter(usuario=usuario_repartidor).first()

        if repartidor_perfil:
            repartidor_perfil.disponible = not repartidor_perfil.disponible # Invertimos estado
            repartidor_perfil.save()
            estado = "disponible" if repartidor_perfil.disponible else "no disponible"
            messages.success(request, f'El repartidor "{usuario_repartidor.username}" ahora está {estado}.')
        else:
            messages.error(request, f'El perfil de repartidor para "{usuario_repartidor.username}" no existe.')

    return redirect('admin_repartidores_lista')

# ========== BÚSQUEDA DE PEDIDO (AJAX) ==========

@login_required
def buscar_pedido_view(request):
    """Busca un pedido por número de pedido o ID y devuelve su ID en JSON."""
    if request.user.rol != 'administrador':
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Parámetro de búsqueda vacío'})
    
    try:
        # Intentar buscar por número de pedido primero
        pedido = Pedido.objects.filter(numero_pedido=query).first()
        
        # Si no se encuentra, intentar por ID
        if not pedido:
            try:
                pedido_id = int(query)
                pedido = Pedido.objects.filter(pk=pedido_id).first()
            except (ValueError, TypeError):
                pass
        
        if pedido:
            return JsonResponse({
                'success': True,
                'pedido_id': pedido.pk,
                'numero_pedido': pedido.numero_pedido
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Pedido no encontrado'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ========== VISTA DEL REPARTIDOR (HU18) ==========

@login_required
def repartidor_pedidos_view(request):
    """
    Vista para que el repartidor gestione las entregas asignadas.
    HU18: Ver pedidos asignados y actualizar estado de entrega.
    
    Funcionalidades:
    - Ver lista de pedidos asignados al repartidor
    - Ver detalles: dirección, productos, contacto del cliente
    - Actualizar estado: 'En preparación', 'Listo para entregar', 'En camino', 'Entregado'
    """
    # Validar que el usuario sea un repartidor
    if request.user.rol != 'repartidor':
        messages.error(request, 'No tienes permisos para acceder a esta área.')
        return redirect('home')
    
    # Obtener el perfil de repartidor del usuario actual
    try:
        perfil_repartidor = request.user.perfil_repartidor
    except Repartidor.DoesNotExist:
        messages.error(request, 'No tienes un perfil de repartidor asociado. Contacta al administrador.')
        return redirect('home')
    
    # Manejar actualización de estado (POST)
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        
        # Validar que se recibieron los datos
        if not pedido_id or not nuevo_estado:
            messages.error(request, 'Datos incompletos para actualizar el pedido.')
            return redirect('repartidor_pedidos')
        
        # Obtener el pedido
        try:
            pedido = Pedido.objects.get(pk=pedido_id, repartidor=perfil_repartidor)
            
            # Validar que el nuevo estado sea válido para el repartidor
            estados_permitidos = ['en_preparacion', 'listo', 'en_camino', 'entregado']
            if nuevo_estado not in estados_permitidos:
                messages.error(request, 'Estado no permitido.')
                return redirect('repartidor_pedidos')
            
            # Actualizar el estado
            estado_anterior = pedido.estado
            pedido.estado = nuevo_estado
            
            # Actualizar timestamps según el estado
            if nuevo_estado == 'en_preparacion' and not pedido.fecha_preparacion:
                pedido.fecha_preparacion = timezone.now()
            elif nuevo_estado == 'listo' and not pedido.fecha_listo:
                pedido.fecha_listo = timezone.now()
            elif nuevo_estado == 'entregado' and not pedido.fecha_entrega:
                pedido.fecha_entrega = timezone.now()
            
            pedido.save()
            
            messages.success(request, f'Pedido #{pedido.numero_pedido} actualizado de "{pedido.get_estado_display()}" a "{dict(Pedido.ESTADO_CHOICES)[nuevo_estado]}".')
            
        except Pedido.DoesNotExist:
            messages.error(request, 'Pedido no encontrado o no tienes permisos para modificarlo.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el pedido: {str(e)}')
        
        return redirect('repartidor_pedidos')
    
    # Obtener pedidos asignados al repartidor (GET)
    # Estados relevantes: confirmado, en_preparacion, listo, en_camino
    pedidos_asignados = Pedido.objects.filter(
        repartidor=perfil_repartidor,
        estado__in=['confirmado', 'en_preparacion', 'listo', 'en_camino']
    ).select_related('cliente', 'metodo_pago').prefetch_related('detalles__producto').order_by('estado', 'fecha_creacion')
    
    # También mostrar pedidos entregados recientes (últimas 24 horas)
    hace_24_horas = timezone.now() - timedelta(hours=24)
    pedidos_entregados_recientes = Pedido.objects.filter(
        repartidor=perfil_repartidor,
        estado='entregado',
        fecha_entrega__gte=hace_24_horas
    ).select_related('cliente', 'metodo_pago').prefetch_related('detalles__producto').order_by('-fecha_entrega')
    
    # Estadísticas para el repartidor
    total_asignados = pedidos_asignados.count()
    total_en_camino = pedidos_asignados.filter(estado='en_camino').count()
    total_entregados_hoy = Pedido.objects.filter(
        repartidor=perfil_repartidor,
        estado='entregado',
        fecha_entrega__date=timezone.now().date()
    ).count()
    
    contexto = {
        'pedidos_asignados': pedidos_asignados,
        'pedidos_entregados_recientes': pedidos_entregados_recientes,
        'total_asignados': total_asignados,
        'total_en_camino': total_en_camino,
        'total_entregados_hoy': total_entregados_hoy,
        'perfil_repartidor': perfil_repartidor,
        'titulo': 'Mis Entregas',
        'estados_disponibles': Pedido.ESTADO_CHOICES,
    }
    
    return render(request, 'core/repartidor_pedidos.html', contexto)