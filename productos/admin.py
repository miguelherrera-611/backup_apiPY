from django.contrib import admin
from django.utils.html import format_html
from .models import Producto, Categoria, PerfilUsuario, Carrito, ItemCarrito

# Personalización del sitio de administración
admin.site.site_header = "🎮 GAMERLY Administration"
admin.site.site_title = "GAMERLY Admin"
admin.site.index_title = "Panel de Control Gaming"


# CSS y JS globales para todo el admin
class BaseGamingAdmin:
    """Clase base para aplicar estilos gaming a todas las páginas del admin"""

    class Media:
        css = {
            'all': (
                'admin/css/admin.css',
                'admin/css/history-gaming.css',
            )
        }
        js = ('admin/js/gaming-admin.js',)


@admin.register(Categoria)
class CategoriaAdmin(BaseGamingAdmin, admin.ModelAdmin):
    list_display = ['nombre_con_emoji', 'descripcion_corta', 'estado_visual', 'productos_count', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre']

    def nombre_con_emoji(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #8b5cf6;">🏷️ {}</span>',
            obj.nombre
        )

    nombre_con_emoji.short_description = 'Categoría'

    def descripcion_corta(self, obj):
        if obj.descripcion:
            desc = obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
            return format_html('<span style="color: #c084fc;">{}</span>', desc)
        return format_html('<span style="color: #6b7280; font-style: italic;">Sin descripción</span>')

    descripcion_corta.short_description = 'Descripción'

    def estado_visual(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background: linear-gradient(45deg, #10b981, #059669); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">✅ Activa</span>'
            )
        else:
            return format_html(
                '<span style="background: linear-gradient(45deg, #ef4444, #dc2626); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">❌ Inactiva</span>'
            )

    estado_visual.short_description = 'Estado'

    def productos_count(self, obj):
        count = obj.productos.count()
        if count > 0:
            return format_html(
                '<span style="background: #8b5cf6; color: white; padding: 2px 8px; border-radius: 10px; font-weight: bold;">📦 {}</span>',
                count
            )
        return format_html('<span style="color: #6b7280;">Sin productos</span>')

    productos_count.short_description = 'Productos'


@admin.register(Producto)
class ProductoAdmin(BaseGamingAdmin, admin.ModelAdmin):
    list_display = ['imagen_miniatura', 'nombre_con_emoji', 'categoria_visual', 'precio', 'precio_visual', 'stock',
                    'stock_visual', 'estado_badge', 'destacado', 'destacado_star']
    list_filter = ['categoria', 'estado', 'destacado', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['precio', 'stock', 'destacado']
    readonly_fields = ['imagen_preview', 'fecha_creacion', 'fecha_actualizacion']

    fieldsets = (
        ('🎮 Información Básica', {
            'fields': ('nombre', 'descripcion', 'categoria'),
            'classes': ('gaming-fieldset',)
        }),
        ('💰 Precios y Stock', {
            'fields': ('precio', 'precio_oferta', 'stock'),
            'classes': ('gaming-fieldset',)
        }),
        ('🖼️ Imagen', {
            'fields': ('imagen', 'imagen_preview'),
            'classes': ('gaming-fieldset',)
        }),
        ('⚙️ Configuración', {
            'fields': ('estado', 'destacado'),
            'classes': ('gaming-fieldset',)
        }),
        ('📅 Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'creado_por'),
            'classes': ('gaming-fieldset collapse',)
        }),
    )

    def imagen_miniatura(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 2px solid #8b5cf6;" />',
                obj.imagen.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: linear-gradient(45deg, #374151, #4b5563); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9ca3af;">📷</div>'
        )

    imagen_miniatura.short_description = 'Imagen'

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 10px; border: 2px solid #8b5cf6;" />',
                obj.imagen.url
            )
        return "No hay imagen"

    imagen_preview.short_description = 'Vista Previa'

    def nombre_con_emoji(self, obj):
        emoji = "⭐" if obj.destacado else "📦"
        return format_html(
            '<span style="font-weight: bold; color: #8b5cf6;">{} {}</span>',
            emoji, obj.nombre
        )

    nombre_con_emoji.short_description = 'Producto'

    def categoria_visual(self, obj):
        return format_html(
            '<span style="background: linear-gradient(45deg, #8b5cf6, #a855f7); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">🏷️ {}</span>',
            obj.categoria.nombre
        )

    categoria_visual.short_description = 'Categoría'

    def precio_visual(self, obj):
        if obj.precio_oferta:
            return format_html(
                '<div>'
                '<span style="text-decoration: line-through; color: #6b7280;">${}</span><br>'
                '<span style="font-weight: bold; color: #10b981; font-size: 1.1em;">${}</span>'
                '<span style="background: #ef4444; color: white; padding: 2px 6px; border-radius: 8px; font-size: 0.8em; margin-left: 5px;">OFERTA</span>'
                '</div>',
                obj.precio, obj.precio_oferta
            )
        else:
            return format_html(
                '<span style="font-weight: bold; color: #8b5cf6; font-size: 1.1em;">${}</span>',
                obj.precio
            )

    precio_visual.short_description = 'Precio Visual'

    def stock_visual(self, obj):
        if obj.stock > 10:
            color, icon = "#10b981", "✅"
        elif obj.stock > 0:
            color, icon = "#f59e0b", "⚠️"
        else:
            color, icon = "#ef4444", "❌"

        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">{} {}</span>',
            color, icon, obj.stock
        )

    stock_visual.short_description = 'Stock Visual'

    def estado_badge(self, obj):
        colores = {'disponible': '#10b981', 'agotado': '#f59e0b', 'descontinuado': '#ef4444'}
        iconos = {'disponible': '✅', 'agotado': '⚠️', 'descontinuado': '❌'}

        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">{} {}</span>',
            colores.get(obj.estado, '#6b7280'),
            iconos.get(obj.estado, '❓'),
            obj.get_estado_display()
        )

    estado_badge.short_description = 'Estado'

    def destacado_star(self, obj):
        if obj.destacado:
            return format_html(
                '<span style="color: #f59e0b; font-size: 1.5em; text-shadow: 0 0 10px #f59e0b;">⭐</span>')
        return format_html('<span style="color: #6b7280;">☆</span>')

    destacado_star.short_description = 'Destacado Visual'

    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(BaseGamingAdmin, admin.ModelAdmin):
    list_display = ['usuario_info', 'tipo_badge', 'telefono', 'estado_visual', 'fecha_registro']
    list_filter = ['tipo_usuario', 'fecha_registro']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['fecha_registro']

    fieldsets = (
        ('👤 Información de Usuario', {
            'fields': ('usuario', 'tipo_usuario'),
        }),
        ('📞 Contacto', {
            'fields': ('telefono', 'direccion'),
        }),
        ('👨‍💼 Información Personal', {
            'fields': ('fecha_nacimiento', 'avatar'),
        }),
        ('⚙️ Configuración', {
            'fields': ('activo', 'fecha_registro'),
        }),
    )

    def usuario_info(self, obj):
        inicial = obj.usuario.first_name[0].upper() if obj.usuario.first_name else obj.usuario.username[0].upper()
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 40px; height: 40px; background: linear-gradient(45deg, #8b5cf6, #a855f7); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; color: white; font-weight: bold;">{}</div>'
            '<div><div style="font-weight: bold; color: #8b5cf6;">{}</div><div style="color: #c084fc; font-size: 0.9em;">{}</div></div>'
            '</div>',
            inicial, obj.usuario.get_full_name() or obj.usuario.username, obj.usuario.email
        )

    usuario_info.short_description = 'Usuario'

    def tipo_badge(self, obj):
        if obj.tipo_usuario == 'admin':
            return format_html(
                '<span style="background: linear-gradient(45deg, #ef4444, #dc2626); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">👑 Admin</span>')
        else:
            return format_html(
                '<span style="background: linear-gradient(45deg, #8b5cf6, #7c3aed); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">👤 Cliente</span>')

    tipo_badge.short_description = 'Tipo'

    def estado_visual(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background: linear-gradient(45deg, #10b981, #059669); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">✅ Activo</span>')
        else:
            return format_html(
                '<span style="background: linear-gradient(45deg, #ef4444, #dc2626); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">❌ Inactivo</span>')

    estado_visual.short_description = 'Estado'


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    readonly_fields = ['fecha_agregado', 'subtotal_visual']
    fields = ['producto', 'cantidad', 'subtotal_visual', 'fecha_agregado']

    def subtotal_visual(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #10b981; font-size: 1.1em;">${}</span>',
            obj.subtotal()
        )

    subtotal_visual.short_description = 'Subtotal'


@admin.register(Carrito)
class CarritoAdmin(BaseGamingAdmin, admin.ModelAdmin):
    list_display = ['usuario_info', 'items_count', 'total_visual', 'fecha_actualizacion']
    list_filter = ['fecha_creacion', 'fecha_actualizacion']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    inlines = [ItemCarritoInline]

    def usuario_info(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 40px; height: 40px; background: linear-gradient(45deg, #8b5cf6, #a855f7); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; color: white; font-weight: bold;">🛒</div>'
            '<div><div style="font-weight: bold; color: #8b5cf6;">{}</div><div style="color: #c084fc; font-size: 0.9em;">{}</div></div>'
            '</div>',
            obj.usuario.get_full_name() or obj.usuario.username, obj.usuario.email
        )

    usuario_info.short_description = 'Usuario'

    def items_count(self, obj):
        count = obj.total_items()
        return format_html(
            '<span style="background: #8b5cf6; color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold;">📦 {} items</span>',
            count
        )

    items_count.short_description = 'Items'

    def total_visual(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #10b981; font-size: 1.2em;">${}</span>',
            obj.total_precio()
        )

    total_visual.short_description = 'Total'


@admin.register(ItemCarrito)
class ItemCarritoAdmin(BaseGamingAdmin, admin.ModelAdmin):
    list_display = ['carrito_info', 'producto_info', 'cantidad', 'subtotal_visual', 'fecha_agregado']
    list_filter = ['fecha_agregado', 'producto__categoria']
    search_fields = ['carrito__usuario__username', 'producto__nombre']
    readonly_fields = ['fecha_agregado', 'subtotal_visual']

    def carrito_info(self, obj):
        return format_html(
            '<span style="color: #8b5cf6; font-weight: bold;">🛒 {}</span>',
            obj.carrito.usuario.username
        )

    carrito_info.short_description = 'Carrito'

    def producto_info(self, obj):
        return format_html(
            '<span style="color: #10b981; font-weight: bold;">📦 {}</span>',
            obj.producto.nombre
        )

    producto_info.short_description = 'Producto'

    def subtotal_visual(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #10b981; font-size: 1.1em;">${}</span>',
            obj.subtotal()
        )

    subtotal_visual.short_description = 'Subtotal'


# Configuración global del admin para aplicar CSS gaming a todas las páginas
def add_gaming_css_to_all_admin_classes():
    """Aplica el CSS gaming a todas las clases del admin"""
    for model_admin in admin.site._registry.values():
        if not hasattr(model_admin, 'Media'):
            model_admin.Media = type('Media', (), {})

        if not hasattr(model_admin.Media, 'css'):
            model_admin.Media.css = {}

        if 'all' not in model_admin.Media.css:
            model_admin.Media.css['all'] = []

        # Agregar CSS gaming si no está presente
        css_files = ['admin/css/admin.css', 'admin/css/history-gaming.css']
        for css_file in css_files:
            if css_file not in model_admin.Media.css['all']:
                model_admin.Media.css['all'].append(css_file)


# Aplicar CSS gaming a todas las clases del admin
add_gaming_css_to_all_admin_classes()

# Personalización adicional del sitio admin
admin.site.empty_value_display = '(Sin valor)'
admin.site.enable_nav_sidebar = True


# Configuración de interfaz mejorada
class GamingAdminSite(admin.AdminSite):
    """Personalización completa del sitio admin con tema gaming"""
    site_header = "🎮 GAMERLY Administration"
    site_title = "GAMERLY Admin"
    index_title = "Panel de Control Gaming"

    def each_context(self, request):
        """Agregar contexto personalizado a todas las páginas del admin"""
        context = super().each_context(request)
        context.update({
            'gaming_mode': True,
            'site_brand': 'GAMERLY',
            'show_sidebar': True,
        })
        return context

# Reemplazar el sitio admin por defecto (opcional)
# admin_site = GamingAdminSite(name='gaming_admin')