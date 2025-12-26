from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from .cart import Cart
from .models import Producto, Pedido, DetallePedido
from django.db.models import Sum, Count, Avg
from django.contrib.auth.decorators import user_passes_test

# -------------------------------
# LOGIN ADMIN
# -------------------------------

def es_admin(user):
    return user.is_authenticated and user.is_staff

# -------------------------------
# LISTA DE PRODUCTOS
# -------------------------------
def lista_productos(request):
    # Obtiene todos los productos de la base de datos
    productos = Producto.objects.all()
    # Renderiza la plantilla con la lista de productos
    return render(request, 'catalogo/lista_productos.html', {'productos': productos})


# -------------------------------
# DETALLE DE PRODUCTO
# -------------------------------
def detalle_producto(request, producto_id):
    # Busca un producto por ID, si no existe lanza 404
    producto = get_object_or_404(Producto, id=producto_id)
    # Renderiza la plantilla con el detalle del producto
    return render(request, 'catalogo/detalle_producto.html', {'producto': producto})


# -------------------------------
# AGREGAR PRODUCTO AL CARRITO
# -------------------------------
def agregar_al_carrito(request, producto_id):
    cart = Cart(request)
    producto = Producto.objects.get(id=producto_id)
    # Añade el producto con cantidad = 1
    cart.add(producto, cantidad=1)
    return redirect('ver_carrito')


# -------------------------------
# VER CARRITO
# -------------------------------
def ver_carrito(request):
    cart = Cart(request)
    items, total = cart.get_items()

    # Calcula cuánto falta para envío gratis (ejemplo: 60.000 COP)
    faltante_envio = 60000 - total if total < 60000 else 0

    return render(request, 'catalogo/carrito.html', {
        'items': items,
        'total': total,
        'faltante_envio': faltante_envio,
    })


# -------------------------------
# INCREMENTAR CANTIDAD DE UN PRODUCTO
# -------------------------------
def incrementar_cantidad(request, producto_id):
    cart = Cart(request)
    producto = Producto.objects.get(id=producto_id)

    # Validar stock antes de incrementar
    if hasattr(producto, 'inventario'):
        if cart.get_quantity(producto) < producto.inventario.cantidad:
            cart.add(producto, cantidad=1)
        else:
            # Mensaje de error si se intenta pasar del stock
            request.session['error'] = f"Solo quedan {producto.inventario.cantidad} unidades de {producto.nombre}."
    return redirect('ver_carrito')



# -------------------------------
# DECREMENTAR CANTIDAD DE UN PRODUCTO
# -------------------------------
def decrementar_cantidad(request, producto_id):
    cart = Cart(request)
    producto = Producto.objects.get(id=producto_id)
    # Resta 1 unidad del producto
    cart.decrement(producto)
    return redirect('ver_carrito')


# -------------------------------
# ELIMINAR PRODUCTO DEL CARRITO
# -------------------------------
def eliminar_item(request, producto_id):
    cart = Cart(request)
    producto = Producto.objects.get(id=producto_id)
    # Elimina completamente el producto del carrito
    cart.remove(producto)
    return redirect('ver_carrito')


# -------------------------------
# CHECKOUT (FINALIZAR PEDIDO)
# -------------------------------
def checkout(request):
    cart = Cart(request)
    items, total = cart.get_items()

    # Si el carrito está vacío, redirige a la lista de productos
    if not items:
        return redirect('lista_productos')

    # Calcular cuánto falta para envío gratis (ejemplo: 60.000 COP)
    faltante_envio = 60000 - total if total < 60000 else 0

    if request.method == 'POST':
        # Captura datos del formulario
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        metodo_pago = request.POST.get('metodo_pago')

        # Validación: todos los campos son obligatorios
        if not nombre or not telefono or not direccion or not metodo_pago:
            return render(request, 'catalogo/checkout.html', {
                'items': items,
                'total': total,
                'faltante_envio': faltante_envio,
                'error': "Todos los campos son obligatorios."
            })

        # Crear el pedido
        pedido = Pedido.objects.create(
            nombre_cliente=nombre,
            telefono=telefono,
            direccion=direccion,
            total=total,
            metodo_pago=metodo_pago,
            estado_pago="pendiente",
            visto_por_admin=False,
        )

        # Crear detalles del pedido y actualizar inventario
        for item in items:
            producto = item['producto']
            cantidad = item['cantidad']
            subtotal = item['subtotal']

            # Validar stock antes de restar
            if hasattr(producto, 'inventario'):
                if producto.inventario.cantidad >= cantidad:
                    producto.inventario.cantidad -= cantidad
                    producto.inventario.save()
                else:
                    # Si no hay stock suficiente, mostrar error y no crear pedido
                    return render(request, 'catalogo/checkout.html', {
                        'items': items,
                        'total': total,
                        'faltante_envio': faltante_envio,
                        'error': f"No hay suficiente stock de {producto.nombre}. Disponible: {producto.inventario.cantidad}"
                    })

            # Crear detalle del pedido
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal
            )

        # Vaciar carrito
        cart.clear()

        # Flujo según método de pago
        if metodo_pago == "Wompi":
            return redirigir_a_wompi (pedido)
        else:
        # Efectivo, Datáfono o Transferencia: se mantiene pendiente
            return redirect('confirmacion_pedido', pedido_id=pedido.id)
        

    # Si es GET, mostrar formulario
    return render(request, 'catalogo/checkout.html', {
        'items': items,
        'total': total,
        'faltante_envio': faltante_envio,
    })


