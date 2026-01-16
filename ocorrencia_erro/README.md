# Documentação do Aplicativo Django: ocorrencia_erro

## 1. Visão Geral

O aplicativo `ocorrencia_erro` é um sistema robusto para gerenciar e rastrear ocorrências ou problemas. Ele permite o registro detalhado de incidentes, atribuição a técnicos, definição de prazos, acompanhamento de status, upload de arquivos e comunicação via chat. O sistema também implementa um controle de acesso baseado em permissões de país e grupos de usuários, além de funcionalidades de notificação e geração de relatórios em PDF.

## 2. Modelos

Este aplicativo define os seguintes modelos para estruturar os dados:

### 2.1. `Country`

Representa os países, utilizados para filtrar permissões e ocorrências.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `name` | `CharField(max_length=100, unique=True)` | Nome único do país. |

### 2.2. `Device`

Representa os equipamentos associados às ocorrências.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `name` | `CharField(max_length=100, unique=True)` | Nome único do equipamento. |

### 2.3. `CountryPermission`

Define as permissões de acesso a países para usuários específicos.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `user` | `ForeignKey(User)` | Usuário associado à permissão. |
| `country` | `ForeignKey(Country)` | País ao qual o usuário tem permissão. |

### 2.4. `Record`

O modelo central que representa uma ocorrência ou problema.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `id` | `AutoField(primary_key=True)` | ID autoincremental da ocorrência. |
| `codigo_externo` | `CharField(max_length=20, blank=True, null=True, unique=True)` | Código externo opcional para a ocorrência. |
| `data` | `DateField(default=timezone.now)` | Data em que o problema foi reportado. |
| `deadline` | `DateField(blank=True, null=True)` | Prazo para resolução do problema. |
| `finished` | `DateField(blank=True, null=True)` | Data em que o problema foi resolvido. |
| `arquivo` | `FileField(upload_to='uploads/', null=True, blank=True)` | Arquivo principal da ocorrência (legado, agora usa `ArquivoOcorrencia`). |
| `technical` | `CharField(max_length=100, default="Não identificado")` | Nome do técnico responsável. |
| `responsible` | `CharField(max_length=100, default="Não identificado", null=True, blank=True)` | Nome do responsável pela ocorrência. |
| `device` | `ForeignKey(Device, null=True, blank=True)` | Equipamento relacionado à ocorrência. |
| `area` | `CharField(max_length=20, default="N/A")` | Área da ocorrência. |
| `serial` | `CharField(max_length=20, blank=True, null=True, default="N/A")` | Número de série do equipamento. |
| `brand` | `CharField(max_length=100, blank=True, null=True, default="N/A")` | Marca do equipamento. |
| `model` | `CharField(max_length=100, blank=True, null=True, default="N/A")` | Modelo do equipamento. |
| `contact` | `CharField(max_length=100, blank=True, null=True, default="N/A")` | Contato relacionado à ocorrência. |
| `year` | `CharField(max_length=100, blank=True, null=True, default='N/A')` | Ano do equipamento. |
| `country` | `ForeignKey(Country, null=True, blank=True)` | País da ocorrência. |
| `country_original` | `CharField(max_length=100, null=True, blank=True)` | País original da ocorrência (preenchido na criação). |
| `version` | `CharField(max_length=100, blank=True, null=True, default="N/A")` | Versão do software/firmware. |
| `problem_detected` | `TextField(default="Não identificado")` | Descrição do problema detectado. |
| `solution` | `TextField(blank=True, null=True)` | Solução final da ocorrência; preenchida automaticamente quando uma mensagem no chat começa com `solução:`/`solucao:`. |
| `status` | `CharField(max_length=20, choices=STATUS_OCORRENCIA.choices, default=STATUS_OCORRENCIA.REQUESTED)` | Status da ocorrência (Concluído, Atrasado, Em progresso, Requisitado, Aguardando). |
| `feedback_technical` | `TextField(blank=True, null=True, default="Não identificado")` | Feedback do técnico. |
| `feedback_manager` | `TextField(blank=True, null=True, default="Não identificado")` | Feedback do gestor. |

