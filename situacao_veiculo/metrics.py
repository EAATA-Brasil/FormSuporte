from prometheus_client import Counter, Gauge

CLIENTES_EXISTENTES = Gauge(
    "situacao_clientes_existentes_total",
    "Quantidade total de clientes cadastrados no sistema"
)

BUSCA_SUCESSO = Counter(
    "situacao_busca_sucesso_total",
    "Buscas de serial com sucesso"
)

BUSCA_FALHA = Counter(
    "situacao_busca_falha_total",
    "Buscas de serial sem resultados"
)

BUSCA_MULTIPLOS = Counter(
    "situacao_busca_multiplos_total",
    "Buscas que retornaram múltiplos clientes"
)

CADASTRO_SUCESSO = Counter(
    "situacao_cadastro_sucesso_total",
    "Clientes cadastrados com sucesso"
)

CADASTRO_ERRO = Counter(
    "situacao_cadastro_erro_total",
    "Falhas ao cadastrar clientes"
)

CLIENTES_ATUALIZADOS = Counter(
    "situacao_clientes_atualizados_total",
    "Total de atualizações de clientes",
    ["campo"]
)

IMPORTADOS_SUCESSO = Counter(
    "situacao_importados_sucesso_total",
    "Clientes importados com sucesso via Excel"
)

IMPORTADOS_DUPLICADOS = Counter(
    "situacao_importados_duplicados_total",
    "Registros duplicados ignorados na importação"
)

IMPORTADOS_ERRO = Counter(
    "situacao_importados_erro_total",
    "Erros durante importação via Excel"
)
