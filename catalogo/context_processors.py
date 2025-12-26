from .models import Pedido
from .cart import Cart

def nuevos_pedidos(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = Pedido.objects.filter(visto_por_admin=False).count()
        return {'nuevos_pedidos': count}
    return {'nuevos_pedidos': 0}

def cart_count(request):
    cart = Cart(request)
    return {
        'cart_count': cart.count()
    }