**Métodos Especiais:**

- `clear_finished_date()`: Limpa a data de `finished` e ajusta o status se necessário.
- `clear_deadline_date()`: Limpa a data de `deadline` e ajusta o status se necessário.
- `clean()`: Realiza validações e ajusta o status da ocorrência com base nas datas e regras de negócio (exceto para a China, que tem tratamento especial).
- `save()`: Sobrescreve o método `save` para garantir a lógica de preenchimento do `country_original`, chamar `clean()` e aplicar a regra de status para ocorrências da China (sempre `AWAITING`). Também gera `codigo_externo` se não for fornecido.

### 2.5. `ArquivoOcorrencia`

Armazena arquivos anexados a uma ocorrência.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `record` | `ForeignKey(Record, related_name='arquivos', null=True)` | Ocorrência à qual o arquivo está anexado. |
| `arquivo` | `FileField(upload_to='download_arquivo/')` | O arquivo em si. |
| `nome_original` | `CharField(max_length=255, blank=True)` | Nome original do arquivo. |

### 2.6. `Notificacao`

Modelo para notificações de feedback em ocorrências.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `user` | `ForeignKey(User, related_name='notificacoes')` | Usuário que receberá a notificação. |
| `record` | `ForeignKey(Record, related_name='notificacoes')` | Ocorrência relacionada à notificação. |
| `tipo` | `CharField(max_length=20, choices=...)` | Tipo de notificação (ex: 'feedback_manager'). |
| `titulo` | `CharField(max_length=200)` | Título da notificação. |
| `resumo` | `TextField(max_length=500)` | Resumo da notificação. |
| `lida` | `BooleanField(default=False)` | Indica se a notificação foi lida. |
| `criada_em` | `DateTimeField(auto_now_add=True)` | Data e hora de criação da notificação. |
| `lida_em` | `DateTimeField(null=True, blank=True)` | Data e hora em que a notificação foi lida. |

**Métodos Especiais:**

- `marcar_como_lida()`: Marca a notificação como lida e a exclui do banco de dados.

### 2.7. `ChatMessage`

Modelo para mensagens de chat associadas a uma ocorrência.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `record` | `ForeignKey(Record, related_name='chat_messages')` | Ocorrência à qual a mensagem pertence. |
| `author` | `ForeignKey(User)` | Autor da mensagem. |
| `message` | `TextField()` | Conteúdo da mensagem. |
| `timestamp` | `DateTimeField(auto_now_add=True)` | Data e hora da mensagem. |

## 3. Views

As views definem a lógica de negócio e os endpoints da aplicação.

### 3.1. `get_responsaveis()`

Função auxiliar que retorna uma lista de responsáveis (usuários do grupo 'Técnicos responsáveis') por país e uma lista de todos os responsáveis, em formato JSON. Utilizada para preencher dropdowns na interface.

### 3.2. `subir_arquivo(files, record)`

Função auxiliar que processa e salva múltiplos arquivos (`files`) associados a um `record` específico, criando instâncias de `ArquivoOcorrencia`.

### 3.3. `download_todos_arquivos(request, record_id)`

- **URL:** `ocorrencia/download_todos/<int:record_id>/`
- **Métodos:** `GET`
- **Funcionalidade:** Permite o download de todos os arquivos anexados a uma ocorrência. Se houver 5 ou menos arquivos, retorna o primeiro diretamente. Se houver mais de 5, compacta todos em um arquivo ZIP e o retorna para download.

### 3.4. `index(request)`

- **URL:** `/`
- **Métodos:** `GET`
- **Funcionalidade:** Renderiza a página inicial do sistema de ocorrências. Prepara dados como permissões do usuário (superuser, semi-admin), países permitidos, e estatísticas de ocorrências por responsável e status. O contexto inclui variáveis para controlar a visibilidade de elementos da UI, como permissões de edição.

### 3.5. `filter_data_view(request)`

