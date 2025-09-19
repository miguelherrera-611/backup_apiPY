from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import json

from .models import Producto, Categoria, PerfilUsuario, Carrito, ItemCarrito, TokenRecuperacion
from .serializers import (
    ProductoSerializer, ProductoListSerializer,
    CategoriaSerializer, PerfilUsuarioSerializer
)


# ====================== VISTAS WEB ======================

def home(request):
    """Página principal - accesible para todos"""
    productos_destacados = Producto.objects.filter(
        destacado=True,
        estado='disponible'
    ).select_related('categoria')[:6]

    categorias = Categoria.objects.filter(activo=True)

    context = {
        'productos_destacados': productos_destacados,
        'categorias': categorias,
    }
    return render(request, 'home.html', context)


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')


@login_required
def dashboard(request):
    """Dashboard principal - diferente vista según el tipo de usuario"""
    try:
        perfil = request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(usuario=request.user)

    # Asegurar que el carrito exista
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

    es_admin = request.user.is_superuser or perfil.tipo_usuario == 'admin'

    if es_admin:
        # Vista de administrador
        productos = Producto.objects.select_related('categoria', 'creado_por').order_by('-fecha_creacion')
        total_productos = productos.count()
        productos_disponibles = productos.filter(estado='disponible').count()
        productos_agotados = productos.filter(stock=0).count()
        categorias = Categoria.objects.all()

        context = {
            'es_admin': True,
            'productos': productos[:10],  # Últimos 10
            'total_productos': total_productos,
            'productos_disponibles': productos_disponibles,
            'productos_agotados': productos_agotados,
            'categorias': categorias,
            'perfil': perfil,
        }
        return render(request, 'dashboard_admin.html', context)
    else:
        # Vista de cliente
        productos = Producto.objects.filter(
            estado='disponible'
        ).select_related('categoria').order_by('-fecha_creacion')

        # Paginación
        paginator = Paginator(productos, 12)
        page_number = request.GET.get('page')
        productos_paginados = paginator.get_page(page_number)

        categorias = Categoria.objects.filter(activo=True)
        categoria_filtro = request.GET.get('categoria')

        if categoria_filtro:
            productos_paginados = productos.filter(categoria_id=categoria_filtro)

        context = {
            'es_admin': False,
            'productos': productos_paginados,
            'categorias': categorias,
            'categoria_seleccionada': categoria_filtro,
            'perfil': perfil,
            'carrito': carrito,
        }
        return render(request, 'dashboard_cliente.html', context)


def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('home')


# ====================== FUNCIONES DE AYUDA ======================

def es_admin(user):
    """Verifica si el usuario es administrador"""
    if not user.is_authenticated:
        return False
    try:
        perfil = user.perfilusuario
        return user.is_superuser or perfil.tipo_usuario == 'admin'
    except PerfilUsuario.DoesNotExist:
        return user.is_superuser


# ====================== VISTAS AJAX PARA ADMIN ======================

