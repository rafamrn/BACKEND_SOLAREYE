import unicodedata
from collections import defaultdict
from typing import List
from passlib.context import CryptContext
from modelos import Integracao
from sqlalchemy.orm import Session
import hashlib
from clients.isolarcloud_client import ApiSolarCloud
from clients.deye_client import ApiDeye
from datetime import datetime
from pytz import timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_apis_ativas(db: Session, cliente_id: int):
    apis = []
    integracoes = db.query(Integracao).filter_by(cliente_id=cliente_id).all()

    for integracao in integracoes:
        if integracao.plataforma.lower() == "sungrow":
            apis.append(ApiSolarCloud(db=db, integracao=integracao))
        elif integracao.plataforma.lower() == "deye":
            apis.append(ApiDeye(db=db, integracao=integracao))
        # Adicione aqui novas plataformas se necessário

    return apis

def get_horario_brasilia():
    fuso_brasilia = timezone("America/Sao_Paulo")
    return datetime.now(fuso_brasilia)

def hash_sha256(password: str) -> str:
    """
    Retorna o hash SHA256 da senha em minúsculas.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def normalizar_nome(nome: str) -> str:
    """Remove acentos e transforma em minúsculas para comparação robusta."""
    return unicodedata.normalize("NFKD", nome).encode("ASCII", "ignore").decode().lower().strip()

import unicodedata
from collections import defaultdict
from typing import List

def normalizar_nome(nome: str) -> str:
    """Remove acentos e transforma em minúsculas para comparação robusta."""
    return unicodedata.normalize("NFKD", nome).encode("ASCII", "ignore").decode().lower().strip()

def agrupar_usinas_por_nome(usinas: List[dict]) -> List[dict]:
    def normalizar_nome(nome):
        return nome.lower().replace(" ", "").replace("-", "").replace("_", "")

    agrupadas = {}
    for usina in usinas:
        chave = normalizar_nome(usina["ps_name"])
        if chave in agrupadas:
            agrupadas[chave].append(usina)
        else:
            agrupadas[chave] = [usina]

    resultado = []
    for grupo in agrupadas.values():
        if len(grupo) == 1:
            u = grupo[0]
            resultado.append({
                "ps_id": u["ps_id"],
                "ps_name": u["ps_name"],
                "location": u["location"],
                "capacidade": float(u["capacidade"]),
                "curr_power": float(u["curr_power"]),
                "total_energy": float(u["total_energy"]),
                "today_energy": float(u["today_energy"]),
                "co2_total": float(u["co2_total"]),
                "income_total": float(u["income_total"]),
                "ps_fault_status": int(u["ps_fault_status"]) if u["ps_fault_status"] is not None else 0,
            })
        else:
            primeira = grupo[0]
            usina_unificada = {
                "ps_id": primeira["ps_id"],
                "ps_name": primeira["ps_name"],
                "location": primeira["location"],
                "capacidade": sum(float(u["capacidade"]) for u in grupo),
                "curr_power": sum(float(u["curr_power"]) for u in grupo),
                "total_energy": sum(float(u["total_energy"]) for u in grupo),
                "today_energy": sum(float(u["today_energy"]) for u in grupo),
                "co2_total": sum(float(u["co2_total"]) for u in grupo),
                "income_total": sum(float(u["income_total"]) for u in grupo),
                "ps_fault_status": max(int(u["ps_fault_status"]) for u in grupo),
            }
            resultado.append(usina_unificada)
    return resultado
    
def parse_float(value):
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0
    
def get_integracao_por_plataforma(db: Session, cliente_id: int, plataforma: str):
    return (
        db.query(Integracao)
        .filter(Integracao.cliente_id == cliente_id)
        .filter(Integracao.plataforma == plataforma)
        .first()
    )
