from django import template
from ..models import Carrito

register = template.Library()


@register.simple_tag
def carrito_items_count(user):
    """Retorna el número de items en el carrito del usuario"""
    if not user.is_authenticated:
        return 0

    try:
        carrito = user.carrito
        return carrito.total_items()
    except Carrito.DoesNotExist:
        return 0


@register.simple_tag
def carrito_total_precio(user):
    """Retorna el precio total del carrito del usuario"""
    if not user.is_authenticated:
        return 0

    try:
        carrito = user.carrito
        return carrito.total_precio()
    except Carrito.DoesNotExist:
        return 0