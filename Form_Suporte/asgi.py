import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Importe TODOS os routing necessários
import ocorrencia_erro.routing
import serial_vci.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Form_Suporte.settings')

websocket_patterns = (
    ocorrencia_erro.routing.websocket_urlpatterns +
    serial_vci.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_patterns)
    ),
})
