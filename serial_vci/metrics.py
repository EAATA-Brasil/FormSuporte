from prometheus_client import Counter, Gauge

# ---- GAUGE: estado atual ----
TOTAL_SERIAIS = Gauge(
    "serial_vci_total_existentes",
    "Quantidade total de seriais cadastrados no banco"
)

TOTAL_GARANTIAS = Gauge(
    "serial_vci_total_garantias",
    "Quantidade total de garantias existentes"
)

TOTAL_COMENTARIOS = Gauge(
    "serial_vci_total_comentarios",
    "Quantidade total de comentários registrados"
)

# ---- COUNTERS: eventos ----

SERIAL_CADASTRADO = Counter(
    "serial_vci_cadastrado_total",
    "Quantidade total de seriais cadastrados"
)

SERIAL_EDITADO = Counter(
    "serial_vci_editado_total",
    "Quantidade total de edições de seriais"
)

FOTO_ADICIONADA = Counter(
    "serial_vci_foto_adicionada_total",
    "Fotos adicionadas ao serial"
)

FOTO_REMOVIDA = Counter(
    "serial_vci_foto_removida_total",
    "Fotos removidas do serial"
)

GARANTIA_CRIADA = Counter(
    "serial_vci_garantia_criada_total",
    "Garantias cadastradas"
)

GARANTIA_DELETADA = Counter(
    "serial_vci_garantia_deletada_total",
    "Garantias removidas"
)

COMENTARIO_CRIADO = Counter(
    "serial_vci_comentario_criado_total",
    "Comentários adicionados"
)

COMENTARIO_DELETADO = Counter(
    "serial_vci_comentario_deletado_total",
    "Comentários removidos"
)
