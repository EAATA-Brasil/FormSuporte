# Documentação do Aplicativo Django: API

## 1. Visão Geral

O aplicativo `API` é responsável por fornecer uma interface RESTful para a gestão de dados de equipamentos, incluindo seus tipos, marcas e detalhes específicos. Além disso, ele oferece uma funcionalidade para gerar relatórios em PDF com base em dados de simulação de vendas.

## 2. Modelos

Este aplicativo define os seguintes modelos para estruturar os dados:

### 2.1. `TipoEquipamento`

Representa as categorias ou grupos de equipamentos. Por exemplo, "diagnóstico" ou "imobilizador".

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `nome` | `CharField(max_length=100)` | Nome do tipo de equipamento. |

### 2.2. `MarcaEquipamento`

Representa as marcas dos equipamentos.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `nome` | `CharField(max_length=30)` | Nome da marca do equipamento. |

### 2.3. `Equipamentos`

Representa um equipamento individual, associando-o a um tipo e uma marca, e contendo detalhes financeiros e de disponibilidade.

| Campo | Tipo de Dado | Descrição |
|---|---|---|
| `nome` | `CharField(max_length=100)` | Nome comercial do equipamento. |
| `marca` | `ForeignKey(MarcaEquipamento)` | Chave estrangeira para a marca do equipamento. |
| `grupo` | `ForeignKey(TipoEquipamento)` | Chave estrangeira para o tipo/grupo do equipamento. |
| `custo` | `FloatField(blank=True, null=True)` | Custo do equipamento (geral). |
| `custo_geral` | `FloatField` | Valor do equipamento dentro de SP. |
| `custo_cnpj` | `FloatField` | Valor do equipamento para CNPJ fora de SP. |
| `custo_cpf` | `FloatField` | Valor do equipamento para CPF fora de SP. |
| `entrada_sp_cnpj` | `FloatField(blank=True, null=True)` | Entrada padrão para SP com CNPJ. |
| `entrada_outros_cnpj` | `FloatField(blank=True, null=True)` | Entrada padrão para outros estados com CNPJ. |
| `entrada_outros_cpf` | `FloatField(blank=True, null=True)` | Entrada padrão para outros estados com CPF. |
| `parcelas` | `FloatField(blank=True, null=True)` | Quantidade de parcelas padrão. |
| `disponibilidade` | `BooleanField(default=True)` | Indica se o equipamento está disponível. |
| `avista` | `BooleanField(default=False)` | Indica se a venda é apenas à vista. |
| `boleto` | `BooleanField(default=True)` | Indica se aceita parcelamento no boleto. |
| `detalhes` | `TextField(blank=True, null=True)` | Detalhes do equipamento (formato WhatsApp). |
| `detalhes_html` | `TextField(editable=False, blank=True, null=True)` | Detalhes convertidos para HTML. |
| `detalhes_sp` | `TextField(blank=True, null=True)` | Detalhes do equipamento (SP, formato WhatsApp). |
| `detalhes_sp_html` | `TextField(editable=False, blank=True, null=True)` | Detalhes SP convertidos para HTML. |

**Métodos Especiais:**

- `save()`: Converte automaticamente os campos `detalhes` e `detalhes_sp` de formato WhatsApp para HTML antes de salvar. Utiliza o método estático `_convert_whatsapp_to_html`.
- `formatted_detalhes()`: Retorna os `detalhes_html` formatados para exibição no admin.
- `formatted_detalhes_sp()`: Retorna os `detalhes_sp_html` formatados para exibição no admin.
- `_convert_whatsapp_to_html(text)`: Método estático que converte texto com formatação estilo WhatsApp (negrito, itálico, tachado, monoespaçado, listas e URLs) para HTML.

## 3. Serializers

Os serializers são usados para converter instâncias de modelos em formatos JSON e vice-versa, facilitando a interação com a API RESTful.

### 3.1. `TipoEquipamentoSerializer`

Serializa o modelo `TipoEquipamento`.

| Campo | Descrição |
|---|---|
| `__all__` | Inclui todos os campos do modelo `TipoEquipamento`. |

### 3.2. `MarcaEquipamentoSerializer`

Serializa o modelo `MarcaEquipamento`.

| Campo | Descrição |
|---|---|
| `__all__` | Inclui todos os campos do modelo `MarcaEquipamento`. |

### 3.3. `EquipamentosSerializer`

Serializa o modelo `Equipamentos`.

| Campo | Descrição |
|---|---|
| `tipo` | Campo de leitura (`read_only=True`) que serializa o `TipoEquipamento` relacionado. |
| `__all__` | Inclui todos os outros campos do modelo `Equipamentos`. |

## 4. Views

As views definem a lógica de negócio e os endpoints da API.

### 4.1. `EquipamentosViewSet`

Um `ReadOnlyModelViewSet` que fornece operações de listagem e recuperação de instâncias do modelo `Equipamentos`.

- **Endpoint:** `/api/equipamentos/`
- **Métodos:** `GET` (lista todos os equipamentos), `GET /<id>/` (recupera um equipamento específico).

### 4.2. `TipoEquipamentoViewSet`

Um `ReadOnlyModelViewSet` que fornece operações de listagem e recuperação de instâncias do modelo `TipoEquipamento`.

- **Endpoint:** `/api/tiposEquipamento/`
- **Métodos:** `GET` (lista todos os tipos de equipamento), `GET /<id>/` (recupera um tipo específico).

### 4.3. `MarcaEquipamentoViewSet`

Um `ReadOnlyModelViewSet` que fornece operações de listagem e recuperação de instâncias do modelo `MarcaEquipamento`.

- **Endpoint:** `/api/marcasEquipamento/`
- **Métodos:** `GET` (lista todas as marcas de equipamento), `GET /<id>/` (recupera uma marca específica).

### 4.4. `generate_pdf(request)`

Uma view de API que gera um documento PDF com base em dados de simulação de vendas fornecidos via POST.

- **Endpoint:** `/api/generate-pdf/`
- **Métodos:** `POST`
- **Funcionalidade:**
    - Recebe dados de simulação (equipamentos, quantidades, localização, faturamento, descontos, etc.).
    - Calcula valores unitários e totais com base na localização (SP ou outros estados) e tipo de faturamento (CPF/CNPJ).
    - Formata valores monetários para o padrão brasileiro.
    - Renderiza um template HTML (`api/pdf_simulador.html`) com os dados processados.
    - Converte o HTML renderizado para PDF usando a biblioteca WeasyPrint.
    - Retorna o PDF como um anexo para download. Em caso de falha na geração do PDF, retorna o HTML para depuração.
- **Dependências:** WeasyPrint (configuração específica para Windows e Linux).

## 5. URLs

O aplicativo `API` define os seguintes padrões de URL:

| Padrão de URL | View Associada | Nome da URL | Descrição |
|---|---|---|---|
| `/` | `router.urls` | (gerado pelo router) | Inclui os endpoints para `EquipamentosViewSet`, `TipoEquipamentoViewSet` e `MarcaEquipamentoViewSet`. |
| `generate-pdf/` | `views.generate_pdf` | `generate_pdf` | Endpoint para gerar relatórios PDF de simulação. |


