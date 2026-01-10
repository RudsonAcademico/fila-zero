from datetime import datetime, timezone
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    def __init__( self, name: str, email: str, password: str = None, role: str = "employee", active: bool = True, _id: ObjectId = None, created_at: datetime = None, password_hash: str = None):
        self.id = _id
        self.name = name
        self.email = email
        self.role = role
        self.active = active
        self.created_at = created_at or datetime.now(timezone.utc)

        if password:
            self.password_hash = generate_password_hash(password)
        else:
            self.password_hash = password_hash

    # Converter para dicionário (MongoDB)
    def to_dict(self):
        data = {
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "active": self.active,
            "created_at": self.created_at
        }
        if self.id:
            data["_id"] = self.id
        return data

    # Criar User a partir do MongoDB
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            _id=data.get("_id"),
            name=data.get("name"),
            email=data.get("email"),
            password=None,  # senha não é usada
            password_hash=data.get("password_hash"),  # carrega hash do banco
            role=data.get("role", "employee"),
            active=data.get("active", True),
            created_at=data.get("created_at")
        )

    # Verificar senha
    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False  # evita erro se hash estiver vazio
        return check_password_hash(self.password_hash, password)

    # Retorno seguro (sem senha)
    def serialize(self):
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": self.created_at.isoformat()
        }
