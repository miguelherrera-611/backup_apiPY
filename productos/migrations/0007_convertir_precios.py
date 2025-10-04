from django.db import migrations
from decimal import Decimal


def limpiar_precios(apps, schema_editor):
    Producto = apps.get_model('productos', 'Producto')

    for producto in Producto.objects.all():
        # Convertir "645,000 COL" o "$129,000 COL" a número
        precio_str = str(producto.precio)

        # Limpiar el string - quitar todo excepto números
        precio_limpio = ''.join(c for c in precio_str if c.isdigit())

        if precio_limpio:
            try:
                producto.precio = Decimal(precio_limpio)
            except:
                producto.precio = Decimal('0')
        else:
            producto.precio = Decimal('0')

        # Lo mismo para precio_oferta si existe
        if producto.precio_oferta:
            precio_oferta_str = str(producto.precio_oferta)
            precio_oferta_limpio = ''.join(c for c in precio_oferta_str if c.isdigit())

            if precio_oferta_limpio:
                try:
                    producto.precio_oferta = Decimal(precio_oferta_limpio)
                except:
                    producto.precio_oferta = None
            else:
                producto.precio_oferta = None

        producto.save()
        print(f"Convertido: {producto.nombre} - Precio: {producto.precio}")


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0006_tokenrecuperacion'),
    ]

    operations = [
        migrations.RunPython(limpiar_precios, revertir),
    ]