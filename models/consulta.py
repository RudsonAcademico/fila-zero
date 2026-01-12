from datetime import datetime, timezone
from bson import ObjectId


class Consulta:
    def __init__(
        self,
        nome_paciente: str,
        cpf_paciente: str,
        telefone: str,
        tipo_consulta: str,
        data_hora: datetime,
        status: str = "marcado",
        _id: ObjectId = None,
        criado_em: datetime = None
    ):
        self.id = _id
        self.nome_paciente = nome_paciente
        self.cpf_paciente = cpf_paciente
        self.telefone = telefone
        self.tipo_consulta = tipo_consulta
        self.data_hora = data_hora
        self.status = status
        self.criado_em = criado_em or datetime.now(timezone.utc)

    # ===============================
    # Factory (criação controlada)
    # ===============================
    @classmethod
    def criar(cls, nome_paciente, cpf_paciente, telefone, tipo_consulta, data_hora):
        """
        Cria uma nova consulta com status inicial 'marcado'
        """
        return cls(
            nome_paciente=nome_paciente,
            cpf_paciente=cpf_paciente,
            telefone=telefone,
            tipo_consulta=tipo_consulta,
            data_hora=data_hora,
            status="marcado"
        )

    # ===============================
    # Regras de domínio
    # ===============================
    def cancelar(self):
        self.status = "cancelado"

    def adiar(self, nova_data_hora: datetime):
        self.data_hora = nova_data_hora
        self.status = "adiado"

    def finalizar(self):
        self.status = "finalizado"

    # ===============================
    # MongoDB
    # ===============================
    def to_dict(self):
        data = {
            "nome_paciente": self.nome_paciente,
            "cpf_paciente": self.cpf_paciente,
            "telefone": self.telefone,
            "tipo_consulta": self.tipo_consulta,
            "data_hora": self.data_hora,
            "status": self.status,
            "criado_em": self.criado_em
        }

        if self.id:
            data["_id"] = self.id

        return data

    @classmethod
    def from_dict(cls, data):
        data_hora = data.get("data_hora")

        if data_hora and data_hora.tzinfo is None:
            data_hora = data_hora.replace(tzinfo=timezone.utc)

        return cls(
            _id=data.get("_id"),
            nome_paciente=data.get("nome_paciente"),
            cpf_paciente=data.get("cpf_paciente"),
            telefone=data.get("telefone"),
            tipo_consulta=data.get("tipo_consulta"),
            data_hora=data_hora,
            status=data.get("status", "marcado"),
            criado_em=data.get("criado_em"),
        )


    # ===============================
    # Retorno seguro (API / Front)
    # ===============================
    def serialize(self):
        return {
            "id": str(self.id) if self.id else None,
            "nome_paciente": self.nome_paciente,
            "cpf_paciente": self.cpf_paciente,
            "telefone": self.telefone,
            "tipo_consulta": self.tipo_consulta,
            "data_hora": self.data_hora.isoformat(),
            "status": self.status,
            "criado_em": self.criado_em.isoformat()
        }