- **URL:** `filter_data/`
- **Métodos:** `POST`
- **Funcionalidade:** Endpoint AJAX para filtrar e ordenar ocorrências. Recebe filtros e informações de ordenação via POST, aplica permissões de usuário (superuser, semi-admin, técnico padrão), pagina os resultados e retorna os dados das ocorrências em formato JSON. Inclui lógica para lidar com diferentes tipos de campos (texto, data, foreign keys) e valores vazios/nulos.

### 3.6. `criar_usuario(request)`

- **URL:** `criar_usuario/`
- **Métodos:** `GET`, `POST`
- **Funcionalidade:** Permite a criação de novos usuários. `GET` exibe o formulário. `POST` processa o formulário, cria o usuário, define a senha, atribui o usuário a um grupo (`Técnicos responsáveis`, `Técnicos de reporte`, `Semi Admin`) e associa permissões de país. Inclui validações para campos obrigatórios e usernames duplicados.

### 3.7. `subir_ocorrencia(request)`

- **URL:** `subir_ocorrencia/`
- **Métodos:** `GET`, `POST`
- **Funcionalidade:** Permite o registro de novas ocorrências. `GET` exibe o formulário de criação. `POST` valida os dados (campos obrigatórios, formato de ticket, datas), cria uma nova instância de `Record` e processa o upload de arquivos anexados. Retorna `JsonResponse` com status de sucesso ou erro.

### 3.8. `get_responsaveis_por_pais(request)`

- **URL:** (Interno, usado por AJAX)
- **Métodos:** `GET`
- **Funcionalidade:** Retorna uma lista de responsáveis filtrados por um `country_id` específico, ou todos os responsáveis se nenhum `country_id` for fornecido. Usado para preencher dinamicamente dropdowns de responsáveis.

### 3.9. `get_paises_por_responsavel(request)`

- **URL:** (Interno, usado por AJAX)
- **Métodos:** `GET`
- **Funcionalidade:** Retorna uma lista de países para os quais um `responsavel_id` específico tem permissão, ou todos os países se nenhum `responsavel_id` for fornecido. Usado para preencher dinamicamente dropdowns de países.

### 3.10. `alterar_dados(request)`

- **URL:** `update_ocorrencia/`
- **Métodos:** `POST`
- **Funcionalidade:** Endpoint versátil para atualizar dados de uma ocorrência. Lida com `multipart/form-data` para upload/deleção de arquivos e com `application/json` para atualização de campos de texto, datas e Foreign Keys. Inclui lógica para limpar datas (`finished`, `deadline`) e reverter o país para o `country_original`.

### 3.11. `get_record(request, pk)`

- **URL:** `get_record/<int:pk>/`
- **Métodos:** `GET`
- **Funcionalidade:** Retorna os detalhes completos de uma ocorrência específica (identificada por `pk`) em formato JSON, incluindo `solution`. Se `solution` estiver vazio, procura a última mensagem do chat iniciada por `solução:`/`solucao:` e persiste no registro.

### 3.12. `criar_notificacao_feedback(record, tipo_feedback, gestor_user)`

Função auxiliar que cria uma notificação para o usuário responsável por uma ocorrência quando um gestor adiciona feedback. Evita duplicatas e notifica apenas usuários diferentes do gestor.

### 3.13. `listar_notificacoes(request)`

- **URL:** `notificacoes/`
- **Métodos:** `GET`
- **Funcionalidade:** Retorna uma lista de notificações não lidas para o usuário logado em formato JSON.

### 3.14. `marcar_notificacao_lida(request, notificacao_id)`

- **URL:** `notificacoes/<int:notificacao_id>/marcar_lida/`
- **Métodos:** `GET`
- **Funcionalidade:** Marca uma notificação específica como lida (e a exclui do banco de dados).

### 3.15. `marcar_notificacoes_por_record_como_lidas(request, record_id)`

- **URL:** `notificacoes/record/<int:record_id>/marcar_lidas/`
- **Métodos:** `GET`
- **Funcionalidade:** Marca todas as notificações não lidas associadas a um `record_id` específico como lidas (e as exclui).

### 3.16. `contar_notificacoes_nao_lidas(request)`

