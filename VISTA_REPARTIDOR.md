# 📦 Vista del Repartidor - CosmoFood

## 📋 Descripción General

La **Vista del Repartidor** (HU18) es una interfaz diseñada específicamente para que los repartidores gestionen eficientemente las entregas que les han sido asignadas. Esta vista permite al repartidor visualizar todos sus pedidos activos, acceder a información crucial del cliente y actualizar el estado de las entregas en tiempo real.

---

## 🎯 Funcionalidades Principales

### 1. **Ver Pedidos Asignados**
- Lista completa de pedidos asignados al repartidor
- Visualización de pedidos en diferentes estados:
  - ✅ Confirmado
  - 🔥 En Preparación
  - ✔️ Listo para Entregar
  - 🚚 En Camino
  - ✅ Entregado

### 2. **Información Detallada del Pedido**
Cada pedido muestra:
- **Número de pedido** único
- **Nombre del cliente** (o nombre de referencia)
- **Teléfono de contacto** (con enlace directo para llamar)
- **Dirección de entrega** completa con referencia
- **Tipo de orden** (Delivery, Retiro, Local)
- **Total del pedido**
- **Lista de productos** con cantidades
- **Notas del cliente** (si las hay)

### 3. **Actualización de Estados**
El repartidor puede cambiar el estado del pedido según el flujo:

```
Confirmado → En Preparación → Listo → En Camino → Entregado
```

Cada transición actualiza automáticamente:
- El estado del pedido en la base de datos
- Timestamps de cambio de estado
- Notificaciones visuales para el repartidor

### 4. **Estadísticas en Tiempo Real**
Panel superior con métricas clave:
- **Pedidos Asignados**: Total de pedidos activos
- **En Camino**: Pedidos que están siendo entregados
- **Entregados Hoy**: Entregas completadas en el día

### 5. **Historial Reciente**
Sección que muestra pedidos entregados en las últimas 24 horas para referencia.

---

## 🔐 Acceso y Permisos

### Requisitos de Acceso:
1. Usuario debe estar autenticado
2. Usuario debe tener rol `'repartidor'`
3. Usuario debe tener un perfil de `Repartidor` asociado

### Formas de Acceso:
- **URL directa**: `/repartidor/pedidos/`
- **Menú de navegación**: "Mis Entregas" (visible solo para repartidores)
- **Redirección automática**: Al iniciar sesión, los repartidores son redirigidos a su vista

---

## 🖥️ Interfaz de Usuario

### Diseño Responsive
- Adaptado para dispositivos móviles (repartidores en movimiento)
- Botones grandes y accesibles para usar con guantes o en movimiento
- Colores distintivos para cada estado del pedido

### Códigos de Color por Estado:
- **Confirmado**: Amarillo (`#fef3c7`)
- **En Preparación**: Azul (`#dbeafe`)
- **Listo**: Verde claro (`#d1fae5`)
- **En Camino**: Púrpura (`#e9d5ff`)
- **Entregado**: Verde oscuro (`#d1fae5`)

### Iconos Informativos:
- 👤 Usuario: Información del cliente
- 📞 Teléfono: Contacto directo
- 📍 Ubicación: Dirección de entrega
- 📋 Clipboard: Tipo de orden
- 💵 Dinero: Total del pedido
- 📦 Caja: Lista de productos

---

## 🔄 Flujo de Trabajo del Repartidor

### Escenario Típico:

1. **Inicio de Sesión**
   - El repartidor inicia sesión con sus credenciales
   - Es redirigido automáticamente a `/repartidor/pedidos/`

2. **Revisión de Pedidos**
   - Ve lista de pedidos asignados
   - Identifica pedidos listos para recoger/entregar

3. **Preparación para Entrega**
   - Revisa dirección y contacto del cliente
   - Verifica productos del pedido
   - Lee notas especiales del cliente

4. **Actualización de Estado - En Camino**
   - Presiona botón "Iniciar Entrega"
   - Sistema registra hora de inicio

5. **Llegada al Destino**
   - Contacta al cliente si es necesario (clic en teléfono)
   - Entrega el pedido

6. **Confirmación de Entrega**
   - Presiona botón "Marcar Entregado"
   - Sistema registra hora de entrega
   - Pedido se mueve a "Entregas Recientes"

---

## 🛠️ Implementación Técnica

### Archivos Relacionados:

#### 1. **Vista Backend** (`core/views.py`)
```python
@login_required
def repartidor_pedidos_view(request):
    """Vista para gestionar entregas del repartidor (HU18)"""
    # Validación de permisos
    # Obtención de pedidos asignados
    # Manejo de actualización de estados
    # Cálculo de estadísticas
```

**Funcionalidades clave:**
- Validación de rol de repartidor
- Filtrado de pedidos por repartidor asignado
- Actualización segura de estados
- Registro de timestamps automático

#### 2. **Template HTML** (`core/templates/core/repartidor_pedidos.html`)
- Diseño moderno con Tailwind CSS y CSS personalizado
- Secciones para estadísticas, pedidos activos e historial
- Formularios inline para actualización de estados
- Diseño responsive para móviles

#### 3. **URL** (`core/urls.py`)
```python
path('repartidor/pedidos/', views.repartidor_pedidos_view, name='repartidor_pedidos'),
```

