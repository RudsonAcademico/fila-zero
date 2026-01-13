from datetime import datetime, timezone

class ConsultaRepository:
    def __init__(self, collection):
        self.collection = collection

    def salvar(self, consulta):
        """Salva uma nova consulta no banco"""
        resultado = self.collection.insert_one(consulta.to_dict())
        consulta.id = resultado.inserted_id
        return consulta

    def atualizar(self, consulta):
        """Atualiza os dados de uma consulta existente"""
        if not consulta.id:
            raise ValueError("Consulta precisa ter um ID para ser atualizada")

        resultado = self.collection.update_one(
            {"_id": consulta.id},
            {"$set": consulta.to_dict()}
        )
        return resultado.modified_count

    def atualizar_atrasadas(self):
        """Marca como atrasadas todas as consultas passadas que ainda não foram finalizadas"""
        agora = datetime.now(timezone.utc)

        resultado = self.collection.update_many(
            {
                "status": {"$in": ["marcado", "adiado"]},
                "data_hora": {"$lt": agora}
            },
            {
                "$set": {"status": "atrasado"}
            }
        )

        return resultado.modified_count
