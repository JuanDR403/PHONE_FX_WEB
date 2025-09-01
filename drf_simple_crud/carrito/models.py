from django.db import models
from usuarios.models import Usuarios
from productos.models import Producto


class Carrito(models.Model):
    idcarrito = models.AutoField(db_column='idCarrito', primary_key=True)

    cliente = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_cliente',
        related_name='carritos'
    )

    fecha_creacion = models.CharField(max_length=45, blank=True, null=True)
    estado = models.CharField(max_length=9, blank=True, null=True)

    def __str__(self):
        return f"Carrito #{self.idcarrito} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"

    class Meta:
        db_table = 'carrito'


class CarritoDetalle(models.Model):
    idcarritodetalle = models.AutoField(db_column='idCarritoDetalle', primary_key=True)

    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        db_column='id_carrito',
        related_name='detalles'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_producto'
    )

    cantidad = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else 'Producto eliminado'}"

    class Meta:
        db_table = 'carritodetalle'
