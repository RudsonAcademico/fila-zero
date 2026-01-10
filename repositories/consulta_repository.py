class ConsultaRepository:
    def __init__(self, collection):
        self.collection = collection

    def salvar(self, consulta: Consulta):
        resultado = self.collection.insert_one(consulta.to_dict())
        consulta.id = resultado.inserted_id
        return consulta
