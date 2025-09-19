# test_recovery_email.py
# Crear este archivo en la raíz del proyecto (mismo nivel que manage.py)

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')
django.setup()

from django.contrib.auth.models import User
from productos.models import TokenRecuperacion
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings


def test_user_recovery():
    """Probar recuperación con un usuario real"""
    print("🧪 Probando recuperación de contraseña...")

    # Buscar usuarios existentes
    users = User.objects.all()
    print(f"📊 Usuarios en la BD: {users.count()}")

    for user in users:
        print(f"  - {user.username} | Email: '{user.email}' | Activo: {user.is_active}")

    if not users.exists():
        print("⚠️ No hay usuarios. Creando usuario de prueba...")
        user = User.objects.create_user(
            username='test_recovery',
            email='gamerly9060@gmail.com',  # TU EMAIL REAL AQUÍ
            password='test123456',
            first_name='Usuario',
            last_name='Prueba'
        )
        print(f"✅ Usuario creado: {user.username}")
    else:
        user = users.first()
        if not user.email:
            print(f"⚠️ Usuario {user.username} no tiene email. Agregando...")
            user.email = 'gamerly9060@gmail.com'  # TU EMAIL REAL AQUÍ
            user.save()
            print(f"✅ Email agregado al usuario: {user.username}")

    print(f"\n🎯 Probando con usuario: {user.username} - {user.email}")

    # Crear token
    try:
        token_obj = TokenRecuperacion.crear_token(user)
        print(f"🔑 Token creado: {token_obj.token}")
    except Exception as e:
        print(f"❌ Error creando token: {e}")
        return False

    # Crear contexto
    context = {
        'user': user,
        'domain': 'localhost:8000',
        'site_name': 'GAMERLY',
        'token': token_obj.token,
        'protocol': 'http',
    }

    print(f"🌐 Contexto del email: {context}")

    # Renderizar template
    try:
        email_body = render_to_string('auth/email_recuperacion.html', context)
        print("✅ Template renderizado OK")
        print(f"📄 Primeros 100 caracteres: {email_body[:100]}...")
    except Exception as e:
        print(f"❌ Error en template: {e}")
        print("🔍 Verifica que existe: productos/templates/auth/email_recuperacion.html")
        return False

    # Enviar email
    try:
        print(f"📤 Enviando email desde: {settings.EMAIL_HOST_USER}")
        print(f"📧 Enviando email a: {user.email}")

        result = send_mail(
            subject='🧪 GAMERLY - Test Recuperación Específico',
            message='Test de recuperación de contraseña desde script.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=email_body,
            fail_silently=False,
        )
        print(f"✅ Email enviado! Resultado: {result}")
        print(f"📧 Revisa el email: {user.email}")

        # Mostrar URL de recuperación
        recovery_url = f"http://localhost:8000/confirmar-password/{token_obj.token}/"
        print(f"🔗 URL de recuperación: {recovery_url}")

        return True

    except Exception as e:
        print(f"❌ Error enviando: {type(e).__name__}: {e}")
        return False


def check_email_config():
    """Verificar configuración de email"""
    print("\n🔧 Verificando configuración de email...")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}")


def check_template_exists():
    """Verificar que el template existe"""
    import os
    template_path = os.path.join(settings.BASE_DIR, 'productos', 'templates', 'auth', 'email_recuperacion.html')
    print(f"\n📄 Verificando template en: {template_path}")

    if os.path.exists(template_path):
        print("✅ Template existe")
        # Leer primeras líneas
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()[:200]
            print(f"📝 Primeros 200 caracteres:\n{content}...")
    else:
        print("❌ Template NO existe")
        print("🔍 Verifica la ruta y que el archivo esté creado")


if __name__ == "__main__":
    print("🎮 GAMERLY - Test de Recuperación de Contraseña")
    print("=" * 60)

    # Verificar configuración
    check_email_config()

    # Verificar template
    check_template_exists()

    # Ejecutar prueba
    print("\n" + "=" * 60)
    success = test_user_recovery()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completado! Revisa tu email.")
    else:
        print("❌ Test falló. Revisa los errores arriba.")

    print("\n💡 Si funciona este script pero no el formulario web,")
    print("   el problema está en la vista de Django, no en la configuración de email.")