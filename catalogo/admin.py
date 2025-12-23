from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import Categoria, Inventario, Producto, Pedido, DetallePedido
from import_export.admin import ImportExportModelAdmin
from .resources import PedidoResource




@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'precio', 'disponible', 'categoria')
     

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cantidad')

@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal')

@admin.register(Pedido)
class PedidoAdmin(ImportExportModelAdmin):
    resource_class = PedidoResource

    list_display = ('id', 'nombre_cliente','total', 'estado', 'creado_en')
    ordering = ('-creado_en',)
    search_fields = ('id', 'nombre_cliente', 'telefono')

