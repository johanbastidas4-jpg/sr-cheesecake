from decimal import Decimal
from catalogo.models import Producto

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get("cart")

        # Si no existe carrito → crear uno vacío
        if cart is None:
            cart = {}
            self.session["cart"] = cart

        self.cart = cart

    def add(self, producto, cantidad=1):
        producto_id = str(producto.id)

        if producto_id in self.cart:
            # Si ya existe, aumentar cantidad
            self.cart[producto_id]["cantidad"] += cantidad
        else:
            # Guardar cantidad y precio en el carrito
            self.cart[producto_id] = {
                "cantidad": cantidad,
                "precio": str(producto.precio)  # Guardamos como string para serializar en sesión
            }

        self.save()

    def decrement(self, producto, cantidad=1):
        producto_id = str(producto.id)

        if producto_id in self.cart:
            self.cart[producto_id]["cantidad"] -= cantidad
            if self.cart[producto_id]["cantidad"] <= 0:
                del self.cart[producto_id]
            self.save()

    def remove(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.cart:
            del self.cart[producto_id]
            self.save()

    def clear(self):
        self.session["cart"] = {}
        self.session.modified = True

    def save(self):
        self.session["cart"] = self.cart
        self.session.modified = True

    def get_items(self):
        """Retornar lista de items procesados + total"""
        items = []
        total = Decimal("0.00")

        for producto_id, datos in self.cart.items():
            producto = Producto.objects.get(id=int(producto_id))
            cantidad = datos["cantidad"]
            precio = Decimal(datos["precio"])
            subtotal = cantidad * precio

            items.append({
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": subtotal,
            })

            total += subtotal

        return items, total
    
    def count(self):
        """Retorna el número total de items en el carrito"""
        total_items = 0
        for datos in self.cart.values():
            if isinstance(datos, int):
                total_items += datos
            else:
                total_items += datos["cantidad"]
        return total_items

    def get_quantity(self, producto):
        producto_id = str(producto.id)
        if producto_id in self.cart:
            return self.cart[producto_id]["cantidad"]
        return 0
