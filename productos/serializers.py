from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Producto, Categoria, PerfilUsuario


class CategoriaSerializer(serializers.ModelSerializer):
    productos_count = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'activo', 'fecha_creacion', 'productos_count']
        read_only_fields = ['fecha_creacion']

    def get_productos_count(self, obj):
        return obj.productos.filter(estado='disponible').count()


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    precio_actual = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    descuento_porcentaje = serializers.IntegerField(read_only=True)
    en_stock = serializers.BooleanField(read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio', 'precio_oferta',
            'precio_actual', 'descuento_porcentaje', 'categoria', 'categoria_nombre',
            'stock', 'imagen', 'estado', 'destacado', 'en_stock',
            'fecha_creacion', 'fecha_actualizacion', 'creado_por_nombre'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'creado_por']

    def create(self, validated_data):
        validated_data['creado_por'] = self.context['request'].user
        return super().create(validated_data)


class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de productos"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    precio_actual = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    descuento_porcentaje = serializers.IntegerField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio', 'precio_oferta', 'precio_actual',
            'descuento_porcentaje', 'categoria_nombre', 'imagen',
            'estado', 'destacado', 'stock'
        ]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    email = serializers.CharField(source='usuario.email', read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = [
            'id', 'username', 'email', 'full_name', 'tipo_usuario',
            'telefono', 'direccion', 'fecha_nacimiento', 'avatar',
            'fecha_registro'
        ]
        read_only_fields = ['fecha_registro']

    def get_full_name(self, obj):
        return f"{obj.usuario.first_name} {obj.usuario.last_name}".strip()


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user