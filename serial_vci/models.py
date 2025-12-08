from django.db import models
from django.utils import timezone

class SerialVCI(models.Model):
    # Campos que você quer EDITAR (VCI, Tablet, Prog)
    numero_vci = models.CharField(max_length=100, blank=True, null=True) 
    # Tornados opcionais (blank=True, null=True) para edição e criação
    numero_tablet = models.CharField(max_length=100, blank=True, null=True) 
    numero_prog = models.CharField(max_length=100, blank=True, null=True)   
    
    # Campos não-editáveis (apenas criação)
    cliente = models.CharField(max_length=255, blank=True, null=True) # Mantido como obrigatório
    email = models.EmailField(blank=True, null=True)                # Mantido como obrigatório
    telefone = models.CharField(max_length=100, blank=True, null=True) # Tornados opcionais
    pedido = models.CharField(max_length=100, blank=True, null=True)  # Mantido como obrigatório

    criado_em = models.DateTimeField(auto_now_add=True)

    data = models.DateField(verbose_name="Data", blank=False, default=timezone.now)

    def __str__(self):
        return f"{self.numero_vci} - {self.cliente or 'Sem Cliente'}"


class SerialFoto(models.Model):
    serial = models.ForeignKey(SerialVCI, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='serial_vci/')

    def __str__(self):
        return f"Foto de {self.serial.numero_vci}"