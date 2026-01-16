# EAATA – Sistema de Suporte (Monorepo)

Este repositório reúne várias apps Django que compõem o sistema de suporte da EAATA (ocorrências, situação por serial, simulador de propostas, API, etc.).

Leituras rápidas
- Instalação básica
  1) python -m venv env
  2) Ative o venv (Linux/macOS: source env/bin/activate | Windows PowerShell: .\\env\\Scripts\\Activate.ps1)
  3) pip install -r requirements.txt
  4) python manage.py migrate
  5) python manage.py createsuperuser
  6) python manage.py runserver
- WebSocket/Channels: em produção configure Redis; em dev a camada in-memory funciona para testes.
- Geração de PDF: WeasyPrint/ReportLab conforme cada app.

Documentação por app
- ocorrencia_erro/README.md – Gestão de ocorrências (chat, anexos, permissões, PDF).
- situacao_veiculo/README.md – Status de clientes por serial + sincronização Odoo.
- API/README.md – Endpoints REST e geração de PDF de simulação.
- simulador/README.md – Interface web do app móvel de simulação.
- serial_vci/README.md – Registros VCI com WebSockets e mídia.
- form/README.md – Base de dados de veículos.
- pedido/README.md – Fluxos de pedido/orçamento (se aplicável).

# FormSuporte

## Visão Geral do Projeto

O projeto `FormSuporte` é uma aplicação Django abrangente que integra diversas funcionalidades essenciais para a gestão de informações de veículos, suporte técnico, rastreamento de ocorrências e simulação de vendas. Ele é composto por múltiplos aplicativos Django, cada um com responsabilidades específicas, trabalhando em conjunto para fornecer uma solução robusta e interconectada.

## Estrutura do Projeto

O `FormSuporte` é modularizado em vários aplicativos Django, cada um focado em uma área de negócio:

*   **`form`**: Gerencia o cadastro e a exibição de informações detalhadas sobre veículos, incluindo características, sistemas e métodos de programação de chaves.
*   **`ocorrencia_erro`**: Um sistema robusto para gerenciar e rastrear ocorrências ou problemas, permitindo registro detalhado, atribuição a técnicos, prazos, status, upload de arquivos, comunicação via chat, controle de acesso baseado em permissões de país e grupos de usuários, notificações e geração de relatórios em PDF.
*   **`simulador`**: Serve como interface web para o `APP Simulador`, uma aplicação móvel desenvolvida com Expo para simulação de juros de vendas, incluindo entrada de dados financeiros, seleção de equipamentos e geração de PDFs.
*   **`situacao_veiculo`**: Projetado para verificar o status do suporte técnico de clientes com base no número de série de um equipamento, fornecendo informações sobre o cliente, data de vencimento do suporte e status atual (liberado, vencido ou a vencer).

## Aplicativos Detalhados

### 1. Aplicativo `form`

#### 1.1. Visão Geral

O aplicativo `form` é responsável por gerenciar o cadastro e a exibição de informações sobre veículos. Ele permite o registro de dados detalhados de veículos, incluindo suas características, sistemas e métodos de programação de chaves. O aplicativo também oferece funcionalidades de filtragem e atualização de dados via interface web.

#### 1.2. Modelos

##### `Veiculo`

Representa um veículo com diversas características, incluindo informações sobre chaves e transponders.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `pais` | `CharField(max_length=100)` | País de origem do veículo. |
| `brand` | `CharField(max_length=100)` | Marca do veículo. |
| `modelo` | `CharField(max_length=100)` | Modelo do veículo. |
| `ano` | `CharField(max_length=20)` | Ano de fabricação do veículo. |
| `sistema` | `CharField(max_length=100, null=True, blank=True)` | Sistema do veículo (opcional). |
| `tipo_chave` | `CharField(max_length=100, blank=True)` | Tipo de chave (ex: ID46, Crypto). |
| `transponder` | `CharField(max_length=100, blank=True)` | Tipo de transponder (ex: T5, Megamos). |
| `immo_part_replacement` | `CharField(max_length=1000, blank=True)` | Informações sobre substituição de peças IMMO. |
| `frequencia` | `CharField(max_length=3, choices=...)` | Frequência da chave (315 MHz ou 433 MHz). |
| `add_key` | `MultiSelectField(choices=...)` | Métodos para adicionar chave (OBD, Bench). |
| `read_password` | `MultiSelectField(choices=...)` | Métodos para leitura de senha. |
| `remote_learning` | `MultiSelectField(choices=...)` | Métodos para aprendizado remoto. |
| `key_lost` | `MultiSelectField(choices=...)` | Métodos para situação de todas as chaves perdidas. |

