from datetime import datetime, timezone

class ConsultaRepository:
    def __init__(self, collection):
        self.collection = collection

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
