# Documentação do Aplicativo Django: situacao_veiculo

## 1. Visão Geral

O aplicativo `situacao_veiculo` é projetado para verificar o status do suporte técnico de clientes com base no número de série de um equipamento. Ele permite que os usuários insiram um número de série e recebam informações sobre o cliente associado, a data de vencimento do suporte e o status atual (liberado, vencido ou a vencer), com mensagens claras para orientar o atendimento.

## 2. Modelos

Este aplicativo define o seguinte modelo para estruturar os dados:

### 2.1. `Cliente`

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

**Métodos Especiais:**

- `clean()`: Realiza validações antes de salvar, garantindo que o `serial` seja único para cada cliente.
- `save()`: Sobrescreve o método `save` para chamar `clean()` e, se a data de `vencimento` não for fornecida, calcula-a automaticamente com base na `data` de registro e nos `anos_para_vencimento` usando `dateutil.relativedelta`.

## 3. Views

As views gerenciam a lógica de apresentação e manipulação de dados.

### 3.1. `buscar_serial(request)`

- **URL:** `/situacao/buscar/`
- **Métodos:** `POST`
- **Funcionalidade:**
    - Recebe um número de série via `POST`.
    - Pesquisa clientes com o número de série fornecido.
    - **Cenários:**
        - **Nenhum cliente encontrado:** Retorna uma mensagem indicando que não há dados e que o comercial deve atualizar o cadastro.
        - **Múltiplos clientes encontrados (duplicatas):** Exibe uma lista de todos os clientes encontrados para o serial, cada um com seu status de suporte (liberado, vencido, a vencer) e uma mensagem explicativa. Isso permite ao usuário identificar qual registro é o correto ou lidar com a duplicidade.
        - **Um cliente encontrado:** Calcula o status do suporte com base na data de vencimento e na data atual. Retorna o status (`direito`, `vencido`, `vencendo`) e mensagens correspondentes para o template `situacao/index.html`.
    - Redireciona para a página inicial (`index`) se acessado via `GET`.

### 3.2. `index(request)`

- **URL:** `/situacao`
- **Métodos:** `GET`
- **Funcionalidade:** Renderiza a página inicial do aplicativo (`situacao/index.html`). Inicialmente, não exibe nenhum cliente, aguardando a entrada de um número de série para busca.

## 4. URLs

O aplicativo `situacao_veiculo` define os seguintes padrões de URL:

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/situacao` | `views.index` | `index` | Página inicial para verificar o status do suporte. |
| `/situacao/buscar/` | `views.buscar_serial` | `buscar_serial` | Endpoint para buscar o status do suporte por número de série. |

## 5. Configuração (`apps.py`)

O arquivo `situacao_veiculo/apps.py` contém a configuração padrão para o aplicativo Django.

```python
from django.apps import AppConfig


class SituacaoVeiculoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'situacao_veiculo'
    verbose_name= 'Verificar suporte'
```

- **`default_auto_field`**: Define o tipo de campo automático padrão para chaves primárias. Neste caso, `BigAutoField`.
- **`name`**: O nome do aplicativo Django, que é `situacao_veiculo`.
- **`verbose_name`**: Um nome mais legível para o aplicativo, exibido em interfaces como o Django Admin, que é "Verificar suporte".

## 6. Conclusão

O aplicativo `situacao_veiculo` é uma ferramenta focada em agilizar a consulta do status de suporte técnico de equipamentos, fornecendo informações rápidas e claras para a equipe de atendimento. Sua lógica de validação de serial único e cálculo automático de vencimento contribui para a integridade dos dados e a eficiência do processo.