# -------------------------------
# REPORTES DE VENTAS
# -------------------------------
@user_passes_test(es_admin)
def reportes(request):

    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")
    pedidos = Pedido.objects.all()

    # Si el usuario selecciona un rango de fechas
    if fecha_inicio and fecha_fin:
        pedidos = pedidos.filter(creado_en__date__range=[fecha_inicio, fecha_fin])

    # Total de ventas
    total_ventas = pedidos.aggregate(total=Sum('total'))['total'] or 0
    # Número de pedidos
    total_pedidos = pedidos.count()
    # Promedio de pedido
    promedio_pedido = pedidos.aggregate(promedio=Avg('total'))['promedio'] or 0
    promedio_pedido = round(promedio_pedido, 2)

    # Top 5 productos más vendidos
    productos_mas_vendidos = (
        DetallePedido.objects.filter(pedido__in=pedidos)
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    ) 

    return render(request, 'catalogo/admin_reportes.html', {
        'total_ventas': total_ventas,
        'total_pedidos': total_pedidos,
        'promedio_pedido': promedio_pedido,
        'productos_mas_vendidos': productos_mas_vendidos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })


# -------------------------------
 #PAGOS (WOMPI)
# -------------------------------
def redirigir_a_wompi(pedido):
    base_url = settings.WOMPI_CHECKOUT_URL
    public_key = settings.WOMPI_PUBLIC_KEY

    amount_in_cents = int(pedido.total * 100)

    reference = f"PEDIDO{pedido.id}"

    wompi_url = (
        f"{base_url}"
        f"?amount-in-cents={amount_in_cents}"
        f"&reference={reference}"
        f"&public-key={public_key}"
    )
    return redirect(wompi_url)

def wompi_confirmacion(request):
    reference = request.GET.get("reference")
    status = request.GET.get("status")

    if not reference:
        # Mostrar un error
        return redirect('lista_productos')

    pedido_id = reference.replace("PEDIDO", "")
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if status == "APPROVED":
        pedido.estado_pago = "pagado"
    elif status == "DECLINED":
        pedido.estado_pago = "rechazado"
    else:
        pedido.estado_pago = "pendiente"

    pedido.save()

    return redirect('confirmacion_pedido', pedido_id=pedido.id)

def confirmacion_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'catalogo/confirmacion_pedido.html', {'pedido': pedido})


# -------------------------------
# PANEL ADMINISTRATIVO - DASHBOARD
# -------------------------------

@user_passes_test(es_admin)
def panel_inicio(request):
    # Total de ventas
    total_ventas = Pedido.objects.aggregate(total=Sum('total'))['total'] or 0
    # Número de pedidos
    total_pedidos = Pedido.objects.count()
    # Promedio de pedido
    promedio_pedido = Pedido.objects.aggregate(promedio=Avg('total'))['promedio'] or 0

    # Top 5 productos más vendidos
    productos_mas_vendidos = (
        DetallePedido.objects
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    )

    return render(request, 'catalogo/panel_inicio.html', {
        'total_ventas': total_ventas,
        'total_pedidos': total_pedidos,
        'promedio_pedido': promedio_pedido,
        'productos_mas_vendidos': productos_mas_vendidos,
    })

@user_passes_test(es_admin)
def admin_pedidos(request):
    # Marcar todos los pedidos como vistos 
    Pedido.objects.filter(visto_por_admin=False).update(visto_por_admin=True)
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")
    estado_pago = request.GET.get("estado_pago")
    estado = request.GET.get("estado")
    pedidos = Pedido.objects.order_by('-creado_en')
    

    # FILTROS
    if fecha_inicio and fecha_fin:
        pedidos = pedidos.filter(creado_en__date__range=[fecha_inicio, fecha_fin])
    
    
    if estado_pago:
        pedidos = pedidos.filter(estado_pago=estado_pago)

    if estado:
        pedidos = pedidos.filter(estado=estado)

    return render(request, 'catalogo/admin_pedidos.html', {
        'pedidos': pedidos,
        'estado_pago': estado_pago,
        'estado': estado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin, })

@user_passes_test(es_admin)
def admin_detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles = pedido.detalles.all()

    if request.method == "POST":
        pedido.estado = request.POST.get("estado")
        pedido.save()
        return redirect('admin_detalle_pedido', pedido_id=pedido.id)
    
    return render(request, 'catalogo/admin_detalle_pedido.html', {
        'pedido': pedido,
        'detalles': detalles,
    })

@user_passes_test(es_admin)
def admin_inventario(request):
    productos = Producto.objects.all()
    return render(request, 'catalogo/admin_inventario.html', {'productos': productos})

@user_passes_test(es_admin)
def editar_inventario(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == "POST":
        nueva_cantidad = request.POST.get("cantidad")

        if nueva_cantidad.isdigit():
            producto.inventario.cantidad = int(nueva_cantidad)
            producto.inventario.save()

        return redirect('admin_inventario')

    return render(request, 'catalogo/editar_inventario.html', {
        'producto': producto
    })