#### 1.3. Forms

##### `VeiculoForm`

Um `ModelForm` baseado no modelo `Veiculo`, com customizações para campos `MultiSelectField` e `widgets`.

#### 1.4. Views

*   **`cadastrar_veiculo(request)`**: Exibe e processa o formulário para cadastro de novos veículos.
*   **`index(request)`**: Exibe uma lista paginada de veículos com opções de filtragem.
*   **`get_opcoes_filtro(request)`**: Retorna opções de filtro (países, marcas, modelos, anos) em formato JSON.
*   **`update_vehicle(request)`**: Atualiza um campo específico de um veículo via AJAX.
*   **`update_vehicle_field(request)`**: Similar a `update_vehicle`, mas retorna o valor de exibição do campo atualizado.

#### 1.5. URLs

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/` | `views.index` | `index_form` | Página inicial com a lista de veículos e filtros. |
| `cadastrar/` | `views.cadastrar_veiculo` | `cadastrar_veiculo` | Formulário para cadastrar novos veículos. |
| `get-opcoes/` | `views.get_opcoes_filtro` | `get_opcoes_filtro` | Endpoint AJAX para obter opções de filtro. |
| `update-vehicle/` | `views.update_vehicle` | `update_vehicle` | Endpoint AJAX para atualizar um campo de veículo. |
| `update-field/` | `views.update_vehicle_field` | `update_vehicle_field` | Endpoint AJAX para atualizar um campo de veículo e retornar o valor de exibição. |

### 2. Aplicativo `ocorrencia_erro`

#### 2.1. Visão Geral

O aplicativo `ocorrencia_erro` é um sistema robusto para gerenciar e rastrear ocorrências ou problemas. Ele permite o registro detalhado de incidentes, atribuição a técnicos, definição de prazos, acompanhamento de status, upload de arquivos e comunicação via chat. O sistema também implementa um controle de acesso baseado em permissões de país e grupos de usuários, além de funcionalidades de notificação e geração de relatórios em PDF.

#### 2.2. Modelos

*   **`Country`**: Representa os países, utilizados para filtrar permissões e ocorrências.
*   **`Device`**: Representa os equipamentos associados às ocorrências.
*   **`CountryPermission`**: Define as permissões de acesso a países para usuários específicos.
*   **`Record`**: O modelo central que representa uma ocorrência ou problema, com campos para código externo, datas, técnico, responsável, equipamento, área, serial, marca, modelo, contato, ano, país, versão, problema detectado, status e feedbacks.
*   **`ArquivoOcorrencia`**: Armazena arquivos anexados a uma ocorrência.
*   **`Notificacao`**: Modelo para notificações de feedback em ocorrências.
*   **`ChatMessage`**: Modelo para mensagens de chat associadas a uma ocorrência.

#### 2.3. Views

As views gerenciam a lógica de apresentação e manipulação de dados, incluindo:

*   **`get_responsaveis()`**: Retorna responsáveis por país em JSON.
*   **`subir_arquivo(files, record)`**: Processa e salva múltiplos arquivos.
*   **`download_todos_arquivos(request, record_id)`**: Permite o download de todos os arquivos de uma ocorrência (ZIP se > 5 arquivos).
*   **`index(request)`**: Renderiza a página inicial do sistema de ocorrências com dados de permissões e estatísticas.
*   **`filter_data_view(request)`**: Endpoint AJAX para filtrar e ordenar ocorrências.
*   **`criar_usuario(request)`**: Permite a criação de novos usuários com atribuição de grupos e permissões de país.
*   **`subir_ocorrencia(request)`**: Permite o registro de novas ocorrências e upload de arquivos.
*   **`get_responsaveis_por_pais(request)`**: Retorna responsáveis filtrados por país.
*   **`get_paises_por_responsavel(request)`**: Retorna países permitidos para um responsável.
*   **`alterar_dados(request)`**: Endpoint versátil para atualizar dados de uma ocorrência, incluindo upload/deleção de arquivos.
*   **`get_record(request, pk)`**: Retorna detalhes completos de uma ocorrência em JSON.
*   **`criar_notificacao_feedback(...)`**: Função auxiliar para criar notificações de feedback.
*   **`listar_notificacoes(request)`**: Lista notificações não lidas para o usuário logado.
*   **`marcar_notificacao_lida(request, notificacao_id)`**: Marca uma notificação como lida.
*   **`marcar_notificacoes_por_record_como_lidas(request, record_id)`**: Marca todas as notificações de um registro como lidas.
*   **`contar_notificacoes_nao_lidas(request)`**: Retorna a contagem de notificações não lidas.
*   **`gerar_pdf_ocorrencia(request, record_id=None)`**: Gera um relatório PDF detalhado de uma ocorrência.
*   **`download_arquivo(request, arquivo_id)`**: Permite o download seguro de um arquivo específico.

#### 2.4. URLs

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/` | `views.index` | `index` | Página inicial do sistema de ocorrências. |
| `subir_ocorrencia/` | `views.subir_ocorrencia` | `subir_ocorrencia` | Formulário para registrar novas ocorrências. |
| `filter_data/` | `views.filter_data_view` | `filter_data` | Endpoint AJAX para filtrar e ordenar ocorrências. |
| `update_ocorrencia/` | `views.alterar_dados` | `update_ocorrencia` | Endpoint para atualizar dados de uma ocorrência. |
| `criar_usuario/` | `views.criar_usuario` | `criar_usuario` | Formulário para criar novos usuários. |
| `login/` | `views.login_view` | `login_ocorrencias` | Página de login. |
| `logout/` | `views.logout_view` | `logout` | Endpoint para logout. |
| `download_arquivo/<int:arquivo_id>/` | `views.download_arquivo` | `download_arquivo` | Download de um arquivo anexado. |
| `get_record/<int:pk>/` | `views.get_record` | `get_record` | Obter detalhes de uma ocorrência via AJAX. |
| `notificacoes/` | `views.listar_notificacoes` | `listar_notificacoes` | Listar notificações não lidas. |
| `notificacoes/contar/` | `views.contar_notificacoes_nao_lidas` | `contar_notificacoes` | Contar notificações não lidas. |
| `notificacoes/<int:notificacao_id>/marcar_lida/` | `views.marcar_notificacao_lida` | `marcar_notificacao_lida` | Marcar notificação como lida. |
| `notificacoes/record/<int:record_id>/marcar_lidas/` | `views.marcar_notificacoes_record_lidas` | `marcar_notificacoes_record_lidas` | Marcar notificações de um registro como lidas. |
| `gerar_pdf/<int:record_id>/` | `views.gerar_pdf_ocorrencia` | `gerar_pdf_ocorrencia_get` | Gerar PDF de ocorrência (GET). |
| `gerar_pdf/` | `views.gerar_pdf_ocorrencia` | `gerar_pdf_ocorrencia_post` | Gerar PDF de ocorrência (POST). |
| `ocorrencia/download_todos/<int:record_id>/` | `views.download_todos_arquivos` | `download_todos_arquivos` | Download de todos os arquivos de uma ocorrência. |

