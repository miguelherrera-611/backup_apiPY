# test_email.py - Crear este archivo en la raíz del proyecto para probar el email

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')
django.setup()

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User


def test_email():
    """Script para probar si el email funciona"""
    print("🧪 Probando configuración de email...")

    try:
        # Email de prueba simple
        send_mail(
            subject='✅ Prueba de Email - GAMERLY',
            message='Si recibes este email, la configuración está funcionando correctamente! 🎮',
            from_email=None,  # Usa DEFAULT_FROM_EMAIL
            recipient_list=['ga60@gmail.com'],  # Cambia por tu email
            fail_silently=False,
        )
        print("✅ Email de prueba enviado exitosamente!")
        print("📧 Revisa tu bandeja de entrada (y spam)")

    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verifica que tengas la contraseña de aplicación correcta en settings.py")
        print("2. Verifica que la verificación en 2 pasos esté activada en Gmail")
        print("3. Revisa la configuración EMAIL_HOST_USER y EMAIL_HOST_PASSWORD")
        print("4. Asegúrate de que el email en recipient_list sea válido")


def test_email_template():
    """Probar el template de email de recuperación"""
    print("\n🎨 Probando template de email...")

    try:
        # Buscar un usuario para la prueba (o crear uno temporal)
        try:
            user = User.objects.first()
            if not user:
                print("⚠️ No hay usuarios en la base de datos. Crea uno primero.")
                return
        except Exception:
            print("⚠️ Error accediendo a la base de datos. ¿Ejecutaste las migraciones?")
            return

        # Simular contexto del email
        context = {
            'user': user,
            'domain': 'localhost:8000',
            'site_name': 'GAMERLY',
            'token': 'token-de-prueba-123',
            'protocol': 'http',
        }

        # Renderizar template
        email_body = render_to_string('auth/email_recuperacion.html', context)

        # Enviar email con template
        send_mail(
            subject='🎮 Prueba de Template - Recuperación GAMERLY',
            message='',
            from_email=None,
            recipient_list=['ga60@gmail.com'],  # Cambia por tu email
            html_message=email_body,
            fail_silently=False,
        )

        print("✅ Email con template enviado exitosamente!")
        print(f"👤 Usuario de prueba: {user.username}")

    except Exception as e:
        print(f"❌ Error enviando email con template: {e}")


if __name__ == "__main__":
    print("🎮 GAMERLY - Prueba de Email")
    print("=" * 40)

    # Probar email básico
    test_email()

    # Probar template
    test_email_template()

    print("\n🎯 Pruebas completadas!")
    print("💡 Si funcionó, ya puedes usar la recuperación por email")
    print("🔧 Si no funcionó, revisa la configuración en settings.py")