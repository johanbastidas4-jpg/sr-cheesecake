from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Pedido, DetallePedido, Producto, Categoria


class PedidoResource(resources.ModelResource):
    total_items = fields.Field()
    promedio_item = fields.Field()

    class Meta:
        model = Pedido
        fields = (
            'id',
            'nombre_cliente',
            'telefono',
            'direccion',
            'fecha',
            'total',
        )
        export_order = (
            'id',
            'nombre_cliente',
            'telefono',
            'direccion',
            'fecha',
            'total',
            'total_items',
            'promedio_item',
        )

    # Total de unidades por pedido
    def dehydrate_total_items(self, pedido):
        return sum(detalle.cantidad for detalle in pedido.detalles.all())

    # Valor promedio por item = total / total_items
    def dehydrate_promedio_item(self, pedido):
        total_items = sum(detalle.cantidad for detalle in pedido.detalles.all())
        if total_items == 0:
            return 0
        return round(pedido.total / total_items, 2)
