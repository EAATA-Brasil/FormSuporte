# Documentação da Aplicação API (Simulador)

## Visão Geral

A aplicação `API` (referida como `simulador` pelo frontend Expo) atua como o **backend** para o aplicativo frontend desenvolvido em Expo. Sua principal responsabilidade é fornecer dados de equipamentos e, crucialmente, gerar relatórios de simulação de vendas em formato PDF.

Ela expõe endpoints RESTful para consulta de dados mestres (equipamentos, tipos e marcas) e um endpoint específico para a geração de PDFs de simulações de venda, que são consumidos diretamente pelo aplicativo Expo.

## Estrutura do Projeto

- `models.py`: Define os modelos de dados para `Equipamentos`, `TipoEquipamento` e `MarcaEquipamento`.
- `serializers.py`: Contém os serializadores Django REST Framework para converter os modelos em formatos JSON e vice-versa.
- `views.py`: Implementa as ViewSets para os modelos e a lógica para a geração de PDF.
- `urls.py`: Define as rotas da API.

## Endpoints da API

A API expõe os seguintes endpoints:

### Equipamentos

- **GET `/api/equipamentos/`**
  - **Descrição**: Lista todos os equipamentos disponíveis.
  - **Método**: `GET`
  - **Autenticação**: Não requer autenticação (ReadOnlyModelViewSet).
  - **Resposta**: Uma lista de objetos `Equipamentos` serializados.

- **GET `/api/equipamentos/{id}/`**
  - **Descrição**: Recupera os detalhes de um equipamento específico pelo seu ID.
  - **Método**: `GET`
  - **Autenticação**: Não requer autenticação.
  - **Resposta**: Um objeto `Equipamentos` serializado.

### Tipos de Equipamento

- **GET `/api/tiposEquipamento/`**
  - **Descrição**: Lista todos os tipos de equipamento disponíveis.
  - **Método**: `GET`
  - **Autenticação**: Não requer autenticação.
  - **Resposta**: Uma lista de objetos `TipoEquipamento` serializados.

### Marcas de Equipamento

- **GET `/api/marcasEquipamento/`**
  - **Descrição**: Lista todas as marcas de equipamento disponíveis.
  - **Método**: `GET`
  - **Autenticação**: Não requer autenticação.
  - **Resposta**: Uma lista de objetos `MarcaEquipamento` serializados.

### Geração de PDF de Simulação

- **POST `/api/generate-pdf/`**
  - **Descrição**: Gera um relatório de simulação de vendas em formato PDF com base nos dados fornecidos.
  - **Método**: `POST`
  - **Autenticação**: Não requer autenticação (pode ser ajustado conforme necessidade).
  - **Corpo da Requisição (JSON)**:
    ```json
    {
      "equipamentos": ["id_equipamento_1", "id_equipamento_2"],
      "quantidades": [1, 2],
      "localizacao": "SP",
      "faturamento": "CPF",
      "desconto": 100.00,
      "entrada": 500.00,
      "parcelas": 12,
      "valorParcela": 250.00,
      "observacao": "Alguma observação em HTML seguro",
      "descricao": "Descrição da simulação",
      "tipoPagamento": "Cartão",
      "nomeVendedor": "João Silva",
      "nomeCNPJ": "Empresa ABC Ltda",
      "nomeCliente": "Cliente Teste"
    }
    ```
  - **Resposta**: Um `HttpResponse` com o conteúdo do PDF (`application/pdf`) ou, em caso de erro na geração do PDF, um `HttpResponse` com o HTML (`text/html`) para depuração. Em caso de erro na API, retorna um `Response` com status 500 e mensagem de erro.

## Lógica de Geração de PDF (`views.py`)

A função `generate_pdf` é o coração da funcionalidade de simulação. Ela realiza os seguintes passos:

1.  **Extração de Dados**: Recebe os dados da simulação via `request.data` (corpo JSON da requisição POST).
2.  **Processamento de Equipamentos**: Itera sobre os IDs e quantidades de equipamentos fornecidos. Para cada equipamento, busca seus detalhes no banco de dados e calcula o valor unitário e total com base na `localizacao` (SP vs. outros estados) e `faturamento` (CPF vs. CNPJ).
3.  **Cálculo de Totais**: Soma os valores dos equipamentos, aplica descontos, entrada e calcula o valor final.
4.  **Geração de Datas**: Determina a data de geração e a data de validade do relatório (primeiro dia do próximo mês).
5.  **Renderização HTML**: Utiliza `django.template.loader.render_to_string` para preencher um template HTML (`api/pdf_simulador.html`) com todos os dados processados.
6.  **Conversão para PDF**: Emprega a biblioteca `WeasyPrint` para converter o HTML renderizado em um arquivo PDF. Há uma lógica de fallback para retornar o HTML diretamente se a geração do PDF falhar (útil para depuração).
7.  **Resposta**: Retorna o PDF gerado como um anexo (`FileResponse`) ou o HTML para depuração.

### Funções Auxiliares:

-   `format_currency(value)`: Formata um valor numérico para o padrão de moeda brasileira.
-   `_html_to_pdf_weasyprint(html_string)`: Encapsula a lógica de conversão de HTML para PDF usando WeasyPrint, incluindo a configuração do GTK3-Runtime para Windows.
-   `_calculate_item_value(...)`: Calcula o valor unitário e total de um item de equipamento.
-   `_process_equipamentos_data(...)`: Orquestra o processamento dos dados de múltiplos equipamentos.
-   `_calculate_totals(...)`: Calcula os totais financeiros da simulação.
-   `_get_report_dates()`: Gera as datas de geração e validade do relatório.

## Configuração do WeasyPrint

A aplicação tenta configurar o `WeasyPrint` para funcionar corretamente, especialmente em ambientes Windows, procurando pelo `GTK3-Runtime`. Em Linux, a biblioteca geralmente funciona sem configurações adicionais. É crucial que o `WeasyPrint` e suas dependências (como o GTK3) estejam corretamente instalados no ambiente de execução para que a geração de PDF funcione.

## Uso com o Frontend Expo

O aplicativo Expo deve fazer requisições `POST` para o endpoint `/api/generate-pdf/` com o corpo JSON contendo os dados da simulação. A resposta será um arquivo PDF que pode ser exibido ou baixado pelo usuário no aplicativo móvel.

