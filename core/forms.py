from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Producto
from django.core.exceptions import ValidationError
import re

class RegistroForm(UserCreationForm):
    """Formulario de registro de usuarios (HU05)"""
    
    # Nota: Usamos los nombres de campo del modelo Usuario (email, first_name, last_name)
    # pero los etiquetamos como quieras mostrarlos al usuario
    
    email = forms.EmailField(
        required=True,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'tucorreo@ejemplo.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=150, 
        required=True, 
        label='Nombres',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=150, 
        required=True, 
        label='Apellidos',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu apellido'
        })
    )
    
    telefono = forms.CharField(
        max_length=15, 
        required=False, 
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+569 1234 5678'
        })
    )
    
    direccion = forms.CharField(
        required=False, 
        label='Dirección',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ingresa tu dirección (opcional)'
        })
    )
    
    class Meta:
        model = Usuario
        # IMPORTANTE: Estos nombres DEBEN coincidir con los campos del modelo Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'telefono', 'direccion', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre de usuario'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir clases de Bootstrap a los campos de contraseña
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        
        # Personalizar mensajes de ayuda
        self.fields['password1'].help_text = 'Mínimo 8 caracteres, debe contener una mayúscula y un número'
    
    def clean_email(self):
        """Validar que el email no esté registrado (HU05)"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_password1(self):
        """Validar requisitos de contraseña: mínimo 8 caracteres, una mayúscula y un número (HU05)"""
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        return password
    
    def save(self, commit=True):
        """Guardar usuario con rol de cliente por defecto"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.rol = 'cliente'  # Por defecto todos son clientes
        
        if commit:
            user.save()
        return user
        
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
          label='Contraseña',
          widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
      
    )
    
class PerfilForm(forms.ModelForm):
      
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion']
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        
class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(
        label = 'Correo Electrónico',
        widget= forms.EmailInput(attrs={'class': 'form-control'})
    )

class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña'
        })
    )

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [ 'nombre', 'descripcion', 'precio', 'imagen', 'stock', 'categoria', 'activo' ]
        widgets = {
                'nombre': forms.TextInput(attrs={'class': 'form-control'}),
                'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
                # Nota: El widget para un ImageField/FileField es FileInput, no FileField
                'imagen': forms.FileInput(attrs={'class':'form-control'}),
                'stock': forms.NumberInput(attrs={'class': 'form-control'}),
                'categoria':forms.Select(attrs={'class': 'form-control'}),
                'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }
    