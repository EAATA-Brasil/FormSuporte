import os
import requests
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from django.utils import timezone

from situacao_veiculo.models import Cliente
from django.conf import settings

# Simple JSON-RPC helper for Odoo
class OdooClient:
    def __init__(self, url: str, db: str, user: str, password: str, timeout: int = 20):
        # Permite receber tanto a URL base (ex: https://host) quanto o endpoint completo (/jsonrpc)
        self.url = url.rstrip('/')
        self.db = db
        self.user = user
        self.password = password
        self.timeout = timeout
        self.uid: Optional[int] = None

    @property
    def endpoint(self) -> str:
        # Se já vier apontando para /jsonrpc, usa direto; senão, acrescenta
        if self.url.endswith('/jsonrpc'):
            return self.url
        return f"{self.url}/jsonrpc"

    def _rpc(self, service: str, method: str, args: list, kwargs: Optional[dict] = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args if args is not None else [],
            },
            "id": 1,
        }
        if kwargs:
            payload["params"]["kwargs"] = kwargs
        resp = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(data["error"])  # surface Odoo error
        return data.get("result")

    def login(self) -> int:
        uid = self._rpc("common", "login", [self.db, self.user, self.password])
        if not uid:
            raise RuntimeError("Odoo login failed")
        self.uid = uid
        return uid

    def execute_kw(self, model: str, method: str, args: list, kwargs: Optional[dict] = None) -> Any:
        if self.uid is None:
            self.login()
        return self._rpc("object", "execute_kw", [self.db, self.uid, self.password, model, method, args, kwargs or {}])


def _norm_serial(s: str) -> str:
    return (s or '').strip()


def fetch_done_outgoing_moves_with_serial(client: OdooClient, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Busca linhas de movimento (stock.move.line) concluídas de saída (outgoing)
    que possuam lote/número de série.
    """
    domain = [
        ("state", "=", "done"),
        ("picking_id.picking_type_id.code", "=", "outgoing"),
        "|",
        ("lot_id", "!=", False),
        ("lot_name", "!=", False),
    ]
    fields = [
        "date",
        "qty_done",
        "product_id",
        "lot_id",
        "lot_name",
        "picking_id",
        "reference",
    ]
    # search_read em blocos
    result: List[Dict[str, Any]] = []
    offset = 0
    step = int(os.getenv("ODOO_READ_STEP", "500"))  # lote de leitura
    while True:
        # calcula limite do lote quando limite total é definido
        per_call_limit = step if (limit is None) else min(step, max(1, limit - offset))
        if limit is not None and per_call_limit <= 0:
            break

        batch = client.execute_kw(
            "stock.move.line",
            "search_read",
            [domain],
            {"fields": fields, "limit": per_call_limit, "offset": offset, "order": "date desc"},
        )
        if not batch:
            break
        result.extend(batch)
        offset += len(batch)
        if limit is not None and offset >= limit:
            break
    # Map picking -> partner
    picking_ids = list({rec["picking_id"][0] for rec in result if isinstance(rec.get("picking_id"), list)})
    picking_partner: Dict[int, str] = {}
    if picking_ids:
        pickings = client.execute_kw("stock.picking", "read", [picking_ids], {"fields": ["name", "partner_id", "date_done"]})
        for p in pickings:
            partner = p.get("partner_id")
            picking_partner[p["id"]] = partner[1] if isinstance(partner, list) and len(partner) > 1 else None
    # Enriquecer
    for r in result:
        pid = r.get("picking_id")
        if isinstance(pid, list):
            r["partner_name"] = picking_partner.get(pid[0])
        else:
            r["partner_name"] = None
    return result


def sync_odoo_to_clientes(max_rows: Optional[int] = None) -> Dict[str, int]:
    """Sincroniza movimentos de saída com série em Clientes.
    Regras:
      - Serial = lot_name (ou lot_id[1])
      - Nome = partner_name (se houver)
      - Equipamento = product_id[1]
      - Data = date (ou hoje se ausente)
      - anos_para_vencimento: 1 se equipamento contém 'reader', senão 2 (mesma regra do app)
      - Se já existir Cliente com o serial, não duplica; atualiza nome/equipamento quando vazios.
    """
    # Ordem de prioridade: Django settings -> env vars -> defaults dev
    url = getattr(settings, "ODOO_URL", None) or os.getenv("ODOO_URL", "http://localhost:8069")
    db = getattr(settings, "ODOO_DB", None) or os.getenv("ODOO_DB", "odoo")
    user = getattr(settings, "ODOO_USER", None) or os.getenv("ODOO_USER", "admin")
    # aceita ODOO_PASSWORD e fallback ODOO_PASS
    password = (
        getattr(settings, "ODOO_PASSWORD", None)
        or os.getenv("ODOO_PASSWORD")
        or os.getenv("ODOO_PASS")
        or "admin"
    )

    client = OdooClient(url, db, user, password)
    rows = fetch_done_outgoing_moves_with_serial(client, limit=max_rows)

    created = 0
    updated = 0
    skipped = 0

    def anos_por_equip(equip: str) -> int:
        return 1 if (equip or '').lower().find('reader') != -1 else 2

    for rec in rows:
        serial = _norm_serial(rec.get("lot_name") or (rec.get("lot_id")[1] if isinstance(rec.get("lot_id"), list) else None))
        if not serial:
            skipped += 1
            continue
        produto = rec.get("product_id")
        equipamento = produto[1] if isinstance(produto, list) and len(produto) > 1 else ""
        partner_name = rec.get("partner_name") or ""
        dt = rec.get("date")
        try:
            data_date = datetime.fromisoformat(dt.replace('Z','+00:00')).date() if isinstance(dt, str) else timezone.localdate()
        except Exception:
            data_date = timezone.localdate()

        obj = Cliente.objects.filter(serial__iexact=serial).first()
        if obj:
            changed = False
            if not obj.nome and partner_name:
                obj.nome = partner_name
                changed = True
            if (not obj.equipamento) and equipamento:
                obj.equipamento = equipamento
                changed = True
            if changed:
                obj.save(update_fields=["nome", "equipamento"])  # saves only changed fields; harmless if not both
                updated += 1
            else:
                skipped += 1
            continue

        # Criar novo
        try:
            Cliente.objects.create(
                data=data_date,
                anos_para_vencimento=anos_por_equip(equipamento),
                serial=serial,
                nome=partner_name,
                cnpj=None,
                tel=None,
                equipamento=equipamento or "N/D",
            )
            created += 1
        except Exception:
            skipped += 1

    return {"created": created, "updated": updated, "skipped": skipped, "fetched": len(rows)}