#### 4. **Navegación** (`core/templates/core/base.html`)
- Enlace "Mis Entregas" en menú desplegable
- Visible solo para usuarios con rol `'repartidor'`

---

## 📊 Modelo de Datos

### Relaciones Utilizadas:

```python
# Pedido tiene un repartidor asignado
pedido.repartidor → Repartidor → Usuario

# Acceso desde usuario repartidor
request.user.perfil_repartidor → Repartidor
```

### Estados Permitidos para Repartidor:
- `'confirmado'`
- `'en_preparacion'`
- `'listo'`
- `'en_camino'`
- `'entregado'`

### Campos de Timestamp Actualizados:
- `fecha_preparacion`: Cuando se marca "En Preparación"
- `fecha_listo`: Cuando se marca "Listo"
- `fecha_entrega`: Cuando se marca "Entregado"

---

## 🔒 Seguridad

### Validaciones Implementadas:

1. **Autenticación Obligatoria**
   ```python
   @login_required
   ```

2. **Validación de Rol**
   ```python
   if request.user.rol != 'repartidor':
       messages.error(request, 'No tienes permisos...')
       return redirect('home')
   ```

3. **Verificación de Perfil**
   ```python
   try:
       perfil_repartidor = request.user.perfil_repartidor
   except Repartidor.DoesNotExist:
       # Error: perfil no existe
   ```

4. **Validación de Propiedad**
   - Solo puede modificar pedidos asignados a él:
   ```python
   pedido = Pedido.objects.get(pk=pedido_id, repartidor=perfil_repartidor)
   ```

5. **Validación de Estados**
   - Solo puede cambiar a estados permitidos:
   ```python
   estados_permitidos = ['en_preparacion', 'listo', 'en_camino', 'entregado']
   ```

---

## 🚀 Cómo Probar

### 1. Crear Usuario Repartidor
```python
python manage.py shell
```

```python
from core.models import Usuario, Repartidor

# Crear usuario con rol repartidor
usuario = Usuario.objects.create_user(
    username='repartidor1',
    password='password123',
    first_name='Juan',
    last_name='Pérez',
    rol='repartidor',
    telefono='+56912345678'
)

# Crear perfil de repartidor
Repartidor.objects.create(
    usuario=usuario,
    vehiculo='Moto Honda',
    placa_vehiculo='AB1234',
    disponible=True
)
```

### 2. Asignar Pedido al Repartidor
- Como administrador, ir a "Gestión de Pedidos"
- Abrir un pedido
- En "Asignar Repartidor", seleccionar el repartidor creado

### 3. Probar la Vista
- Cerrar sesión
- Iniciar sesión como `repartidor1`
- Automáticamente serás redirigido a `/repartidor/pedidos/`
- Verás el pedido asignado
- Prueba cambiar el estado del pedido

---

## 📱 Uso en Móvil

### Recomendaciones:
- La interfaz está optimizada para móviles
- Uso de iconos grandes y botones táctiles
- Teléfonos son enlaces directos (`tel:`)
- Scroll suave y secciones colapsables

### Características Mobile-First:
- Grid responsive que se adapta a pantalla pequeña
- Botones de ancho completo en móviles
- Información priorizada (dirección y teléfono destacados)
- Colores de alto contraste para legibilidad

---

## 🔄 Próximas Mejoras Sugeridas

1. **Notificaciones Push**: Alertar al repartidor cuando se le asigna un nuevo pedido
2. **Mapa Integrado**: Mostrar ruta óptima usando Google Maps
3. **Escaneo de QR**: Confirmar entrega escaneando código del cliente
4. **Historial Completo**: Ver todas las entregas históricas con filtros
5. **Calificaciones**: Permitir al cliente calificar al repartidor
6. **Chat en Tiempo Real**: Comunicación directa con cliente/administrador

---

## 🐛 Troubleshooting

### Problema: "No tienes un perfil de repartidor asociado"
**Solución**: Crear perfil de Repartidor en admin o shell

### Problema: "No hay pedidos asignados"
**Solución**: El administrador debe asignar pedidos al repartidor

### Problema: No aparece "Mis Entregas" en el menú
**Solución**: Verificar que el rol del usuario sea exactamente `'repartidor'`

---

## 📚 Referencias

- **Historia de Usuario**: HU18
- **Privilegios**: Tabla de "Privilegios de acceso por perfil"
- **Estados de Pedido**: Modelo `Pedido` en `models.py`
- **Documentación Django**: https://docs.djangoproject.com/

---

## ✅ Checklist de Implementación

- [x] Vista backend creada (`repartidor_pedidos_view`)
- [x] Template HTML diseñado (responsive)
- [x] URL configurada (`/repartidor/pedidos/`)
- [x] Navegación actualizada (menú con "Mis Entregas")
- [x] Redirección automática en login
- [x] Validaciones de seguridad implementadas
- [x] Actualización de estados funcional
- [x] Timestamps registrados correctamente
- [x] Estadísticas calculadas
- [x] Historial de entregas recientes
- [x] Diseño mobile-friendly
- [x] Documentación completada

---

## 👥 Contacto

Para preguntas o mejoras, contactar al equipo de desarrollo de CosmoFood.

**Última actualización**: 3 de noviembre de 2025
