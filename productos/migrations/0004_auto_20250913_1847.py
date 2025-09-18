# Generated manually
from django.db import migrations, models


def convert_decimal_to_string(apps, schema_editor):
    """Convierte valores decimales existentes a string"""
    Producto = apps.get_model('productos', 'Producto')
    for producto in Producto.objects.all():
        if producto.precio_oferta is not None:
            # Convierte el decimal a string manteniendo el formato
            producto.precio_oferta = str(producto.precio_oferta)
            producto.save()


def convert_string_to_decimal(apps, schema_editor):
    """Función reversa: convierte string de vuelta a decimal"""
    Producto = apps.get_model('productos', 'Producto')
    from decimal import Decimal, InvalidOperation
    for producto in Producto.objects.all():
        if producto.precio_oferta:
            try:
                producto.precio_oferta = Decimal(str(producto.precio_oferta))
                producto.save()
            except (InvalidOperation, ValueError):
                producto.precio_oferta = None
                producto.save()


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0003_remove_itemcarrito_unique_carrito_producto_and_more'),  # Cambia por tu última migración
    ]

    operations = [
        # Paso 1: Cambiar los datos existentes a string
        migrations.RunPython(convert_decimal_to_string, convert_string_to_decimal),

        # Paso 2: Cambiar el tipo de campo
        migrations.AlterField(
            model_name='producto',
            name='precio_oferta',
            field=models.CharField(max_length=20, null=True, blank=True, help_text="Precio de oferta como texto"),
        ),
    ]