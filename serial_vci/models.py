from django.db import models

class SerialVCI(models.Model):
    # VCI continua obrigatório (padrão)
    numero_vci = models.CharField(max_length=100) 
    numero_tablet = models.CharField(max_length=100, blank=True, null=True)
    numero_prog = models.CharField(max_length=100, blank=True, null=True)
    
    # CORREÇÃO: Tornando não obrigatórios
    cliente = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    pedido = models.CharField(max_length=100, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # CORREÇÃO: Removida a definição duplicada
        return f"{self.numero_vci} - {self.cliente or 'Sem Cliente'}"


class SerialFoto(models.Model):
    serial = models.ForeignKey(SerialVCI, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='serial_vci/')

    def __str__(self):
        return f"Foto de {self.serial.numero_vci}"