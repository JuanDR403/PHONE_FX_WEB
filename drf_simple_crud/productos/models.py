from django.db import models

class Categoria(models.Model):
    idcategoria = models.AutoField(db_column='idCategoria', primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre or f"Categoría {self.idcategoria}"

    class Meta:
        db_table = 'categoria'


class Producto(models.Model):
    idproducto = models.AutoField(primary_key=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_categoria',
        related_name='productos'
    )
    nombre = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.CharField(max_length=100, blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True)
    imagen = models.CharField(max_length=500, blank=True, null=True)
    activo = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return self.nombre or f"Producto {self.idproducto}"

    class Meta:
        db_table = 'producto'
