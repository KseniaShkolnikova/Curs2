from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from PIL import Image
import os

# SUMMARY: Модели данных для системы управления фитнес-клубом
# ОСНОВНОЕ НАЗНАЧЕНИЕ: Определение структуры данных и бизнес-логики приложения
# ПРИНЦИП РАБОТЫ: Каждая модель представляет таблицу в БД с соответствующими полями и методами
# ОСОБЕННОСТИ: Включает профили пользователей, абонементы, тренировки, платежи и логирование действий

class UserProfiles(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
        ('O', 'Другой'),
    ]
    
    firstname = models.CharField(max_length=255, null=True, blank=True)
    lastname = models.CharField(max_length=255, null=True, blank=True)
    middlename = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id', related_name='userprofile')
    theme = models.BooleanField(default=False, null=False)
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        null=True, 
        blank=True, 
        verbose_name='Аватар'
    )
    
    class Meta:
        db_table = 'UserProfiles'

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    @property
    def full_name(self):
        parts = [self.lastname, self.firstname, self.middlename]
        return ' '.join(part for part in parts if part).strip()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar:
            self.resize_avatar()
    
    def resize_avatar(self):
        avatar_path = self.avatar.path
        if os.path.exists(avatar_path):
            try:
                with Image.open(avatar_path) as img:
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    max_size = (400, 400)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(avatar_path, 'JPEG', quality=85, optimize=True)
            except Exception as e:
                print(f"Error resizing avatar: {e}")


class SubscriptionTypes(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    durationdays = models.IntegerField(null=False)
    
    gym_access = models.BooleanField(default=False, verbose_name='Тренажерный зал')
    pool_access = models.BooleanField(default=False, verbose_name='Бассейн')
    spa_access = models.BooleanField(default=False, verbose_name='СПА зона')
    locker_room = models.BooleanField(default=False, verbose_name='Раздевалка')
    towel_service = models.BooleanField(default=False, verbose_name='Полотенце')
    nutrition_consultation = models.BooleanField(default=False, verbose_name='Консультация по питанию')

    class Meta:
        db_table = 'SubscriptionTypes'

    def __str__(self):
        return self.name

    def get_included_services(self):
        services = []
        if self.gym_access:
            services.append('Тренажерный зал')
        if self.pool_access:
            services.append('Бассейн')
        if self.spa_access:
            services.append('СПА зона')
        if self.locker_room:
            services.append('Раздевалка')
        if self.towel_service:
            services.append('Полотенце')
        if self.nutrition_consultation:
            services.append('Консультация по питанию')
        return services

    def get_service_icons(self):
        icons = {
            'gym_access': 'fas fa-dumbbell',
            'pool_access': 'fas fa-swimming-pool',
            'spa_access': 'fas fa-spa',
            'locker_room': 'fas fa-door-open',
            'towel_service': 'fas fa-tshirt',
            'nutrition_consultation': 'fas fa-apple-alt',
        }
        
        active_icons = []
        for field, icon in icons.items():
            if getattr(self, field):
                active_icons.append(icon)
        return active_icons


class Subscriptions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    subscriptiontype = models.ForeignKey(SubscriptionTypes, on_delete=models.CASCADE, db_column='subscriptiontype_id')
    startdate = models.DateField(null=False)
    is_active = models.BooleanField(default=True, null=False)

    class Meta:
        db_table = 'Subscriptions'

    def __str__(self):
        return f"{self.user.email} - {self.subscriptiontype.name}"


class TrainingPlans(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trainer_plans', db_column='trainer_id')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_plans', db_column='client_id')
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=False)
    is_active = models.BooleanField(default=True, null=False)

    class Meta:
        db_table = 'TrainingPlans'

    def __str__(self):
        return self.name


class TrainerSpecializations(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, db_column='trainer_id')
    specialization = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = 'TrainerSpecializations'
        unique_together = ('trainer', 'specialization')

    def __str__(self):
        return f"{self.trainer.email} - {self.specialization}"


class Classes(models.Model):
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, db_column='trainer_id')
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=False)
    starttime = models.DateTimeField(null=False)
    endtime = models.DateTimeField(null=False)
    maxclient = models.IntegerField(null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    is_active = models.BooleanField(default=True, null=False)

    class Meta:
        db_table = 'Classes'

    def __str__(self):
        return self.name


class ClassClient(models.Model):
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE, db_column='class_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    amount = models.IntegerField(null=False)
    is_active = models.BooleanField(default=True, null=False)

    class Meta:
        db_table = 'ClassClient'
        unique_together = ('class_id', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.class_id.name}"


class UserActionsLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Создание'),
        ('UPDATE', 'Обновление'), 
        ('DELETE', 'Удаление'),
        ('LOGIN', 'Вход в систему'),
        ('LOGOUT', 'Выход из системы'),
        ('SYSTEM', 'Системное действие'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, db_column='user_id')
    action = models.CharField(max_length=255, null=False)
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES, default='SYSTEM')
    model_name = models.CharField(max_length=100, null=True, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    user_full_name = models.CharField(max_length=255, null=True, blank=True)
    actiondate = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        db_table = 'UserActionsLog'
        ordering = ['-actiondate']

    def __str__(self):
        return f"{self.action} at {self.actiondate}"

    def save(self, *args, **kwargs):
        if self.user and self.user.userprofile:
            self.user_full_name = self.user.userprofile.full_name
        elif self.user:
            self.user_full_name = self.user.username
        super().save(*args, **kwargs)


class Payments(models.Model):
    subscription = models.ForeignKey(Subscriptions, on_delete=models.CASCADE, null=True, blank=True, db_column='subscription_id')
    classclient = models.ForeignKey(ClassClient, on_delete=models.CASCADE, null=True, blank=True, db_column='classclient_id')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    paymentdate = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        db_table = 'Payments'
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(subscription__isnull=False) & models.Q(classclient__isnull=True)) |
                    (models.Q(subscription__isnull=True) & models.Q(classclient__isnull=False))
                ),
                name='check_payment_type'
            )
        ]

    def __str__(self):
        return f"Payment {self.price} at {self.paymentdate}"