class UserRepository:
    def __init__(self, collection):
        self.collection = collection

    def salvar(self, user):
        """Salva um novo user no banco"""
        resultado = self.collection.insert_one(user.to_dict())
        user.id = resultado.inserted_id
        return user