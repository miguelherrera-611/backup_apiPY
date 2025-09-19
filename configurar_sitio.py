# configurar_sitio.py
# Crear este archivo en la raíz del proyecto y ejecutarlo una sola vez

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')
django.setup()

from django.contrib.sites.models import Site


def configurar_sitio():
    """Configurar el sitio por defecto para desarrollo local"""
    try:
        # Obtener o crear el sitio por defecto
        site, created = Site.objects.get_or_create(pk=1)

        # Configurar dominio correcto para desarrollo
        site.domain = 'localhost:8000'
        site.name = 'GAMERLY Local'
        site.save()

        if created:
            print("✅ Sitio creado correctamente:")
        else:
            print("✅ Sitio actualizado correctamente:")

        print(f"   - ID: {site.id}")
        print(f"   - Dominio: {site.domain}")
        print(f"   - Nombre: {site.name}")

        # Verificar configuración
        print(f"\n🔍 Verificación:")
        print(f"   - El sitio por defecto ahora apunta a: {site.domain}")
        print(f"   - Los emails de recuperación usarán: http://{site.domain}/")

        return True

    except Exception as e:
        print(f"❌ Error configurando sitio: {e}")
        return False


if __name__ == "__main__":
    print("🎮 GAMERLY - Configuración de Sitio")
    print("=" * 50)

    success = configurar_sitio()

    if success:
        print("\n🎉 ¡Configuración completada!")
        print("💡 Ahora los enlaces de recuperación de contraseña apuntarán a localhost:8000")
        print("🧪 Prueba enviando otro email de recuperación para verificar")
    else:
        print("\n❌ Error en la configuración")
        print("🔧 Verifica que las migraciones estén aplicadas: python manage.py migrate")