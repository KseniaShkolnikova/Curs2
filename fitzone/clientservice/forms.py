from multiprocessing import AuthenticationError
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from .models import UserProfiles

class RegistrationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя.
    Использует email в качестве имени пользователя и автоматически добавляет пользователя в группу 'Клиент'.
    """
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
        """Инициализация формы - скрываем поле username"""
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['username'].required = False

    def clean_email(self):
        """Валидация уникальности email"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        """Сохранение пользователя с настройкой дополнительных параметров"""
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            UserProfiles.objects.get_or_create(
                user=user, 
                defaults={'theme': False}
            )
            client_group, created = Group.objects.get_or_create(name='Клиент')
            user.groups.add(client_group)
            
        return user


class UserProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя.
    Включает валидацию полей имени и обработку загрузки аватара.
    """
    theme = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'theme-checkbox',
        })
    )
    
    class Meta:
        model = UserProfiles
        fields = ['firstname', 'lastname', 'middlename', 'gender', 'theme', 'avatar']
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
                'style': 'display: none;',
                'accept': 'image/*'
            })
        }

    def clean(self):
        """Валидация формы - проверка согласованности полей имени"""
        cleaned_data = super().clean()
        firstname = cleaned_data.get('firstname')
        lastname = cleaned_data.get('lastname')
        
        if firstname and not lastname:
            raise ValidationError('Если указано имя, должна быть указана и фамилия')
        if lastname and not firstname:
            raise ValidationError('Если указана фамилия, должно быть указано и имя')
            
        return cleaned_data

    def save(self, commit=True):
        """Сохранение профиля с обработкой аватара"""
        instance = super().save(commit=False)
        
        if 'avatar' in self.changed_data and instance.avatar:
            # Логика ресайза аватара может быть добавлена здесь
            pass
            
        if commit:
            instance.save()
        return instance


class LoginForm(AuthenticationForm):
    """
    Форма входа в систему с поддержкой аутентификации по email.
    """
    username = forms.CharField(
        label='Электронная почта',
        widget=forms.TextInput(attrs={
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

    def clean(self):
        """Валидация формы с попыткой аутентификации по email"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        
        if username:
            try:
                user_by_email = User.objects.get(email=username)
                # Дополнительная логика аутентификации по email может быть добавлена здесь
            except User.DoesNotExist:
                pass  # Игнорируем, будет стандартная аутентификация по username
            
        return cleaned_data