- **URL:** `notificacoes/contar/`
- **Métodos:** `GET`
- **Funcionalidade:** Retorna a contagem de notificações não lidas para o usuário logado em formato JSON.

### 3.17. `gerar_pdf_ocorrencia(request, record_id=None)`

- **URL:** `gerar_pdf/<int:record_id>/` (GET) e `gerar_pdf/` (POST)
- **Métodos:** `GET`, `POST`
- **Funcionalidade:** Gera um relatório PDF detalhado de uma ocorrência. Utiliza a biblioteca `reportlab` para criar o PDF, formatando os dados da ocorrência com quebras de linha automáticas para textos longos. Retorna o PDF como um anexo para download.

### 3.18. `download_arquivo(request, arquivo_id)`

- **URL:** `download_arquivo/<int:arquivo_id>/`
- **Métodos:** `GET`
- **Funcionalidade:** Permite o download seguro de um arquivo específico anexado a uma ocorrência. Verifica as permissões do usuário com base no país da ocorrência antes de permitir o download.

## 4. URLs

O aplicativo `ocorrencia_erro` define os seguintes padrões de URL:

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/` | `views.index` | `index` | Página inicial do sistema de ocorrências. |
| `subir_ocorrencia/` | `views.subir_ocorrencia` | `subir_ocorrencia` | Formulário para registrar novas ocorrências. |
| `filter_data/` | `views.filter_data_view` | `filter_data` | Endpoint AJAX para filtrar e ordenar ocorrências. |
| `update_ocorrencia/` | `views.alterar_dados` | `update_ocorrencia` | Endpoint para atualizar dados de ocorrências. |
| `criar_usuario/` | `views.criar_usuario` | `criar_usuario` | Formulário para criar novos usuários. |
| `login/` | `views.login_view` | `login_ocorrencias` | Página de login. |
| `logout/` | `views.logout_view` | `logout` | Endpoint para logout. |
| `download_arquivo/<int:arquivo_id>/` | `views.download_arquivo` | `download_arquivo` | Download de um arquivo anexado. |
| `get_record/<int:pk>/` | `views.get_record` | `get_record` | Obter detalhes de uma ocorrência via AJAX. |
| `notificacoes/` | `views.listar_notificacoes` | `listar_notificacoes` | Listar notificações não lidas. |
| `notificacoes/contar/` | `views.contar_notificacoes_nao_lidas` | `contar_notificacoes` | Contar notificações não lidas. |
| `notificacoes/<int:notificacao_id>/marcar_lida/` | `views.marcar_notificacao_lida` | `marcar_notificacao_lida` | Marcar notificação como lida. |
| `notificacoes/record/<int:record_id>/marcar_lidas/` | `views.marcar_notificacoes_por_record_como_lidas` | `marcar_notificacoes_record_lidas` | Marcar notificações de um registro como lidas. |
| `gerar_pdf/<int:record_id>/` | `views.gerar_pdf_ocorrencia` | `gerar_pdf_ocorrencia_get` | Gerar PDF de ocorrência (GET). |
| `gerar_pdf/` | `views.gerar_pdf_ocorrencia` | `gerar_pdf_ocorrencia_post` | Gerar PDF de ocorrência (POST). |
| `ocorrencia/download_todos/<int:record_id>/` | `views.download_todos_arquivos` | `download_todos_arquivos` | Download de todos os arquivos de uma ocorrência. |

## 6. Configuração (`apps.py`)

O arquivo `ocorrencia_erro/apps.py` configura o aplicativo e garante que os sinais sejam carregados corretamente.

```python
from django.apps import AppConfig


class OcorrenciaErroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ocorrencia_erro'
    verbose_name = 'Ocorrência de erros'

    def ready(self):
        """
        Este método é executado quando o aplicativo está pronto.
        É o local recomendado para importar os sinais.
        """
        import ocorrencia_erro.signals
```

- **`ready()` método:** Este método é sobrescrito para importar o módulo `ocorrencia_erro.signals`, garantindo que os sinais definidos no aplicativo sejam registrados e ativados quando o Django inicia. Isso é crucial para que a lógica de permissão da China seja aplicada automaticamente aos usuários.
