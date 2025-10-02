# FormSuporte

Este projeto é uma aplicação web desenvolvida em Django para gerenciar formulários de suporte, situação de veículos, ocorrências de erro, e funcionalidades de simulação. Ele integra diversas aplicações para fornecer uma solução completa de gerenciamento.

## Estrutura do Projeto

O projeto `FormSuporte` é organizado da seguinte forma:

- `FormSuporte/`: Diretório principal do projeto Django.
  - `settings.py`: Configurações globais do projeto, incluindo banco de dados, aplicações instaladas e configurações de segurança.
  - `urls.py`: Mapeamento de URLs globais que direcionam para as URLs de cada aplicação.
  - `asgi.py`, `wsgi.py`: Configurações para servidores ASGI e WSGI.
- `API/`: Aplicação Django para fornecer endpoints RESTful.
- `form/`: Aplicação Django para gerenciar formulários de suporte de veículos.
  - `views.py`: Contém a lógica para cadastrar veículos, listar veículos com filtros e paginação, e atualizar dados de veículos via AJAX.
  - `models.py`: Define os modelos de dados para veículos.
  - `forms.py`: Define os formulários baseados nos modelos.
  - `urls.py`: Mapeamento de URLs específicas para a aplicação `form`.
- `ocorrencia_erro/`: Aplicação Django para registrar e gerenciar ocorrências de erro.
- `simulador/`: Aplicação Django para funcionalidades de simulação.
- `situacao_veiculo/`: Aplicação Django para gerenciar a situação atual dos veículos.
- `static/`: Contém arquivos estáticos (CSS, JavaScript, imagens) para todas as aplicações.
- `templates/`: Contém templates HTML globais ou compartilhados.

## Configuração do Ambiente

Para configurar e executar este projeto localmente, siga os passos abaixo:

### Pré-requisitos

Certifique-se de ter os seguintes softwares instalados:

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Git
- MySQL Server (ou outro banco de dados configurado em `settings.py`)
- Redis Server (para Django Channels)

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/EAATA-Brasil/FormSuporte.git
   cd FormSuporte
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Linux/macOS
   # venv\Scripts\activate   # No Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuração do Banco de Dados:**
   O projeto está configurado para usar MySQL. Certifique-se de que seu servidor MySQL esteja em execução e que você tenha um banco de dados chamado `servidorEaata` com um usuário `root` e senha `eaata360` (conforme `settings.py`).
   
   **Alternativamente, para desenvolvimento local com SQLite:**
   Descomente a seção SQLite em `FormSuporte/settings.py` e comente a seção MySQL.
   ```python
   # DATABASES = {
   #     'default': {
   #         'ENGINE': 'django.db.backends.sqlite3',
   #         'NAME': BASE_DIR / 'db.sqlite3',
   #     }
   # }
   ```

5. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crie um superusuário (opcional, para acessar o admin do Django):**
   ```bash
   python manage.py createsuperuser
   ```
   Siga as instruções para criar seu usuário e senha.

7. **Coletar arquivos estáticos:**
   ```bash
   python manage.py collectstatic
   ```

## Executando o Projeto

Para iniciar o servidor de desenvolvimento Django:

```bash
python manage.py runserver
```

O aplicativo estará disponível em `http://127.0.0.1:8000/`.

Para o Django Channels (WebSockets), você precisará de um servidor Redis em execução e iniciar o servidor Daphne:

1. **Inicie o servidor Redis:**
   (Instruções variam conforme o sistema operacional. Ex: `redis-server` no Linux)

2. **Inicie o servidor Daphne:**
   ```bash
   daphne -b 0.0.0.0 -p 8000 Form_Suporte.asgi:application
   ```
   Ou, se estiver usando `runserver` para desenvolvimento, ele pode iniciar o Daphne automaticamente se configurado.

## Boas Práticas e Clean Code Aplicados

Durante a refatoração, foram aplicadas as seguintes boas práticas:

- **Comentários e Docstrings:** Adição de comentários explicativos e docstrings (seguindo o padrão reStructuredText ou Google Style) para funções, classes e seções importantes do código, melhorando a legibilidade e a compreensão.
- **Organização de `settings.py`:** Agrupamento lógico de configurações e adição de comentários para cada seção, facilitando a manutenção e a identificação de configurações específicas.
- **Refatoração de `urls.py`:** Remoção de URLs duplicadas e adição de comentários para descrever a finalidade de cada inclusão de URLconf.
- **Clareza nas Views (`form/views.py`):**
  - **`cadastrar_veiculo`:** Adição de docstrings detalhadas explicando o propósito, argumentos e retorno da função, além de comentários inline para passos importantes.
  - **`index`:** Docstrings e comentários para explicar a lógica de filtragem, ordenação e paginação.
  - **`get_opcoes_filtro`:** Docstrings e comentários para descrever a obtenção de opções de filtro dinâmicas.
  - **`update_vehicle_data` (anteriormente `update_vehicle` e `update_vehicle_field`):** Consolidação de lógica duplicada em uma única função mais robusta, com docstrings e tratamento de erros mais claros. Utilização de `update_fields` para otimização de saves no banco de dados.
- **Tratamento de Exceções:** Melhoria no tratamento de exceções em funções de API para fornecer respostas mais informativas em caso de erro.
- **Nomenclatura:** Garantia de nomes de variáveis e funções descritivos e consistentes.

## Contribuição

Para contribuir com este projeto, por favor, siga os passos:

1. Faça um fork do repositório.
2. Crie uma nova branch para sua feature (`git checkout -b feature/minha-feature`).
3. Faça suas alterações e adicione testes, se aplicável.
4. Certifique-se de que o código segue as diretrizes de estilo e boas práticas.
5. Faça commit de suas alterações (`git commit -m 'feat: Adiciona minha nova feature'`).
6. Envie suas alterações para o seu fork (`git push origin feature/minha-feature`).
7. Abra um Pull Request para o repositório original.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes. (Assumindo que há um arquivo LICENSE ou que será criado.)

---

**Desenvolvido por Manus AI**
Data: 02 de Outubro de 2025

