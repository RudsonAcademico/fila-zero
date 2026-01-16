from datetime import datetime, timezone
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    def __init__(
        self,
        nome: str,
        email: str,
        senha_hash: str,
        papel: str = "funcionario",
        ativo: bool = True,
        _id: ObjectId = None,
        criado_em: datetime = None
    ):
        self.id = _id
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash
        self.papel = papel
        self.ativo = ativo
        self.criado_em = criado_em or datetime.now(timezone.utc)

    # ===============================
    # Factories
    # ===============================
    @classmethod
    def criar(cls, nome, email, senha, papel="funcionario"):
        return cls(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha),
            papel=papel
        )

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            _id=data.get("_id"),
            nome=data.get("nome"),
            email=data.get("email"),
            senha_hash=data.get("senha_hash"),
            papel=data.get("papel", "funcionario"),
            ativo=data.get("ativo", True),
            criado_em=data.get("criado_em")
        )
    
    def to_dict(self):
        data = {
            "nome": self.nome,
            "email": self.email,
            "senha_hash": self.senha_hash,
            "papel": self.papel,
            "ativo": self.ativo,
            "criado_em": self.criado_em
        }
        if self.id:
            data["_id"] = self.id
        return data

    # ===============================
    # Autenticação
    # ===============================
    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)
