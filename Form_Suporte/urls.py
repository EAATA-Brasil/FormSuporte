from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # URLs sem prefixo de idioma (normalmente admin)
    path('admin/', admin.site.urls),
    path("simulador/", include("simulador.urls")),
    path("api/", include("API.urls"))
]

# URLs que devem ter prefixo de idioma
urlpatterns += i18n_patterns(
    path("", include("ocorrencia_erro.urls")),
    path("form/", include("form.urls")),
    path("situacao/", include("situacao_veiculo.urls")),
    path("ocorrencia/", include("ocorrencia_erro.urls"))
    
)

path('i18n/', include('django.conf.urls.i18n')),

# Arquivos estáticos
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
