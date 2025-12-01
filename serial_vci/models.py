from django.db import models

class SerialVCI(models.Model):
    numero_vci = models.CharField(max_length=100)
    numero_tablet = models.CharField(max_length=100)
    numero_prog = models.CharField(max_length=100)
    cliente = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    pedido = models.CharField(max_length=100)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero_vci} - {self.cliente}"


class SerialFoto(models.Model):
    serial = models.ForeignKey(SerialVCI, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='serial_vci/')

    def __str__(self):
        return f"Foto de {self.serial.numero_vci}"