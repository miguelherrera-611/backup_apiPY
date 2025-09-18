# Generated manually
from django.db import migrations, models


def convert_precio_decimal_to_string(apps, schema_editor):
    """Convierte valores decimales de precio a string"""
    Producto = apps.get_model('productos', 'Producto')
    for producto in Producto.objects.all():
        if producto.precio is not None:
            # Convierte el decimal a string manteniendo el formato
            producto.precio = str(producto.precio)
            producto.save()


def convert_precio_string_to_decimal(apps, schema_editor):
    """Función reversa: convierte string de vuelta a decimal"""
    Producto = apps.get_model('productos', 'Producto')
    from decimal import Decimal, InvalidOperation
    for producto in Producto.objects.all():
        if producto.precio:
            try:
                producto.precio = Decimal(str(producto.precio))
                producto.save()
            except (InvalidOperation, ValueError):
                # Si no se puede convertir, poner un valor por defecto
                producto.precio = Decimal('0.00')
                producto.save()


class Migration(migrations.Migration):
    dependencies = [
        ('productos', '0004_auto_20250913_1847'),  # Cambia por tu última migración
    ]

    operations = [
        # Paso 1: Cambiar los datos existentes a string
        migrations.RunPython(convert_precio_decimal_to_string, convert_precio_string_to_decimal),

        # Paso 2: Cambiar el tipo de campo
        migrations.AlterField(
            model_name='producto',
            name='precio',
            field=models.CharField(max_length=20, help_text="Precio como texto"),
        ),
    ]