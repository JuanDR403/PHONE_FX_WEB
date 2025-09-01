from django.db import models
from usuarios.models import Usuarios
from productos.models import Producto

class Pedido(models.Model):
    idpedido = models.AutoField(db_column='idPedido', primary_key=True)
    cliente = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_cliente',
        related_name='pedidos'
    )
    fecha_pedido = models.CharField(max_length=45)
    total = models.CharField(max_length=100)
    estado = models.CharField(max_length=9)
    direccion_envio = models.CharField(max_length=200)

    def __str__(self):
        return f"Pedido #{self.idpedido} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"

    class Meta:
        db_table = 'pedido'


class PedidoDetalle(models.Model):
    idpedidodetalle = models.AutoField(db_column='idPedidoDetalle', primary_key=True)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        db_column='id_pedido',
        related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_producto'
    )
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else 'Producto eliminado'}"

    class Meta:
        db_table = 'pedidodetalle'


class Pago(models.Model):
    idpago = models.AutoField(db_column='idPago', primary_key=True)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_pedido',
        related_name='pagos'
    )
    metodo = models.CharField(max_length=14)
    fecha_pago = models.CharField(max_length=45, blank=True, null=True)
    estado = models.CharField(max_length=9, blank=True, null=True)

    def __str__(self):
        return f"Pago #{self.idpago} - {self.metodo} ({self.estado})"

    class Meta:
        db_table = 'pago'
