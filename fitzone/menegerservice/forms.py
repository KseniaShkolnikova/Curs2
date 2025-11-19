from django import forms
from datetime import datetime, timedelta
from clientservice.models import SubscriptionTypes

class SubscriptionTypeForm(forms.ModelForm):
    class Meta:
        model = SubscriptionTypes
        fields = [
            'name', 'description', 'price', 'durationdays',
            'gym_access', 'pool_access', 'spa_access',
             'locker_room', 'towel_service',
            'nutrition_consultation',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название абонемента'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Описание абонемента',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Цена в рублях',
                'min': 0
            }),
            'durationdays': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Продолжительность в днях',
                'min': 1
            }),
        }
    
    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError("Цена должна быть положительным числом")
        return price
    
    def clean_durationdays(self):
        duration = self.cleaned_data['durationdays']
        if duration <= 0:
            raise forms.ValidationError("Продолжительность должна быть положительным числом")
        return duration

class ReportFilterForm(forms.Form):
    REPORT_TYPES = [
        ('combined', 'Общий отчет'),
        ('subscriptions', 'Отчет по абонементам'),
        ('classes', 'Отчет по тренировкам'),
    ]
    
    start_date = forms.DateField(
        label='Дата начала',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input',
            'max': datetime.now().date().isoformat()
        })
    )
    
    end_date = forms.DateField(
        label='Дата окончания',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input',
            'max': datetime.now().date().isoformat()
        })
    )
    
    report_type = forms.ChoiceField(
        label='Тип отчета',
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Дата начала не может быть больше даты окончания")
            
            # Проверяем, что период не больше 1 года
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("Период не может превышать 1 год")
        
        return cleaned_data