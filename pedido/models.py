from django.db import models

class Pedido(models.Model):
    data = models.DateField()

    cliente = models.CharField(max_length=255)

    cep = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)

    bairro = models.CharField(max_length=100, blank=True)
    rua = models.CharField(max_length=150, blank=True)
    numero = models.CharField(max_length=20, blank=True)       # opcional
    complemento = models.CharField(max_length=150, blank=True) # opcional

    cnpj_cpf = models.CharField(max_length=30, blank=True)
    ie = models.CharField(max_length=30, blank=True)

    email = models.EmailField(blank=True)
    transporte = models.CharField(max_length=100, blank=True)
    vendedor = models.CharField(max_length=255, blank=True)

    observacoes = models.TextField(blank=True)

    total_geral = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Pedido {self.id}"



class PedidoItem(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        related_name="itens",
        on_delete=models.CASCADE
    )

    referencia = models.CharField(max_length=50, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    unidade = models.CharField(max_length=10, default="UN")
    descricao = models.CharField(max_length=255)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)
