from django.apps import AppConfig

class SerialVciConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'serial_vci'

    def ready(self):
        from .models import SerialVCI, Garantia, GarantiaComentario
        from .metrics import TOTAL_SERIAIS, TOTAL_GARANTIAS, TOTAL_COMENTARIOS

        TOTAL_SERIAIS.set(SerialVCI.objects.count())
        TOTAL_GARANTIAS.set(Garantia.objects.count())
        TOTAL_COMENTARIOS.set(GarantiaComentario.objects.count())