### 3. Aplicativo `simulador`

#### 3.1. Visão Geral

O aplicativo `simulador` tem como funcionalidade servir uma interface web para o projeto `APP Simulador`. Este, por sua vez, é uma aplicação móvel desenvolvida com Expo, focada na simulação de juros de vendas. Ele utiliza o roteamento baseado em arquivos do Expo Router e inclui componentes para entrada de dados financeiros, seleção de equipamentos e geração de PDFs.

#### 3.2. Views

Sua view oferece apenas um roteamento para `templates/simulador` que está na seguinte árvore:

```
templates/
├── _sitemap.html
├── +not-found.html
├── index.html
├── simulador/
│   ├── index.html
```

Os arquivos são gerados pelo comando `npx expo export -p web`.

#### 3.3. Static

Por ser um sistema desenvolvido em Expo, o arquivo JS gerado está na pasta `static` deste projeto.

#### 3.4. Observação

*   Existem dois arquivos `index.html` devido a um erro de desenvolvimento, o que é uma observação para futuras correções.
*   Para detalhes sobre o funcionamento, consulte a documentação do aplicativo `APP Simulador`.

### 4. Aplicativo `situacao_veiculo`

#### 4.1. Visão Geral

O aplicativo `situacao_veiculo` é projetado para verificar o status do suporte técnico de clientes com base no número de série de um equipamento. Ele permite que os usuários insiram um número de série e recebam informações sobre o cliente associado, a data de vencimento do suporte e o status atual (liberado, vencido ou a vencer), com mensagens claras para orientar o atendimento.

#### 4.2. Modelos

##### `Cliente`

Representa um cliente e as informações de seu equipamento, incluindo o status do suporte.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `data` | `DateField` | Data de registro do cliente/equipamento. |
| `vencimento` | `DateField(blank=True, null=True)` | Data de vencimento do suporte. Calculado automaticamente se não for fornecido. |
| `anos_para_vencimento` | `PositiveIntegerField(default=2)` | Quantidade de anos padrão para o cálculo do vencimento a partir da `data`. |
| `serial` | `CharField(max_length=100, blank=True, null=True)` | Número de série do equipamento. Deve ser único. |
| `nome` | `CharField(max_length=100)` | Nome do cliente. |
| `cnpj` | `CharField(max_length=30, blank=True, default="SEM DADO")` | CPF ou CNPJ do cliente. |
| `tel` | `CharField(max_length=30, blank=True, default="SEM DADO")` | Telefone do cliente. |
| `equipamento` | `CharField(max_length=100, blank=True, default="")` | Nome do equipamento. |

