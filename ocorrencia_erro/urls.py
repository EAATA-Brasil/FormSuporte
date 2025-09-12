from django.urls import path
from . import views

def get_china_id_view(request):
    from django.http import JsonResponse
    from .models import Country
    try:
        china = Country.objects.get(name='China' )
        return JsonResponse({'china_id': china.id})
    except Country.DoesNotExist:
        return JsonResponse({'error': 'País "China" não encontrado no banco de dados.'}, status=404)


urlpatterns = [
    path('', views.index, name='index'),
    path('subir_ocorrencia/', views.subir_ocorrencia, name='subir_ocorrencia'),
    path('filter_data/', views.filter_data_view, name='filter_data'),
    path('update_ocorrencia/', views.update_record_view, name='update_ocorrencia'),
    path('criar_usuario/', views.criar_usuario, name='criar_usuario'),
    path('login/', views.login_view, name='login_ocorrencias'),  
    path('logout/', views.logout_view, name='logout'),
    path('download_arquivo/<int:arquivo_id>/', views.download_arquivo, name='download_arquivo'),
    path('get_record/<int:pk>/', views.get_record, name='get_record'),
    path('notificacoes/', views.listar_notificacoes, name='listar_notificacoes'),
    path('notificacoes/contar/', views.contar_notificacoes_nao_lidas, name='contar_notificacoes'),
    path('notificacoes/<int:notificacao_id>/marcar_lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('api/get_china_id/', get_china_id_view, name='get_china_id'),
    path('gerar_pdf/<int:record_id>/', views.gerar_pdf_ocorrencia, name='gerar_pdf_ocorrencia'),
    path('gerar_pdf/', views.gerar_pdf_ocorrencia, name='gerar_pdf_ocorrencia_post'),
    path("ocorrencia/download_todos/<int:record_id>/", views.download_todos_arquivos, name="download_todos_arquivos"),
]