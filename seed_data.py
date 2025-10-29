import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cosmofood.settings')
django.setup()

from django.contrib.auth.models import User
from faker import Faker
from core.models import (
    Category, Product, Cart, CartItem, Order, OrderItem,
    Review, Wishlist, Coupon, ShippingAddress, Contact
)

fake = Faker('es_ES')

def clear_data():
    """Limpiar datos existentes"""
    print("🗑️  Limpiando datos existentes...")
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    CartItem.objects.all().delete()
    Cart.objects.all().delete()
    Review.objects.all().delete()
    Wishlist.objects.all().delete()
    ShippingAddress.objects.all().delete()
    Contact.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Coupon.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    print("✅ Datos limpiados")

def create_users(count=20):
    """Crear usuarios"""
    print(f"👤 Creando {count} usuarios...")
    users = []
    
    # Crear superusuario si no existe
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@cosmofood.com',
            password='admin123'
        )
        users.append(admin)
        print("  ✅ Superusuario creado (admin/admin123)")
    
    for i in range(count):
        username = fake.user_name() + str(i)
        user = User.objects.create_user(
            username=username,
            email=fake.email(),
            password='password123',
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        users.append(user)
    
    print(f"✅ {len(users)} usuarios creados")
    return users

def create_categories():
    """Crear categorías"""
    print("📁 Creando categorías...")
    categories_data = [
        {'name': 'Frutas Frescas', 'description': 'Frutas frescas de temporada'},
        {'name': 'Verduras', 'description': 'Verduras orgánicas y frescas'},
        {'name': 'Lácteos', 'description': 'Productos lácteos de calidad'},
        {'name': 'Carnes', 'description': 'Carnes frescas y embutidos'},
        {'name': 'Panadería', 'description': 'Pan y productos de panadería'},
        {'name': 'Bebidas', 'description': 'Bebidas refrescantes y saludables'},
        {'name': 'Snacks', 'description': 'Snacks y aperitivos'},
        {'name': 'Congelados', 'description': 'Productos congelados'},
        {'name': 'Despensa', 'description': 'Productos de despensa'},
        {'name': 'Orgánicos', 'description': 'Productos 100% orgánicos'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category = Category.objects.create(**cat_data)
        categories.append(category)
    
    print(f"✅ {len(categories)} categorías creadas")
    return categories

def create_products(categories, count=50):
    """Crear productos"""
    print(f"🛍️  Creando {count} productos...")
    
    products_names = [
        'Manzanas', 'Bananas', 'Naranjas', 'Fresas', 'Uvas',
        'Tomates', 'Lechuga', 'Zanahorias', 'Pepinos', 'Pimientos',
        'Leche', 'Yogur', 'Queso', 'Mantequilla', 'Crema',
        'Pollo', 'Carne de Res', 'Cerdo', 'Pescado', 'Jamón',
        'Pan Integral', 'Croissants', 'Galletas', 'Pasteles', 'Donas',
        'Agua Mineral', 'Jugo Naranja', 'Café', 'Té', 'Refresco',
        'Papas Fritas', 'Chocolate', 'Nueces', 'Almendras', 'Palomitas',
        'Pizza Congelada', 'Helado', 'Verduras Congeladas', 'Hamburguesas',
        'Arroz', 'Pasta', 'Aceite', 'Sal', 'Azúcar', 'Harina',
        'Aguacates', 'Mangos', 'Piñas', 'Melones', 'Sandías'
    ]
    
    products = []
    for i in range(count):
        product = Product.objects.create(
            name=random.choice(products_names) + f" {fake.word().capitalize()}",
            description=fake.text(max_nb_chars=200),
            price=Decimal(str(random.uniform(1.99, 99.99))).quantize(Decimal('0.01')),
            category=random.choice(categories),
            stock=random.randint(0, 200),
            is_available=random.choice([True, True, True, False]),
            image=None  # Puedes agregar URLs de imágenes si las tienes
        )
        products.append(product)
    
    print(f"✅ {len(products)} productos creados")
    return products

def create_coupons():
    """Crear cupones"""
    print("🎟️  Creando cupones...")
    coupons_data = [
        {'code': 'WELCOME10', 'discount': 10, 'min_amount': Decimal('20.00')},
        {'code': 'SAVE20', 'discount': 20, 'min_amount': Decimal('50.00')},
        {'code': 'MEGA30', 'discount': 30, 'min_amount': Decimal('100.00')},
        {'code': 'PROMO15', 'discount': 15, 'min_amount': Decimal('30.00')},
        {'code': 'SPECIAL25', 'discount': 25, 'min_amount': Decimal('75.00')},
    ]
    
    coupons = []
    for coupon_data in coupons_data:
        coupon = Coupon.objects.create(
            **coupon_data,
            valid_from=datetime.now() - timedelta(days=10),
            valid_to=datetime.now() + timedelta(days=30),
            is_active=True
        )
        coupons.append(coupon)
    
    print(f"✅ {len(coupons)} cupones creados")
    return coupons

def create_shipping_addresses(users):
    """Crear direcciones de envío"""
    print("📍 Creando direcciones de envío...")
    addresses = []
    
    for user in random.sample(users, min(15, len(users))):
        for _ in range(random.randint(1, 3)):
            address = ShippingAddress.objects.create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                phone=fake.phone_number(),
                address_line1=fake.street_address(),
                address_line2=fake.secondary_address() if random.choice([True, False]) else '',
                city=fake.city(),
                state=fake.state(),
                postal_code=fake.postcode(),
                country='España',
                is_default=random.choice([True, False])
            )
            addresses.append(address)
    
    print(f"✅ {len(addresses)} direcciones creadas")
    return addresses

def create_orders(users, products, coupons, addresses):
    """Crear órdenes"""
    print("📦 Creando órdenes...")
    orders = []
    order_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    for user in random.sample(users, min(15, len(users))):
        num_orders = random.randint(1, 5)
        
        for _ in range(num_orders):
            status = random.choice(order_statuses)
            order = Order.objects.create(
                user=user,
                status=status,
                coupon=random.choice(coupons) if random.choice([True, False, False]) else None,
                shipping_address=random.choice([a for a in addresses if a.user == user]) if addresses else None,
                created_at=fake.date_time_between(start_date='-60d', end_date='now')
            )
            
            # Agregar items a la orden
            num_items = random.randint(1, 6)
            order_total = Decimal('0.00')
            
            for product in random.sample(products, num_items):
                quantity = random.randint(1, 5)
                item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                order_total += product.price * quantity
            
            # Aplicar descuento si hay cupón
            if order.coupon:
                discount = order_total * (order.coupon.discount / Decimal('100'))
                order_total -= discount
            
            order.total_amount = order_total
            order.save()
            orders.append(order)
    
    print(f"✅ {len(orders)} órdenes creadas")
    return orders

def create_carts(users, products):
    """Crear carritos"""
    print("🛒 Creando carritos...")
    carts = []
    
    for user in random.sample(users, min(10, len(users))):
        cart, _ = Cart.objects.get_or_create(user=user)
        
        # Agregar items al carrito
        num_items = random.randint(1, 5)
        for product in random.sample(products, num_items):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=random.randint(1, 3)
            )
        
        carts.append(cart)
    
    print(f"✅ {len(carts)} carritos creados")
    return carts

def create_reviews(users, products):
    """Crear reseñas"""
    print("⭐ Creando reseñas...")
    reviews = []
    
    for _ in range(40):
        user = random.choice(users)
        product = random.choice(products)
        
        # Verificar que no exista ya una reseña
        if not Review.objects.filter(user=user, product=product).exists():
            review = Review.objects.create(
                user=user,
                product=product,
                rating=random.randint(3, 5),
                comment=fake.text(max_nb_chars=150),
                created_at=fake.date_time_between(start_date='-30d', end_date='now')
            )
            reviews.append(review)
    
    print(f"✅ {len(reviews)} reseñas creadas")
    return reviews

def create_wishlists(users, products):
    """Crear listas de deseos"""
    print("💝 Creando listas de deseos...")
    wishlists = []
    
    for user in random.sample(users, min(12, len(users))):
        num_items = random.randint(2, 8)
        for product in random.sample(products, num_items):
            wishlist, created = Wishlist.objects.get_or_create(
                user=user,
                product=product
            )
            if created:
                wishlists.append(wishlist)
    
    print(f"✅ {len(wishlists)} items en wishlist creados")
    return wishlists

def create_contacts():
    """Crear mensajes de contacto"""
    print("📧 Creando mensajes de contacto...")
    contacts = []
    
    for _ in range(15):
        contact = Contact.objects.create(
            name=fake.name(),
            email=fake.email(),
            subject=fake.sentence(),
            message=fake.text(max_nb_chars=300),
            is_read=random.choice([True, False])
        )
        contacts.append(contact)
    
    print(f"✅ {len(contacts)} mensajes de contacto creados")
    return contacts

def main():
    """Ejecutar todos los seeders"""
    print("\n🌟 === INICIANDO SEEDING DE BASE DE DATOS === 🌟\n")
    
    clear_data()
    
    users = create_users(20)
    categories = create_categories()
    products = create_products(categories, 50)
    coupons = create_coupons()
    addresses = create_shipping_addresses(users)
    orders = create_orders(users, products, coupons, addresses)
    carts = create_carts(users, products)
    reviews = create_reviews(users, products)
    wishlists = create_wishlists(users, products)
    contacts = create_contacts()
    
    print("\n✨ === SEEDING COMPLETADO EXITOSAMENTE === ✨")
    print(f"\n📊 Resumen:")
    print(f"   👤 Usuarios: {len(users)}")
    print(f"   📁 Categorías: {len(categories)}")
    print(f"   🛍️  Productos: {len(products)}")
    print(f"   🎟️  Cupones: {len(coupons)}")
    print(f"   📍 Direcciones: {len(addresses)}")
    print(f"   📦 Órdenes: {len(orders)}")
    print(f"   🛒 Carritos: {len(carts)}")
    print(f"   ⭐ Reseñas: {len(reviews)}")
    print(f"   💝 Wishlist: {len(wishlists)}")
    print(f"   📧 Contactos: {len(contacts)}")
    print("\n")

if __name__ == '__main__':
    main()