from datetime import datetime
from bson import ObjectId


class Consulta:
    def __init__( self, client_name: str, phone: str, consultation_type: str, scheduled_at: datetime, _id: ObjectId = None, created_at: datetime = None, status: str = "marcado" ):
        self.id = _id
        self.client_name = client_name
        self.phone = phone
        self.consultation_type = consultation_type
        self.scheduled_at = scheduled_at
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)


    # Criar consulta nova (regra centralizada)
    @classmethod
    def create(cls, client_name, phone, consultation_type, scheduled_at):
        """
        Cria uma nova Consulta com status inicial 'marcado'
        """
        return cls(
            client_name=client_name,
            phone=phone,
            consultation_type=consultation_type,
            scheduled_at=scheduled_at,
            status="marcado"
        )

    def to_dict(self):
        return {
            "client_name": self.client_name,
            "phone": self.phone,
            "consultation_type": self.consultation_type,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "created_at": self.created_at
        }

    # Ações de domínio (mudança de status)
    def cancelar(self):
        self.status = "cancelado"

    def adiar(self, nova_data: datetime):
        self.scheduled_at = nova_data
        self.status = "adiado"

    # MongoDB
    def to_dict(self):
        data = {
            "client_name": self.client_name,
            "phone": self.phone,
            "consultation_type": self.consultation_type,
            "scheduled_at": self.scheduled_at,
            "status": self.status,
            "created_at": self.created_at
        }
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            _id=data.get("_id"),
            client_name=data.get("client_name"),
            phone=data.get("phone"),
            consultation_type=data.get("consultation_type"),
            scheduled_at=data.get("scheduled_at"),
            status=data.get("status", "marcado"),
            created_at=data.get("created_at")
        )

    # Retorno para API
    def serialize(self):
        return {
            "id": str(self.id) if self.id else None,
            "client_name": self.client_name,
            "phone": self.phone,
            "consultation_type": self.consultation_type,
            "scheduled_at": self.scheduled_at.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }
