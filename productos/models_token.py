from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid


class TokenRecuperacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    def __str__(self):
        return f"Token para {self.usuario.username}"

    def es_valido(self):
        """Verifica si el token es válido (no expirado y no usado)"""
        if self.usado:
            return False
        # Token expira en 1 hora
        expiracion = self.fecha_creacion + timedelta(hours=1)
        return timezone.now() < expiracion

    @classmethod
    def crear_token(cls, usuario):
        """Crea un nuevo token para el usuario"""
        # Eliminar tokens anteriores del usuario
        cls.objects.filter(usuario=usuario).delete()

        # Crear nuevo token
        token = str(uuid.uuid4())
        return cls.objects.create(usuario=usuario, token=token)

    class Meta:
        verbose_name = "Token de Recuperación"
        verbose_name_plural = "Tokens de Recuperación"