@login_required
@user_passes_test(es_admin)
@csrf_exempt
def crear_producto(request):
    """Crear producto vía AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            producto = Producto.objects.create(
                nombre=data.get('nombre'),
                descripcion=data.get('descripcion'),
                precio=data.get('precio'),
                precio_oferta=data.get('precio_oferta') if data.get('precio_oferta') else None,
                categoria_id=data.get('categoria_id'),
                stock=data.get('stock', 0),
                estado=data.get('estado', 'disponible'),
                destacado=data.get('destacado', False),
                creado_por=request.user
            )

            return JsonResponse({
                'success': True,
                'message': 'Producto creado exitosamente',
                'producto_id': producto.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@user_passes_test(es_admin)
@csrf_exempt
def eliminar_producto(request, producto_id):
    """Eliminar producto vía AJAX"""
    if request.method == 'DELETE':
        try:
            producto = get_object_or_404(Producto, id=producto_id)
            nombre = producto.nombre
            producto.delete()

            return JsonResponse({
                'success': True,
                'message': f'Producto "{nombre}" eliminado exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


# ====================== VISTAS DEL CARRITO ======================

@login_required
@csrf_exempt
def agregar_al_carrito(request):
    """Agregar producto al carrito vía AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto_id = data.get('producto_id')
            cantidad = int(data.get('cantidad', 1))

            producto = get_object_or_404(Producto, id=producto_id, estado='disponible')

            # Verificar stock
            if cantidad > producto.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Solo hay {producto.stock} unidades disponibles'
                })

            # Obtener o crear carrito
            carrito, created = Carrito.objects.get_or_create(usuario=request.user)

            # Obtener o crear item del carrito
            item, item_created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                defaults={'cantidad': cantidad}
            )

            if not item_created:
                # Si el item ya existe, aumentar la cantidad
                nueva_cantidad = item.cantidad + cantidad
                if nueva_cantidad > producto.stock:
                    return JsonResponse({
                        'success': False,
                        'message': f'Solo puedes agregar {producto.stock - item.cantidad} unidades más'
                    })
                item.cantidad = nueva_cantidad
                item.save()

            return JsonResponse({
                'success': True,
                'message': f'{producto.nombre} agregado al carrito',
                'carrito_items': carrito.total_items(),
                'carrito_total': float(carrito.total_precio())
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@csrf_exempt
def actualizar_item_carrito(request, item_id):
    """Actualizar cantidad de un item del carrito vía AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nueva_cantidad = int(data.get('cantidad', 1))

            # Obtener el item del carrito
            item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)

            # Verificar stock
            if nueva_cantidad > item.producto.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Solo hay {item.producto.stock} unidades disponibles'
                })

            if nueva_cantidad <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'La cantidad debe ser mayor a 0'
                })

            # Actualizar cantidad
            item.cantidad = nueva_cantidad
            item.save()

            carrito = item.carrito

            return JsonResponse({
                'success': True,
                'message': 'Cantidad actualizada correctamente',
                'item_subtotal': float(item.subtotal()),
                'carrito_items': carrito.total_items(),
                'carrito_total': float(carrito.total_precio())
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@csrf_exempt
def eliminar_item_carrito(request, item_id):
    """Eliminar un item del carrito vía AJAX"""
    if request.method == 'DELETE':
        try:
            # Obtener el item del carrito
            item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
            producto_nombre = item.producto.nombre
            carrito = item.carrito

            # Eliminar el item
            item.delete()

            return JsonResponse({
                'success': True,
                'message': f'{producto_nombre} eliminado del carrito',
                'carrito_items': carrito.total_items(),
                'carrito_total': float(carrito.total_precio())
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@csrf_exempt
def limpiar_carrito(request):
    """Limpiar todo el carrito vía AJAX"""
    if request.method == 'POST':
        try:
            carrito = get_object_or_404(Carrito, usuario=request.user)
            carrito.limpiar_carrito()

            return JsonResponse({
                'success': True,
                'message': 'Carrito limpiado correctamente',
                'carrito_items': 0,
                'carrito_total': 0.0
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def ver_carrito(request):
    """Vista para mostrar el carrito completo"""
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.select_related('producto').all()

    context = {
        'carrito': carrito,
        'items': items,
    }
    return render(request, 'carrito.html', context)


@login_required
def carrito_items_ajax(request):
    """Obtener items del carrito para mostrar en el dropdown"""
    try:
        carrito = request.user.carrito
        # MOSTRAR TODOS los items sin limitación
        items = carrito.items.select_related('producto').all()

        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'producto_id': item.producto.id,
                'nombre': item.producto.nombre,
                'precio': float(item.producto.precio_actual()),
                'cantidad': item.cantidad,
                'subtotal': float(item.subtotal()),
                'imagen_url': item.producto.imagen.url if item.producto.imagen else None,
                'categoria': item.producto.categoria.nombre,
            })

        return JsonResponse({
            'success': True,
            'items': items_data,
            'total_items': carrito.total_items(),
            'total_precio': float(carrito.total_precio()),
            'items_count': items.count(),
            'has_more': False  # Ya no limitamos
        })
    except Carrito.DoesNotExist:
        return JsonResponse({
            'success': True,
            'items': [],
            'total_items': 0,
            'total_precio': 0.0,
            'items_count': 0,
            'has_more': False
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


# ====================== VISTAS DE USUARIO ======================

def registro_view(request):
    """Vista de registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validaciones
        if not all([username, email, first_name, last_name, password1, password2]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'registro.html')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'registro.html')

        if len(password1) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'registro.html')

        # Verificar que el usuario no exista
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return render(request, 'registro.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return render(request, 'registro.html')

        try:
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )

            # El perfil y carrito se crean automáticamente por las señales
            messages.success(request, f'¡Bienvenido a GAMERLY, {first_name}! Tu cuenta ha sido creada exitosamente.')

            # Loguear automáticamente al usuario
            login(request, user)
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            return render(request, 'registro.html')

    return render(request, 'registro.html')


@login_required
def perfil_view(request):
    """Vista del perfil de usuario"""
    try:
        perfil = request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(usuario=request.user)

    # Asegurar que el carrito exista
    carrito, created = Carrito.objects.get_or_create(usuario=request.user)

    context = {
        'perfil': perfil,
        'carrito': carrito,
    }
    return render(request, 'perfil.html', context)


