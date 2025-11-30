import random
from django import template
from django.templatetags.static import static

register = template.Library()

register = template.Library()

FITNESS_IMAGES = [
    "fitness1.jpg",
    "fitness2.jpg", 
    "fitness3.jpg",
    "fitness4.jpg",
]

@register.simple_tag
def random_fitness_image():
    """Возвращает случайную картинку для тренировок"""
    image_name = random.choice(FITNESS_IMAGES)
    return f"/media/img/{image_name}"
