import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cosmofood.settings')
django.setup()

from django.core.mail import send_mail

try:
    send_mail(
        subject='Prueba de Email - Cosmofood',
        message='Este es un correo de prueba desde Django.',
        from_email='cosmofood@grivyzom.com',
        recipient_list=['grivyzom@gmail.com'],  # Cambia esto
        fail_silently=False,
    )
    print("✅ Email enviado correctamente!")
except Exception as e:
    print(f"❌ Error al enviar email: {e}")