@login_required
@csrf_exempt
def actualizar_perfil(request):
    """Actualizar perfil de usuario vía AJAX - CORREGIDO"""
    if request.method == 'POST':
        try:
            print("🔍 DEBUG: Iniciando actualización de perfil")
            print(f"📋 POST data recibida: {dict(request.POST)}")

            # Obtener o crear perfil
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
            print(f"✅ Perfil obtenido: {perfil}")

            # Actualizar datos del usuario
            user = request.user

            # ✅ CAMBIOS PRINCIPALES: Obtener datos correctamente del POST
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()

            print(f"📝 Datos a actualizar: first_name='{first_name}', last_name='{last_name}', email='{email}'")

            # Solo actualizar si hay valores
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                # Validar email único
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    print(f"❌ Email duplicado: {email}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Este email ya está en uso por otra cuenta'
                    })
                user.email = email

            # ✅ IMPORTANTE: Guardar el usuario primero
            user.save()
            print(f"✅ Usuario actualizado: {user.first_name} {user.last_name} - {user.email}")

            # Actualizar datos del perfil
            telefono = request.POST.get('telefono', '').strip()
            direccion = request.POST.get('direccion', '').strip()
            fecha_nacimiento = request.POST.get('fecha_nacimiento', '').strip()

            print(f"📱 Perfil a actualizar: telefono='{telefono}', direccion='{direccion}', fecha='{fecha_nacimiento}'")

            # Actualizar campos del perfil solo si hay valores
            if telefono:
                perfil.telefono = telefono
            if direccion:
                perfil.direccion = direccion

            # Manejar fecha de nacimiento
            if fecha_nacimiento:
                from datetime import datetime
                try:
                    perfil.fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                    print(f"✅ Fecha actualizada: {perfil.fecha_nacimiento}")
                except ValueError as e:
                    print(f"❌ Error en fecha: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Formato de fecha inválido'
                    })

            # ✅ IMPORTANTE: Guardar el perfil
            perfil.save()
            print(f"✅ Perfil actualizado: telefono={perfil.telefono}, direccion={perfil.direccion}")

            return JsonResponse({
                'success': True,
                'message': 'Perfil actualizado correctamente',
                'data': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'telefono': perfil.telefono,
                    'direccion': perfil.direccion,
                }
            })

        except Exception as e:
            print(f"❌ Error actualizando perfil: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar perfil: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@csrf_exempt
def cambiar_password(request):
    """Cambiar contraseña del usuario vía AJAX"""
    if request.method == 'POST':
        try:
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            # Validaciones
            if not all([current_password, new_password1, new_password2]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son obligatorios'
                })

            if new_password1 != new_password2:
                return JsonResponse({
                    'success': False,
                    'message': 'Las nuevas contraseñas no coinciden'
                })

            if len(new_password1) < 8:
                return JsonResponse({
                    'success': False,
                    'message': 'La nueva contraseña debe tener al menos 8 caracteres'
                })

            # Verificar contraseña actual
            if not request.user.check_password(current_password):
                return JsonResponse({
                    'success': False,
                    'message': 'La contraseña actual es incorrecta'
                })

            # Cambiar contraseña
            request.user.set_password(new_password1)
            request.user.save()

            # Mantener la sesión activa después del cambio
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)

            return JsonResponse({
                'success': True,
                'message': 'Contraseña cambiada exitosamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cambiar contraseña: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


# ====================== RECUPERACIÓN DE CONTRASEÑA POR EMAIL ======================

def solicitar_recuperacion_password(request):
    """Vista para solicitar recuperación de contraseña por email - CON DEBUGGING"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email_or_username = request.POST.get('email_or_username')

        # 🔍 DEBUGGING AGREGADO
        print(f"🔍 DEBUG WEB: Formulario recibido con: '{email_or_username}'")

        if not email_or_username:
            messages.error(request, 'Por favor ingresa tu email o nombre de usuario')
            return render(request, 'auth/solicitar_recuperacion.html')

        try:
            # Buscar usuario por email o username
            try:
                if '@' in email_or_username:
                    user = User.objects.get(email=email_or_username)
                    print(f"✅ DEBUG WEB: Usuario encontrado por EMAIL: {user.username} - {user.email}")
                else:
                    user = User.objects.get(username=email_or_username)
                    print(f"✅ DEBUG WEB: Usuario encontrado por USERNAME: {user.username} - {user.email}")
            except User.DoesNotExist:
                print(f"❌ DEBUG WEB: Usuario NO encontrado: '{email_or_username}'")
                # Por seguridad, no revelamos si el usuario existe o no
                messages.success(request, 'Si el usuario existe, se ha enviado un email con instrucciones.')
                return render(request, 'auth/solicitar_recuperacion.html')

            # 🔍 DEBUGGING: Verificar email
            if not user.email:
                print(f"❌ DEBUG WEB: Usuario {user.username} sin email")
                messages.error(request, 'Este usuario no tiene email configurado.')
                return render(request, 'auth/solicitar_recuperacion.html')

            print(f"📧 DEBUG WEB: Email destino: {user.email}")

            # Crear token de recuperación
            try:
                token_obj = TokenRecuperacion.crear_token(user)
                print(f"🔑 DEBUG WEB: Token creado: {token_obj.token}")
            except Exception as token_error:
                print(f"❌ DEBUG WEB: Error creando token: {token_error}")
                messages.error(request, 'Error interno. Contacta al administrador.')
                return render(request, 'auth/solicitar_recuperacion.html')

            # Enviar email
            subject = 'Recuperación de contraseña - GAMERLY'

            # Crear contexto para el template del email
            current_site = get_current_site(request)
            context = {
                'user': user,
                'domain': current_site.domain,
                'site_name': 'GAMERLY',
                'token': token_obj.token,
                'protocol': 'https' if request.is_secure() else 'http',
            }

            print(f"🌐 DEBUG WEB: Contexto: {context}")

            # Renderizar el email desde template
            try:
                email_body = render_to_string('auth/email_recuperacion.html', context)
                print(f"✅ DEBUG WEB: Template renderizado OK")
                print(f"📄 DEBUG WEB: Primeros 100 caracteres: {email_body[:100]}...")
            except Exception as template_error:
                print(f"❌ DEBUG WEB: Error en template: {template_error}")
                messages.error(request, 'Error interno del sistema.')
                return render(request, 'auth/solicitar_recuperacion.html')

            print(f"📤 DEBUG WEB: Enviando email...")
            print(f"  - From: {settings.EMAIL_HOST_USER}")
            print(f"  - To: {user.email}")
            print(f"  - Subject: {subject}")

            try:
                result = send_mail(
                    subject=subject,
                    message='Versión en texto plano: Para recuperar tu contraseña, usa el enlace en la versión HTML de este email.',
                    from_email=settings.EMAIL_HOST_USER,  # Usar explícitamente
                    recipient_list=[user.email],
                    html_message=email_body,
                    fail_silently=False,
                )

                print(f"✅ DEBUG WEB: Email enviado! Resultado: {result}")

                if result == 1:
                    print("🎉 DEBUG WEB: Email enviado exitosamente")
                    messages.success(request, 'Se ha enviado un email con instrucciones para recuperar tu contraseña.')
                    return redirect('login')
                else:
                    print(f"⚠️ DEBUG WEB: Send_mail retornó: {result} (esperado: 1)")
                    messages.error(request, 'Error al enviar email. Intenta nuevamente.')

            except Exception as email_error:
                print(f"❌ DEBUG WEB: Error enviando email: {type(email_error).__name__}: {email_error}")
                print(f"🔧 DEBUG WEB: Configuración EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
                print(f"🔧 DEBUG WEB: Configuración EMAIL_HOST: {settings.EMAIL_HOST}")
                print(f"🔧 DEBUG WEB: Configuración EMAIL_PORT: {settings.EMAIL_PORT}")
                messages.error(request, 'Error al enviar el email. Por favor intenta más tarde.')
                return render(request, 'auth/solicitar_recuperacion.html')

        except Exception as e:
            print(f"❌ DEBUG WEB: Error general: {type(e).__name__}: {e}")
            messages.error(request, 'Error interno. Por favor intenta más tarde.')

    return render(request, 'auth/solicitar_recuperacion.html')


def confirmar_recuperacion_password(request, token):
    """Vista para confirmar y cambiar contraseña con token"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    try:
        token_obj = TokenRecuperacion.objects.get(token=token)

        if not token_obj.es_valido():
            messages.error(request, 'El enlace ha expirado o ya fue usado. Solicita uno nuevo.')
            return redirect('solicitar_recuperacion_password')

        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            # Validaciones
            if not new_password1 or not new_password2:
                messages.error(request, 'Ambos campos son obligatorios')
                return render(request, 'auth/confirmar_recuperacion.html', {'token': token})

            if new_password1 != new_password2:
                messages.error(request, 'Las contraseñas no coinciden')
                return render(request, 'auth/confirmar_recuperacion.html', {'token': token})

            if len(new_password1) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
                return render(request, 'auth/confirmar_recuperacion.html', {'token': token})

            # Cambiar contraseña
            user = token_obj.usuario
            user.set_password(new_password1)
            user.save()

            # Marcar token como usado
            token_obj.usado = True
            token_obj.save()

            messages.success(request, '¡Contraseña cambiada exitosamente! Ya puedes iniciar sesión.')
            return redirect('login')

        return render(request, 'auth/confirmar_recuperacion.html', {
            'token': token,
            'usuario': token_obj.usuario
        })

    except TokenRecuperacion.DoesNotExist:
        messages.error(request, 'Enlace inválido o expirado.')
        return redirect('solicitar_recuperacion_password')


def recuperar_password_view(request):
    """Vista para recuperar contraseña (método anterior)"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        # Validaciones
        if not all([username, current_password, new_password1, new_password2]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'recuperar_password.html')

        if new_password1 != new_password2:
            messages.error(request, 'Las nuevas contraseñas no coinciden')
            return render(request, 'recuperar_password.html')

        if len(new_password1) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres')
            return render(request, 'recuperar_password.html')

        try:
            # Verificar que el usuario existe
            user = User.objects.get(username=username)

            # Verificar contraseña actual
            if not user.check_password(current_password):
                messages.error(request, 'La contraseña actual es incorrecta')
                return render(request, 'recuperar_password.html')

            # Cambiar contraseña
            user.set_password(new_password1)
            user.save()

            messages.success(request,
                             'Contraseña cambiada exitosamente. Puedes iniciar sesión con tu nueva contraseña.')
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, 'El usuario no existe')
            return render(request, 'recuperar_password.html')
        except Exception as e:
            messages.error(request, f'Error al cambiar contraseña: {str(e)}')
            return render(request, 'recuperar_password.html')

    return render(request, 'recuperar_password.html')


# ====================== API REST ======================

class ProductoViewSet(viewsets.ModelViewSet):
    """API REST para productos con permisos diferenciados"""
    queryset = Producto.objects.select_related('categoria', 'creado_por').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductoListSerializer
        return ProductoSerializer

    def get_permissions(self):
        """Permisos: clientes solo pueden ver, admins pueden todo"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por estado si es cliente
        if not self.request.user.is_superuser:
            try:
                perfil = self.request.user.perfilusuario
                if perfil.tipo_usuario != 'admin':
                    queryset = queryset.filter(estado='disponible')
            except PerfilUsuario.DoesNotExist:
                queryset = queryset.filter(estado='disponible')

        # Filtros opcionales
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)

        destacado = self.request.query_params.get('destacado')
        if destacado:
            queryset = queryset.filter(destacado=True)

        return queryset

    @action(detail=False, methods=['get'])
    def destacados(self, request):
        """Endpoint para productos destacados"""
        productos = self.get_queryset().filter(destacado=True, estado='disponible')[:6]
        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data)


