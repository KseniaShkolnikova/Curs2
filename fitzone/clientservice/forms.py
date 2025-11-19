from multiprocessing import AuthenticationError
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfiles

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email',
            'id': 'id_email'
        }),
        required=True
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
            'id': 'id_password1'
        }),
        help_text=''
    )
    
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль',
            'id': 'id_password2'
        }),
        help_text=''
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['username'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    theme = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'theme-checkbox',
        })
    )
    
    class Meta:
        model = UserProfiles
        fields = ['firstname', 'lastname', 'middlename', 'gender', 'theme', 'avatar']  # Добавлено avatar
        widgets = {
            'firstname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя'
            }),
            'lastname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите вашу фамилию'
            }),
            'middlename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше отчество'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'avatar': forms.FileInput(attrs={
                'style': 'display: none;',  # Скрываем стандартный input
                'accept': 'image/*'
            })
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(  # ИЗМЕНИТЕ EmailField на CharField
        label='Электронная почта',
        widget=forms.TextInput(attrs={  # И TextInput вместо EmailInput
            'class': 'form-control',
            'placeholder': 'Введите email или имя пользователя',
            'id': 'email',
            'autocomplete': 'email'
        }),
    )
    
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
            'id': 'password',
            'autocomplete': 'current-password'
        }),
    )
    