def atualizar_consultas_atrasadas(repo):
    modificadas = repo.atualizar_atrasadas()
    print(f"⏰ Job executado → {modificadas} consultas atrasadas")