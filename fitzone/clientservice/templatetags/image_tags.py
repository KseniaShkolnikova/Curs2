import random
from django import template
from django.templatetags.static import static

register = template.Library()

# Локальные изображения
FITNESS_IMAGES = [
    "img/fitness1.jpg",
    "img/fitness2.jpg", 
    "img/fitness3.jpg",
    "img/fitness4.jpg",
]

@register.simple_tag
def random_fitness_image():
    """Возвращает случайную картинку для тренировок"""
    return static(random.choice(FITNESS_IMAGES))
