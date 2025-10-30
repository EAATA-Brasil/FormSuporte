# Documentação do Aplicativo Django: `situacao_veiculo`

## 1. Visão Geral

O aplicativo **`situacao_veiculo`** tem como objetivo verificar e gerenciar o status de suporte técnico de clientes com base no número de série dos equipamentos.  

Agora, o sistema conta com **recursos interativos**:
- Consulta do status via número de série;
- Cadastro de novos clientes diretamente pela interface (popup);
- Atualização automática de dados em tempo real (observer/autosave);
- Retorno visual imediato (mensagens de sucesso, erro e informação).

---

## 2. Modelo de Dados

### 2.1. `Cliente`

Representa o cliente e as informações de seu equipamento, além dos campos para controle de vencimento e status de suporte.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `data` | `DateField` | Data de registro do cliente. |
| `vencimento` | `DateField(blank=True, null=True)` | Data de vencimento do suporte, calculada automaticamente. |
| `anos_para_vencimento` | `PositiveIntegerField(default=2)` | Número de anos usado para calcular o vencimento a partir da `data`. |
| `serial` | `CharField(max_length=100, unique=True)` | Número de série do equipamento (chave principal para buscas). |
| `nome` | `CharField(max_length=100)` | Nome do cliente. |
| `cnpj` | `CharField(max_length=30, blank=True, default="SEM DADO")` | CPF/CNPJ do cliente. |
| `tel` | `CharField(max_length=30, blank=True, default="SEM DADO")` | Telefone do cliente. |
| `equipamento` | `CharField(max_length=100, blank=True, default="")` | Nome do equipamento. |

**Métodos Especiais:**
- `clean()`: Garante unicidade do `serial`.
- `save()`: Calcula o vencimento automaticamente com base em `anos_para_vencimento`.

---

## 3. Views

### 3.1. `index(request)`

- **URL:** `/situacao`
- **Método:** `GET`
- **Função:** Renderiza a página principal (`situacao/index.html`), que exibe o formulário de busca e os botões para cadastrar ou atualizar dados via popup.

---

### 3.2. `buscar_serial(request)`

- **URL:** `/situacao/buscar/`
- **Método:** `POST`
- **Função:** Recebe um número de série e retorna:
  - **Nenhum cliente:** Mensagem “Sem dados”.
  - **Múltiplos clientes:** Exibe tabela com duplicatas.
  - **Um cliente:** Exibe dados e status (ativo, vencido, a vencer).

---

### 3.3. `cadastrar_serial(request)`

- **URL:** `/situacao/cadastrar/`
- **Método:** `POST`
- **Função:** Cadastra um novo cliente.
- **Fluxo AJAX (via popup):**
  - Envia dados sem recarregar a página.
  - Valida campos obrigatórios e unicidade do `serial`.
  - Exibe mensagens dinâmicas no popup (erro, sucesso, aviso).

**Retornos JSON:**
```json
{ "ok": true, "message": "Cadastro realizado com sucesso!" }
{ "ok": false, "message": "Serial já em uso.", "field_errors": {"serial": "Serial já cadastrado."} }
```

---

### 3.4. `api_buscar_cliente(request)`

- **URL:** `/situacao/api/cliente`
- **Método:** `GET`
- **Parâmetros:** `?serial=<valor>`
- **Função:** Retorna os dados de um cliente específico, usado pelo popup de atualização.

**Exemplo de resposta:**
```json
{
  "ok": true,
  "data": {
    "serial": "12345",
    "nome": "Cliente Exemplo",
    "cnpj": "00000000000000",
    "tel": "(11) 99999-9999",
    "equipamento": "EAATA Reader"
  }
}
```

---

### 3.5. `api_atualizar_cliente(request)`

- **URL:** `/situacao/api/cliente/update`
- **Método:** `POST`
- **Função:** Atualiza dinamicamente os campos de um cliente conforme o usuário edita os inputs no popup.
- **Funcionamento:** Cada campo é salvo automaticamente (autosave) após 400ms sem digitação.

**Exemplo de payload:**
```json
{
  "serial": "12345",
  "field": "nome",
  "value": "Novo Nome"
}
```

---

## 4. URLs

| Padrão | View | Nome | Descrição |
|---|---|---|---|
| `/situacao` | `index` | `index` | Página inicial. |
| `/situacao/buscar/` | `buscar_serial` | `buscar_serial` | Busca por número de série. |
| `/situacao/cadastrar/` | `cadastrar_serial` | `cadastrar_serial` | Cadastro de novos clientes. |
| `/situacao/api/cliente` | `api_buscar_cliente` | `api_buscar_cliente` | Endpoint de busca dinâmica. |
| `/situacao/api/cliente/update` | `api_atualizar_cliente` | `api_atualizar_cliente` | Endpoint de atualização automática. |

---

## 5. Interações no Frontend

### 5.1. Cadastro (Popup “Novo Serial”)
- Abre modal para inserir novos dados.
- Envio AJAX (`fetch`) para `/cadastrar/`.
- Mensagens de feedback visual (erro/sucesso) no próprio popup e no rodapé da página.

### 5.2. Atualização (Popup “Atualizar Serial”)
- Campo “Serial” com **observer**: busca automática ao parar de digitar.
- Campos carregados (`nome`, `cnpj`, `tel`) são **autosalvos** conforme o usuário edita.
- Feedback visual:
  - Azul → Informação (buscando, carregando);
  - Verde → Sucesso (salvo);
  - Vermelho → Erro (falha, serial inexistente).

---

## 6. Configuração do App (`apps.py`)

```python
from django.apps import AppConfig

class SituacaoVeiculoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'situacao_veiculo'
    verbose_name = 'Verificar suporte'
```

---

## 7. Estrutura de Templates

```
situacao/
├── templates/
│   └── situacao/
│       └── index.html   # Página principal com popups e interações
└── static/
    └── situacao/
        └── css/
            └── style.css # Estilos visuais e responsividade
```

---

## 8. Conclusão

O aplicativo **`situacao_veiculo`** é uma ferramenta moderna e eficiente para controle de suporte técnico, unindo **Django (backend)** e **JavaScript (frontend)** de forma integrada.  
Os novos recursos de **validação dinâmica** e **autosave** proporcionam uma experiência fluida e produtiva, eliminando a necessidade de recarregar a página e garantindo agilidade no atendimento e manutenção dos cadastros.
