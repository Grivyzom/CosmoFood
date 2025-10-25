from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib import messages
from django.db import models
from django.db import transaction
from .forms import ( 
    RegistroForm, LoginForm, PerfilForm, ProductoForm,
    RecuperarPasswordForm, ResetPasswordForm
)
from .models import Carrito, Producto, Usuario, Categoria, ItemCarrito, Pedido, Slide,MetodoPago, DetallePedido
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import json

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
                    return redirect('admin_dashboard')
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
    dias = []
    ventas_por_dia = []
    for i in range(7):
        dia = today - timedelta(days=i)
        dias.append(dia.strftime('%a')) # 'Lun', 'Mar', 'Mié', etc.
        ventas_dia = Pedido.objects.filter(
            fecha_creacion__date=dia,
            estado__in=['confirmado', 'en_preparacion', 'listo', 'en_camino', 'entregado']
        ).aggregate(total=Sum('total'))['total'] or 0
        ventas_por_dia.append(float(ventas_dia))
    dias.reverse()
    ventas_por_dia.reverse()

    # --- NUEVO CÁLCULO: Productos Más Vendidos Hoy ---
    detalles_hoy = DetallePedido.objects.filter(
        pedido__fecha_creacion__date=today,
        pedido__estado__in=['confirmado', 'en_preparacion', 'listo', 'en_camino', 'entregado']
    )
    productos_populares_hoy = detalles_hoy.values('producto__nombre') \
                                          .annotate(cantidad_vendida=Sum('cantidad')) \
                                          .order_by('-cantidad_vendida')[:5]
    # --- FIN NUEVO CÁLCULO ---

    # Contexto para la plantilla
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

# (Asegúrate de tener estas importaciones al principio de views.py)
# from django.contrib.auth import get_user_model
# from django.db import transaction
# from .models import Pedido, Producto, DetallePedido, MetodoPago, Categoria, Usuario # Asegúrate que Usuario esté importado
# import json
# Usuario = get_user_model() # O usa la importación directa si prefieres

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
        productos_pos = Producto.objects.filter(activo=True, stock__gt=0).select_related('categoria').order_by('categoria__nombre', 'nombre')
        categorias_pos = Categoria.objects.filter(activo=True, productos__in=productos_pos).distinct().order_by('nombre')

        contexto = {
            'productos_pos': productos_pos,
            'categorias_pos': categorias_pos,
            'titulo': 'Punto de Venta (POS)'
        }
        # Asegúrate que el nombre de la plantilla sea correcto ('pos.html' o 'pos_view.html')
        return render(request, 'core/admin/pos.html', contexto)