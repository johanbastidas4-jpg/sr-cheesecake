from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from .models import Producto, Pedido, DetallePedido

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'catalogo/lista_productos.html', {'productos': productos})

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'catalogo/detalle_producto.html', {'producto': producto})

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, disponible=True)

    # Carrito guardado en la sesión como diccionario {id_producto: cantidad}
    carrito = request.session.get('carrito', {})

    producto_id_str = str(producto.id)
    if producto_id_str in carrito:
        carrito[producto_id_str] += 1
    else:
        carrito[producto_id_str] = 1

    request.session['carrito'] = carrito
    request.session.modified = True

    return redirect('ver_carrito')


def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    items = []
    total = Decimal('0.00')

    for producto_id_str, cantidad in carrito.items():
        producto = get_object_or_404(Producto, id=int(producto_id_str))
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })

    return render(request, 'catalogo/carrito.html', {
        'items': items,
        'total': total,
    })


def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    producto_id_str = str(producto_id)

    if producto_id_str in carrito:
        del carrito[producto_id_str]
        request.session['carrito'] = carrito
        request.session.modified = True

    return redirect('ver_carrito')

def checkout(request):
    carrito = request.session.get('carrito', {})

    if not carrito:
        # Si no hay nada en el carrito, enviamos de nuevo al catálogo
        return redirect('lista_productos')

    items = []
    total = Decimal('0.00')

    for producto_id_str, cantidad in carrito.items():
        producto = get_object_or_404(Producto, id=int(producto_id_str))
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')

        if not nombre or not telefono or not direccion:
            error = "Todos los campos son obligatorios."
            return render(request, 'catalogo/checkout.html', {
                'items': items,
                'total': total,
                'error': error,
                'nombre': nombre,
                'telefono': telefono,
                'direccion': direccion,
            })

        pedido = Pedido.objects.create(
            nombre_cliente=nombre,
            telefono=telefono,
            direccion=direccion,
            total=total,
        )

        # Crear detalles del pedido y actualizar inventario
        for item in items:
            producto = item['producto']
            cantidad = item['cantidad']
            subtotal = item['subtotal']

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal,
            )

            # Actualizar inventario si existe
            if hasattr(producto, 'inventario'):
                producto.inventario.cantidad = max(0, producto.inventario.cantidad - cantidad)
                producto.inventario.save()

        # Vaciar el carrito
        request.session['carrito'] = {}
        request.session.modified = True

        return render(request, 'catalogo/confirmacion_pedido.html', {
            'pedido': pedido,
        })

    # Si es GET, mostrar formulario
    return render(request, 'catalogo/checkout.html', {
        'items': items,
        'total': total,
    })
