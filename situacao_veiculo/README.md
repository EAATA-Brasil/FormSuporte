# Documentação do Aplicativo Django: `situacao_veiculo`

## 1. Visão Geral

O aplicativo **`situacao_veiculo`** gerencia o status de suporte técnico de clientes com base no número de série dos equipamentos.

Com a versão atual, ele passou a contar com recursos **interativos e automatizados**, incluindo:
- Consulta rápida do status de suporte;
- Cadastro de novos clientes (popup AJAX);
- Atualização automática de dados com observer e autosave;
- Recarregamento dinâmico da página após fechamento dos popups;
- Controle de acesso (botão de atualização visível apenas para superusuários);
- Feedback visual (banners de erro, sucesso e informação).

---

## 2. Modelo de Dados

### 2.1. `Cliente`

Representa o cliente e os dados do equipamento, com controle de vencimento e status.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `data` | `DateField` | Data de registro. |
| `vencimento` | `DateField(blank=True, null=True)` | Data de vencimento do suporte, calculada automaticamente. |
| `anos_para_vencimento` | `PositiveIntegerField(default=2)` | Quantidade de anos para o vencimento. |
| `serial` | `CharField(max_length=100, unique=True)` | Número de série do equipamento (chave principal). |
| `nome` | `CharField(max_length=100)` | Nome do cliente. |
| `cnpj` | `CharField(max_length=30, blank=True, default="SEM DADO")` | CPF/CNPJ do cliente. |
| `tel` | `CharField(max_length=30, blank=True, default="SEM DADO")` | Telefone do cliente. |
| `equipamento` | `CharField(max_length=100, blank=True, default="")` | Equipamento associado. |

**Métodos Especiais**
- `clean()`: Garante unicidade do `serial`.
- `save()`: Calcula o vencimento automático com base em `anos_para_vencimento`.

---

## 3. Views

### 3.1. `index(request)`
- **URL:** `/situacao`
- **Método:** `GET`
- **Função:** Renderiza a página principal (`situacao/index.html`) com o formulário de busca, status e botões para cadastrar/atualizar.

---

### 3.2. `buscar_serial(request)`
- **URL:** `/situacao/buscar/`
- **Método:** `POST`
- **Função:** Busca um cliente pelo número de série e retorna:
  - Nenhum cliente → “Sem dados”;
  - Múltiplos → tabela de duplicatas;
  - Um cliente → dados e status (ativo, vencido, a vencer).

---

### 3.3. `cadastrar_serial(request)`
- **URL:** `/situacao/cadastrar/`
- **Método:** `POST`
- **Função:** Cadastra um novo cliente (via popup AJAX).

**Fluxo AJAX:**
- Envia o formulário sem recarregar a página;
- Valida campos obrigatórios e unicidade de `serial`;
- Retorna mensagens dinâmicas de erro/sucesso;
- Após sucesso, **fecha o popup e atualiza automaticamente a tela principal** com o novo serial.

**Exemplo de retorno:**
```json
{ "ok": true, "message": "Cadastro realizado com sucesso!" }
```

---

### 3.4. `api_buscar_cliente(request)`
- **URL:** `/situacao/api/cliente`
- **Método:** `GET`
- **Função:** Busca um cliente específico com base no `serial`, usada pelo popup de atualização.

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
- **Função:** Atualiza dinamicamente campos (`nome`, `cnpj`, `tel`, `equipamento`) conforme o usuário edita.
- Usa autosave com debounce (400ms).
- Após o fechamento do popup, a página principal recarrega com os dados atualizados.

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

| Rota | View | Nome | Descrição |
|---|---|---|---|
| `/situacao` | `index` | `index` | Página inicial. |
| `/situacao/buscar/` | `buscar_serial` | `buscar_serial` | Busca por número de série. |
| `/situacao/cadastrar/` | `cadastrar_serial` | `cadastrar_serial` | Cadastro via popup AJAX. |
| `/situacao/api/cliente` | `api_buscar_cliente` | `api_buscar_cliente` | Busca dinâmica por serial. |
| `/situacao/api/cliente/update` | `api_atualizar_cliente` | `api_atualizar_cliente` | Atualização automática (autosave). |

---

## 5. Controle de Acesso

O botão **“Atualizar Serial”** aparece apenas para usuários com permissão de **superusuário**:

```html
{% if request.user.is_superuser %}
<button id="abrirPopupUpdate" class="btn-popup">Atualizar Serial</button>
{% endif %}
```

Usuários comuns visualizam apenas o botão **“Novo Serial”**.

---

## 6. Observers e Automatizações

### 6.1. `IntersectionObserver`
- Observa quando o popup de atualização fica visível.
- Assim que aparece, busca automaticamente o cliente pelo serial atual.

```js
const io = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) {
      const s = serialInput.value.trim();
      if (s) fetchBySerial(s);
    }
  }
}, { threshold: 0.1 });
```

---

### 6.2. Observador de Fechamento de Popups
- Quando o popup **de criação** fecha após sucesso, chama `refreshMain(serial)` para atualizar a tela principal.
- Quando o popup **de atualização** é fechado (por X, botão, clique fora ou ESC), chama `refreshMain(serialAtual)` para buscar os dados atualizados no backend.

---

### 6.3. Autosave
- Cada campo (`nome`, `cnpj`, `tel`) tem um **observer** que envia o valor ao servidor 400ms após parar de digitar.
- Feedback visual:
  - **Azul:** carregando/buscando;
  - **Verde:** salvo;
  - **Vermelho:** erro.

---

## 7. Estrutura do Template

```
situacao/
├── templates/
│   └── situacao/
│       └── index.html     # Página principal (busca, popups e JS)
└── static/
    └── situacao/
        ├── css/
        │   └── style.css  # Estilos visuais e banners
        └── js/
            └── scripts.js # (opcional) lógica separada de popups e autosave
```

---

## 8. Configuração (`apps.py`)

```python
from django.apps import AppConfig

class SituacaoVeiculoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'situacao_veiculo'
    verbose_name = 'Verificar suporte'
```

---

## 9. Conclusão

O aplicativo **`situacao_veiculo`** combina **backend robusto (Django)** com uma **interface reativa e intuitiva** em JavaScript.  
Os novos observers, autosave e recarregamento automático tornam a operação mais eficiente, garantindo que todas as informações estejam sempre sincronizadas e atualizadas sem recarregamentos manuais de página.
