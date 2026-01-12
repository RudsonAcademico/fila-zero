from datetime import datetime, timezone
from models.consulta import Consulta


class ConsultaRepository:
    def __init__(self, collection):
        self.collection = collection

    def salvar(self, consulta: Consulta):
        resultado = self.collection.insert_one(consulta.to_dict())
        consulta.id = resultado.inserted_id
        return consulta

    def atualizar_atrasadas(self):
        agora = datetime.now(timezone.utc)

        resultado = self.collection.update_many(
            {
                "status": {"$in": ["marcado", "aguardando"]},
                "data_hora": {"$lt": agora}
            },
            {
                "$set": {"status": "atrasado"}
            }
        )

        return resultado.modified_count
