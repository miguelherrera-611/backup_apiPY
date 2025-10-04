import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')
django.setup()

from productos.models import Producto
from decimal import Decimal

print("Limpiando precios...")

for producto in Producto.objects.all():
    # Limpiar precio
    precio_str = str(producto.precio)
    precio_limpio = ''.join(c for c in precio_str if c.isdigit())

    if precio_limpio:
        producto.precio = Decimal(precio_limpio)
    else:
        producto.precio = Decimal('0')

    # Limpiar precio_oferta
    if producto.precio_oferta:
        precio_oferta_str = str(producto.precio_oferta)
        precio_oferta_limpio = ''.join(c for c in precio_oferta_str if c.isdigit())

        if precio_oferta_limpio:
            producto.precio_oferta = Decimal(precio_oferta_limpio)
        else:
            producto.precio_oferta = None

    producto.save(update_fields=['precio', 'precio_oferta'])
    print(f"✓ {producto.nombre}: ${producto.precio}")

print("\n¡Listo! Precios corregidos.")