#### 4.3. Views

*   **`buscar_serial(request)`**: Recebe um número de série via `POST`, pesquisa clientes e retorna o status do suporte (nenhum encontrado, múltiplos ou um cliente encontrado) com mensagens explicativas.
*   **`index(request)`**: Renderiza a página inicial do aplicativo, aguardando a entrada de um número de série para busca.

#### 4.4. URLs

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/` | `views.index` | `index` | Página inicial para verificar o status do suporte. |
| `buscar/` | `views.buscar_serial` | `buscar_serial` | Endpoint para buscar o status do suporte por número de série. |

## Configuração Geral

O projeto `FormSuporte` é uma aplicação Django. A configuração principal (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`) está localizada no diretório `FormSuporte/FormSuporte/`.

Cada aplicativo (`form`, `ocorrencia_erro`, `simulador`, `situacao_veiculo`) possui seu próprio arquivo `apps.py` para configuração específica do aplicativo, incluindo `verbose_name` e importação de sinais (como em `ocorrencia_erro`) para garantir o carregamento correto da lógica de negócio.

## 🌍 Tradução e Internacionalização (i18n)

O projeto utiliza o sistema de tradução do **Django**, permitindo exibir textos em diferentes idiomas.

---

### 🔹 1. Marcar textos nos templates

No início do template adicione:
{% load i18n %}

Exemplo com `trans`:
<h1>{% trans "Bem-vindo" %}</h1>
<p>{% trans "Clique no botão para continuar." %}</p>

Exemplo com `blocktrans` (com variável):
{% load i18n %}
{% blocktrans with user_name=request.user.first_name %}
Olá, {{ user_name }}! Seu painel está pronto.
{% endblocktrans %}

Exemplo com pluralização:
{% load i18n %}
{% blocktrans count total=itens|length %}
Você tem {{ total }} item no carrinho.
{% plural %}
Você tem {{ total }} itens no carrinho.
{% endblocktrans %}

---

### 🔹 2. Marcar textos no código Python

from django.utils.translation import gettext as _
# ou, para uso preguiçoso (modelos/forms):
# from django.utils.translation import gettext_lazy as _

titulo = _("Relatório de Ocorrências")
mensagem = _("Arquivo gerado com sucesso.")

---

### 🔹 3. Configuração no settings.py

USE_I18N = True

LANGUAGE_CODE = "pt-br"

LANGUAGES = [
    ("pt-br", "Português (Brasil)"),
    ("en", "English"),
    # adicione outros idiomas se necessário
]

LOCALE_PATHS = [
    BASE_DIR / "locale",  # pasta onde ficarão os arquivos de tradução
]

No MIDDLEWARE, o LocaleMiddleware deve vir após SessionMiddleware e CommonMiddleware:
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # ...
]

---

### 🔹 4. Gerar e compilar traduções

Execute na raiz do projeto (onde está o manage.py):

django-admin makemessages --all --ignore=env
django-admin compilemessages

Esses comandos:
- Criam/atualizam os arquivos .po em locale/<idioma>/LC_MESSAGES/
- Compilam os arquivos .mo usados pelo Django em runtime

Dicas:
- Para um idioma específico: django-admin makemessages -l en --ignore=env
- Em Windows, se necessário, use: python manage.py makemessages ... / python manage.py compilemessages

---

### 🔹 5. Troca de idioma no site (opcional)

Formulário para trocar o idioma usando a view set_language do Django:

<form action="{% url 'set_language' %}" method="post">
  {% csrf_token %}
  <select name="language">
    <option value="pt-br">Português (Brasil)</option>
    <option value="en">English</option>
  </select>
  <button type="submit">{% trans "Alterar idioma" %}</button>
</form>

---

✅ Resumo rápido:
1) Use {% trans "texto" %} ou {% blocktrans %} nos templates
2) Use _() no Python
3) Ajuste USE_I18N, LANGUAGES e LOCALE_PATHS
4) Rode: django-admin makemessages --all --ignore=env && django-admin compilemessages


## Como Contribuir

Informações sobre como configurar o ambiente de desenvolvimento, executar testes e contribuir para o projeto serão adicionadas em futuras atualizações deste README. Por enquanto, consulte os arquivos de código-fonte e os READMEs específicos de cada aplicativo para obter mais detalhes.
