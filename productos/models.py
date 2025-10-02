from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('agotado', 'Agotado'),
        ('descontinuado', 'Descontinuado'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name="Precio Oferta")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

    def precio_actual(self):
        """Retorna el precio con oferta si existe, sino el precio normal"""
        if self.precio_oferta:
            return self.precio_oferta
        return self.precio

    @property
    def precio_formateado(self):
        """Retorna el precio en formato colombiano: $129.000 COL"""
        precio = self.precio_actual()
        return f"${int(precio):,} COL".replace(',', '.')

    @property
    def precio_formateado_sin_col(self):
        """Retorna solo el número formateado: $129.000"""
        precio = self.precio_actual()
        return f"${int(precio):,}".replace(',', '.')

    def precio_actual_str(self):
        """Retorna el precio actual como string para mostrar - COMPATIBILIDAD"""
        return str(self.precio_actual())

    def descuento_porcentaje(self):
        """Calcula el porcentaje de descuento si hay precio de oferta"""
        if self.precio_oferta and self.precio_oferta < self.precio:
            return int(((self.precio - self.precio_oferta) / self.precio) * 100)
        return 0

    def en_stock(self):
        return self.stock > 0 and self.estado == 'disponible'


class PerfilUsuario(models.Model):
    TIPOS_USUARIO = [
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=10, choices=TIPOS_USUARIO, default='cliente')
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_usuario_display()}"

    def es_admin(self):
        return self.tipo_usuario == 'admin' or self.usuario.is_superuser


class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    def total_items(self):
        """Retorna el número total de items en el carrito"""
        return self.items.aggregate(total=models.Sum('cantidad'))['total'] or 0

    def total_precio(self):
        """Calcula el precio total del carrito"""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.subtotal()
        return total

    def limpiar_carrito(self):
        """Elimina todos los items del carrito"""
        self.items.all().delete()


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('carrito', 'producto')
        verbose_name = "Item del Carrito"
        verbose_name_plural = "Items del Carrito"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

    def subtotal(self):
        """Calcula el subtotal del item (precio x cantidad)"""
        precio_actual = self.producto.precio_actual()
        return precio_actual * self.cantidad

    def puede_aumentar_cantidad(self):
        """Verifica si se puede aumentar la cantidad basado en el stock"""
        return self.cantidad < self.producto.stock


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


# Señales para crear perfil y carrito automáticamente
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def crear_carrito_usuario(sender, instance, created, **kwargs):
    """Crear carrito automáticamente cuando se crea un usuario"""
    if created:
        Carrito.objects.create(usuario=instance)