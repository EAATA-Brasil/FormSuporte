# Documentação do Aplicativo Django: Form

## 1. Visão Geral

O aplicativo `form` é responsável por gerenciar o cadastro e a exibição de informações sobre veículos. Ele permite o registro de dados detalhados de veículos, incluindo suas características, sistemas e métodos de programação de chaves. O aplicativo também oferece funcionalidades de filtragem e atualização de dados via interface web.

## 2. Modelos

Este aplicativo define o seguinte modelo para estruturar os dados:

### 2.1. `Veiculo`

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

**Funções Auxiliares:**

- `get_flat_choices()`: Transforma as escolhas definidas em `METHOD_CHOICES` (que categoriza métodos por OBD e BENCH) em uma lista de tuplas simples, adequada para campos `choices` do Django.

## 3. Forms

O aplicativo utiliza um formulário Django para facilitar a interação com o modelo `Veiculo`.

### 3.1. `VeiculoForm`

Um `ModelForm` baseado no modelo `Veiculo`, com customizações para campos `MultiSelectField` e `widgets`.

- **Campos Customizados:**
    - `add_key`, `read_password`, `remote_learning`, `keys_lost`: São definidos como `forms.MultipleChoiceField` com `CheckboxSelectMultiple` para permitir a seleção de múltiplas opções de métodos (OBD, Bench).
- **Widgets:** Define widgets HTML específicos para campos como `frequencia`, `tipo_chave`, `transponder` e `immo_part_replacement` para melhorar a experiência do usuário na interface.
- **Labels:** Customiza os rótulos exibidos para os campos `add_key`, `read_password`, `remote_learning` e `keys_lost`.

## 4. Views

As views gerenciam a lógica de apresentação e manipulação de dados.

### 4.1. `cadastrar_veiculo(request)`

- **URL:** `/cadastrar/`
- **Métodos:** `GET`, `POST`
- **Funcionalidade:**
    - `GET`: Exibe um formulário vazio (`VeiculoForm`) para o cadastro de um novo veículo.
    - `POST`: Processa os dados enviados pelo formulário. Se o formulário for válido, salva o novo veículo no banco de dados e exibe uma mensagem de sucesso. Caso contrário, exibe mensagens de erro.

### 4.2. `index(request)`

- **URL:** `/`
- **Métodos:** `GET`
- **Funcionalidade:**
    - Exibe uma lista paginada de veículos, com opções de filtragem por país, marca, modelo e ano.
    - Utiliza `Q` objects para construir filtros dinâmicos com base nos parâmetros da URL (`request.GET`).
    - Ordena os veículos por país, marca, modelo e ano.
    - Implementa paginação com 10 veículos por página.

### 4.3. `get_opcoes_filtro(request)`

- **URL:** `/get-opcoes/`
- **Métodos:** `GET`
- **Funcionalidade:**
    - Retorna opções de filtro (países, marcas, modelos, anos) em formato JSON, com base nos filtros já aplicados (`pais`, `marca`). Útil para preencher dinamicamente dropdowns de filtro na interface.

### 4.4. `update_vehicle(request)`

- **URL:** `/update-vehicle/`
- **Métodos:** `POST`
- **Funcionalidade:**
    - Recebe um ID de veículo, nome do campo e novo valor via POST.
    - Atualiza o campo especificado do veículo correspondente no banco de dados.
    - Retorna um `JsonResponse` indicando sucesso ou erro.

### 4.5. `update_vehicle_field(request)`

- **URL:** `/update-field/`
- **Métodos:** `POST`
- **Funcionalidade:**
    - Similar a `update_vehicle`, mas com uma lógica ligeiramente diferente para retornar o valor de exibição do campo atualizado, o que pode ser útil para campos com `choices`.

## 5. URLs

O aplicativo `form` define os seguintes padrões de URL:

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/` | `views.index` | `index_form` | Página inicial com a lista de veículos e filtros. |
| `cadastrar/` | `views.cadastrar_veiculo` | `cadastrar_veiculo` | Formulário para cadastrar novos veículos. |
| `get-opcoes/` | `views.get_opcoes_filtro` | `get_opcoes_filtro` | Endpoint AJAX para obter opções de filtro. |
| `update-vehicle/` | `views.update_vehicle` | `update_vehicle` | Endpoint AJAX para atualizar um campo de veículo. |
| `update-field/` | `views.update_vehicle_field` | `update_vehicle_field` | Endpoint AJAX para atualizar um campo de veículo e retornar o valor de exibição. |

