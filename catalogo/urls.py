from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
# rutas de carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('checkout/', views.checkout, name='checkout'),
    path('carrito/mas/<int:producto_id>/', views.incrementar_cantidad, name='incrementar_cantidad'),
    path('carrito/menos/<int:producto_id>/', views.decrementar_cantidad, name='decrementar_cantidad'),
    path('carrito/eliminar/<int:producto_id>/', views.eliminar_item, name='eliminar_item'),
    
# rutas pagos
    path('pago/wompi/confirmacion/', views.wompi_confirmacion, name='wompi_confirmacion'),
    path('pedido/<int:pedido_id>/confirmacion/', views.confirmacion_pedido, name='confirmacion_pedido'),

# rutas del panel administrativo
    path('panel/', views.panel_inicio, name='panel_inicio'),
    path('panel/pedidos/', views.admin_pedidos, name='admin_pedidos'),
    path('panel/pedidos/<int:pedido_id>/', views.admin_detalle_pedido, name='admin_detalle_pedido'),
    path('panel/inventario/', views.admin_inventario, name='admin_inventario'),
    path('inventario/editar/<int:producto_id>/', views.editar_inventario, name='editar_inventario'),
    path('panel/reportes/', views.reportes, name='admin_reportes'),

# rutas para login

# LOGIN / LOGOUT DEL PANEL
    path('panel/login/', auth_views.LoginView.as_view(
    template_name='catalogo/admin_login.html'
    ), name='admin_login'),

    path(
    'panel/logout/',
    auth_views.LogoutView.as_view(),
    name='admin_logout'
    ),


]
