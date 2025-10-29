from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Producto,Repartidor
from django.core.exceptions import ValidationError
import re

# Clases de Tailwind CSS para inputs
TAILWIND_INPUT_CLASSES = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition'
TAILWIND_TEXTAREA_CLASSES = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition'
TAILWIND_SELECT_CLASSES = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition'
TAILWIND_CHECKBOX_CLASSES = 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'

class RegistroForm(UserCreationForm):
    """Formulario de registro de usuarios (HU05)"""
    
    # Nota: Usamos los nombres de campo del modelo Usuario (email, first_name, last_name)
    # pero los etiquetamos como quieras mostrarlos al usuario
    
    email = forms.EmailField(
        required=True,
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'tucorreo@ejemplo.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=150, 
        required=True, 
        label='Nombres',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Ingresa tu nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=150, 
        required=True, 
        label='Apellidos',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Ingresa tu apellido'
        })
    )
    
    telefono = forms.CharField(
        max_length=15, 
        required=False, 
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': '+569 1234 5678'
        })
    )
    
    direccion = forms.CharField(
        required=False, 
        label='Dirección',
        widget=forms.Textarea(attrs={
            'class': TAILWIND_TEXTAREA_CLASSES,
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
                'class': TAILWIND_INPUT_CLASSES, 
                'placeholder': 'Nombre de usuario'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir clases de Tailwind a los campos de contraseña
        self.fields['password1'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASSES, 
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASSES,
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
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Nombre de usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
          label='Contraseña',
          widget=forms.PasswordInput(attrs={
              'class': TAILWIND_INPUT_CLASSES, 
              'placeholder': 'Contraseña'
          })
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
            'first_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'email': forms.EmailInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'telefono': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
            'direccion': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA_CLASSES, 'rows': 3})
        }
        
class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'tucorreo@ejemplo.com'
        }),
        help_text='Ingresa el correo con el que te registraste'
    )

class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Ingresa tu nueva contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Confirma tu nueva contraseña'
        })
    )

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [ 'nombre', 'descripcion', 'precio', 'imagen', 'stock', 'categoria', 'activo', 'en_promocion' ]
        widgets = {
                'nombre': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
                'descripcion': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA_CLASSES, 'rows': 3}),
                'precio': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASSES, 'step': '0.01'}),
                # Nota: El widget para un ImageField/FileField es FileInput
                'imagen': forms.FileInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
                'stock': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASSES}),
                'categoria':forms.Select(attrs={'class': TAILWIND_SELECT_CLASSES}),
                'activo': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX_CLASSES}),
                'en_promocion': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX_CLASSES}),
            }

class RepartidorForm(forms.Form):
    username = forms.CharField(
        label='Nombre de Usuario', required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: juanito_delivery'}) 
    )
    email = forms.EmailField(
        label='Correo Electrónico', required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}) 
    )
    first_name = forms.CharField(
        label='Nombres', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}) 
    )
    last_name = forms.CharField(
        label='Apellidos', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}) 
    )
    telefono = forms.CharField(
        label='Teléfono', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}) 
    )
    # Campos para contraseña
    password = forms.CharField(
        label='Contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        help_text="Dejar en blanco para no cambiar la contraseña existente."
    )
    password_confirm = forms.CharField(
        label='Confirmar Contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    # Campos del Modelo Repartidor
    vehiculo = forms.CharField(
        label='Vehículo', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Moto Honda CB190R'})
    )
    placa_vehiculo = forms.CharField(
        label='Placa Patente', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: ABCD12'}) 
    )
    disponible = forms.BooleanField(
        label='Disponible para entregas', required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}) 
    )

    # Constructor para manejar edición
    def __init__(self, *args, **kwargs):
        instance_usuario = kwargs.pop('instance', None)
        instance_perfil = kwargs.pop('instance_perfil', None)
        super().__init__(*args, **kwargs)

        if instance_usuario: # Editando
            self.fields['username'].initial = instance_usuario.username
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['email'].initial = instance_usuario.email
            self.fields['first_name'].initial = instance_usuario.first_name
            self.fields['last_name'].initial = instance_usuario.last_name
            self.fields['telefono'].initial = instance_usuario.telefono
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False

            if instance_perfil:
                self.fields['vehiculo'].initial = instance_perfil.vehiculo
                self.fields['placa_vehiculo'].initial = instance_perfil.placa_vehiculo
                self.fields['disponible'].initial = instance_perfil.disponible
        else: # Creando
             self.fields['password'].required = True
             self.fields['password_confirm'].required = True

    # Validación contraseñas
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password != password_confirm:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
        return cleaned_data

    # Validación username único (al crear)
    def clean_username(self):
        username = self.cleaned_data['username']
        if not self.initial and Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    # Validación email único
    def clean_email(self):
        email = self.cleaned_data['email']
        username = self.cleaned_data.get('username')
        query = Usuario.objects.filter(email=email)
        if self.initial:
            query = query.exclude(username=username)
        if query.exists():
             raise forms.ValidationError("Este correo electrónico ya está registrado por otro usuario.")
        return email