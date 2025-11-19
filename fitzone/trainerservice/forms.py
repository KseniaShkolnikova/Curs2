from django import forms
from clientservice.models import TrainingPlans

class TrainingPlanForm(forms.ModelForm):
    class Meta:
        model = TrainingPlans
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название тренировочного плана'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Подробное описание тренировочного плана...',
                'rows': 6
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            })
        }
        labels = {
            'name': 'Название плана',
            'description': 'Описание',
            'is_active': 'Активный план'
        }

class TrainingPlanEditForm(forms.ModelForm):
    class Meta:
        model = TrainingPlans
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название тренировочного плана'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Подробное описание тренировочного плана...',
                'rows': 6
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            })
        }
        labels = {
            'name': 'Название плана',
            'description': 'Описание',
            'is_active': 'Активный план'
        }