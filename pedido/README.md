Pedido – App

Visão geral
- App Django responsável por fluxos de pedido/orçamento específicos do projeto.
- Inclui views, forms e templates para criação/visualização de pedidos.

Rotas (urls.py)
- Verifique as rotas definidas em pedido/urls.py para a versão atual do projeto.

Principais componentes
- models.py: Modelos de pedido e relacionamentos auxiliares (se aplicável).
- forms.py: Formulários de criação/edição.
- views.py: Lógica de listagem e CRUD.
- templates/pedido/: Páginas de interface do app.

Integrações
- Pode consumir dados de outras apps (ex.: API de equipamentos) conforme necessidade.

Tarefas comuns
- Migrações: python manage.py makemigrations pedido && python manage.py migrate
- Testes: python manage.py test pedido

Observações
- Esta app é modular e pode variar conforme o ambiente; mantenha o README alinhado às rotas e modelos correntes.