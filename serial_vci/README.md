# 🚀 Documentação do Projeto Serial VCI

Este projeto é uma aplicação web desenvolvida em **Django** para gestão de registros de Seriais VCI. Ele utiliza **Django Channels** para comunicação em tempo real via WebSockets e gerencia o upload e a visualização de fotos de mídia.

---

## 🛠️ Configuração e Instalação

### 1. Requisitos

* **Python 3.x**
* **Django** (Framework Web)
* **Django Channels** (Para WebSockets)
* **Banco de Dados** (Geralmente SQLite, PostgreSQL ou MySQL)

### 2. Configuração do Ambiente

1.  **Instalar Dependências (exemplo):**
    ```bash
    pip install django djangorestframework channels
    ```

2.  **Configurar `settings.py` (Principal):**

    * **Adicionar Apps e Channels:**
        ```python
        INSTALLED_APPS = [
            # ... apps nativos e de terceiros
            'channels',
            'serial_vci',
        ]

        # Configuração do Channels (substitua 'seu_projeto' pelo nome do seu projeto)
        ASGI_APPLICATION = 'seu_projeto.asgi.application' 
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer', # Use Redis em produção
            },
        }
        ```

    * **Configurar Mídia (Arquivos de Usuário):**
        ```python
        MEDIA_URL = '/media/'
        MEDIA_ROOT = BASE_DIR / 'media'
        ```

3.  **Configurar `urls.py` (Principal) para servir Mídia:**

    Esta é uma correção crucial para exibir as imagens em ambiente de desenvolvimento (`DEBUG=True`).
    ```python
    # urls.py principal
    # ... imports ...
    from django.conf import settings
    from django.conf.urls.static import static 

    urlpatterns = [
        # ... suas rotas ...
    ]
    
    # Servir arquivos de Mídia e Estáticos apenas em modo de desenvolvimento
    if settings.DEBUG:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    ```

4.  **Realizar Migrações:**
    ```bash
    python manage.py makemigrations serial_vci
    python manage.py migrate
    ```

5.  **Executar o Servidor (usando Channels):**
    ```bash
    python manage.py runserver
    ```

---

## 📦 Estrutura e Modelos

O projeto utiliza dois modelos principais no `serial_vci/models.py`:

| Modelo | Função | Campos Chave |
| :--- | :--- | :--- |
| **`SerialVCI`** | Registro principal do equipamento. | `numero_vci`, `numero_tablet`, `cliente`, `email`, `pedido`. |
| **`SerialFoto`** | Armazena as fotos relacionadas a um serial. | `serial` (ForeignKey), `imagem` (ImageField, salva em `media/serial_vci/`). |

---

## ✨ Funcionalidades e Rotas

O aplicativo oferece o seguinte conjunto de operações:

### 1. CRUD e Fluxo de Dados

| Funcionalidade | Endpoint | Método | Descrição |
| :--- | :--- | :--- | :--- |
| **Lista/Busca** | `/seriais/` | GET/AJAX | Exibe tabela principal, busca e paginação dinâmicas. |
| **Adicionar** | `/seriais/adicionar/` | POST | Cria um novo serial e suas fotos. |
| **Detalhes** | `/seriais/detalhes/<id>/` | GET | Retorna JSON com todos os dados e URLs das fotos. |
| **Edição Restrita** | `/seriais/editar/<id>/` | POST | Permite a edição **APENAS** dos campos `VCI`, `Tablet` e `Prog`, e a adição de novas fotos. |
| **Remover Foto** | `/seriais/remover_foto/<id>/` | POST | Remove uma foto específica permanentemente (usado no modal de edição). |

### 2. WebSockets (Tempo Real)

A aplicação utiliza **Django Channels** para comunicação em tempo real:

* **`consumers.py`**: Define o `SerialVCIConsumer` para gerenciar a conexão WebSocket.
* **`views.py`**: A função `broadcast_update()` é chamada após qualquer operação de escrita (adição, edição, remoção), enviando uma mensagem de atualização para o grupo `"serial_vci_updates"`.
* **`index.html` (Frontend)**: O JavaScript do cliente escuta a conexão WSS/WS e, ao receber a mensagem, aciona uma busca AJAX para atualizar a tabela em tempo real.

### 3. Visualizador de Imagem (Lightbox) 🖼️

Para melhorar a visualização das fotos:

* **Ação:** Ao clicar em qualquer miniatura de foto exibida nos modais (Adição, Detalhes ou Edição), o evento `onclick="abrirImagemCompleta(url)"` é disparado.
* **Resultado:** Abre um modal escuro de tela cheia que exibe a imagem em tamanho completo, proporcionando uma experiência de visualização otimizada.