class CategoriaViewSet(viewsets.ModelViewSet):
    """API REST para categorías"""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Solo mostrar categorías activas a los clientes
        if not self.request.user.is_superuser:
            try:
                perfil = self.request.user.perfilusuario
                if perfil.tipo_usuario != 'admin':
                    queryset = queryset.filter(activo=True)
            except PerfilUsuario.DoesNotExist:
                queryset = queryset.filter(activo=True)

        return queryset


# ====================== API ENDPOINTS ======================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_perfil(request):
    """Obtener perfil del usuario actual"""
    try:
        perfil = request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(usuario=request.user)

    serializer = PerfilUsuarioSerializer(perfil)
    return Response(serializer.data)


@api_view(['GET'])
def estadisticas_publicas(request):
    """Estadísticas públicas de la tienda"""
    total_productos = Producto.objects.filter(estado='disponible').count()
    total_categorias = Categoria.objects.filter(activo=True).count()

    return Response({
        'total_productos': total_productos,
        'total_categorias': total_categorias,
        'productos_destacados': Producto.objects.filter(destacado=True, estado='disponible').count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carrito_info(request):
    """Información del carrito del usuario actual"""
    try:
        carrito = request.user.carrito
        return Response({
            'total_items': carrito.total_items(),
            'total_precio': carrito.total_precio()
        })
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(usuario=request.user)
        return Response({
            'total_items': 0,
            'total_precio': 0
        })


def detalle_producto(request, producto_id):
    """Vista de detalle de un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id, estado='disponible')

    # Productos relacionados de la misma categoría (excluyendo el actual)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        estado='disponible'
    ).exclude(id=producto.id)[:4]

    # Asegurar que el carrito exista si el usuario está autenticado
    carrito = None
    if request.user.is_authenticated:
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)

    context = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
        'carrito': carrito,
    }
    return render(request, 'detalle_producto.html', context)