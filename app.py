from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timezone, timedelta
from flask_apscheduler import APScheduler
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

from repositories.consulta_repository import ConsultaRepository
from jobs.atualizar_atrasadas import atualizar_consultas_atrasadas
from models.consulta import Consulta
from models.user import User

import os


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("PSW_SECRET")
app.config["SCHEDULER_API_ENABLED"] = True

# Conexão com MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["fila_zero"]
users_collection = db["users"]
consultas_collection = db["consultas"]
consulta_repository = ConsultaRepository(consultas_collection)

# Scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Job a cada 10 minutos
scheduler.add_job(
    id="atualizar_atrasadas",
    func=atualizar_consultas_atrasadas,
    args=[consulta_repository],
    trigger="interval",
    minutes=10
)

scheduler.start()


# Converter ObjectId para string
def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }

# Rotas para Paginas
@app.route("/", endpoint='login' , methods=["GET"])
def login():
    session["user_id"] = None
    session.clear()
    return render_template("login.html")


@app.route("/principal")
def principal():
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    # ===== BUSCAR CONSULTAS =====
    
    consultas_cursor = consultas_collection.find()
    consulta_repository.atualizar_atrasadas()
    consultas = [Consulta.from_dict(c) for c in consultas_cursor]

    # ===== STATUS AUTOMÁTICO (ATRASADO) =====
    agora = datetime.now(timezone.utc)

    for c in consultas:
        if c.status != "finalizado" and c.data_hora < agora:
            c.status = "atrasado"

    # ===== ESTATÍSTICAS =====
    inicio_semana = agora.date() - timedelta(days=agora.weekday())

    stats = {
        # Agendados futuros
        "scheduled": sum(
            1 for c in consultas
            if c.status == "marcado" and c.data_hora >= agora
        ),

        # Atrasados
        "waiting": sum(
            1 for c in consultas
            if c.status == "atrasado"
        ),

        # Finalizados essa semana
        "completed": sum(
            1 for c in consultas
            if c.status == "finalizado"
            and c.data_hora.date() >= inicio_semana
        ),
    }

    # ===== CRONOGRAMA DA SEMANA =====
    today = agora.date()

    DAYS_PT = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }

    week_days = []

    for i in range(10):
        day_date = today + timedelta(days=i)

        day_consultas = [
            c for c in consultas
            if c.data_hora.date() == day_date
        ]

        week_days.append({
            "date": day_date,
            "day_name": DAYS_PT[day_date.weekday()],
            "is_today": day_date == today,
            "consultas": sorted(day_consultas, key=lambda x: x.data_hora)
        })

    return render_template(
        "principal.html",
        user_nome=session.get("user_nome"),
        consultas=consultas,
        stats=stats,
        week_days=week_days
    )



@app.route("/consultas", methods=["GET"])
def consultas():
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    # ===== BUSCA =====
    termo = request.args.get("q")  # Pega o valor do campo de busca
    filtro = {}

    if termo:
        filtro = {
            "$or": [
                {"nome_paciente": {"$regex": termo, "$options": "i"}},
                {"cpf_paciente": {"$regex": termo, "$options": "i"}},
                {"telefone": {"$regex": termo, "$options": "i"}},
                {"tipo_consulta": {"$regex": termo, "$options": "i"}},
            ]
        }

    # ===== BUSCAR CONSULTAS =====
    consultas_cursor = consultas_collection.find(filtro).sort("data_hora", 1)
    
    # Atualizar atrasadas no banco (se houver)
    consulta_repository.atualizar_atrasadas()
    
    # Transformar em objetos Consulta
    consultas = [Consulta.from_dict(c) for c in consultas_cursor]

    # ===== ESTATÍSTICAS =====
    agora = datetime.now(timezone.utc)
    inicio_semana = agora.date() - timedelta(days=agora.weekday())

    stats = {
        # Agendados futuros
        "scheduled": sum(
            1 for c in consultas
            if c.status == "marcado" and c.data_hora >= agora
        ),

        # Atrasados
        "waiting": sum(
            1 for c in consultas
            if c.status == "atrasado"
        ),

        # Finalizados essa semana
        "completed": sum(
            1 for c in consultas
            if c.status == "finalizado" and c.data_hora.date() >= inicio_semana
        ),
    }

    return render_template(
        "consultas.html",
        user_nome=session.get("user_nome"),
        consultas=consultas,
        stats=stats,
        termo=termo  # Para preencher o input de busca com o valor digitado
    )




# ======== Rota de login (POST) ========
@app.route("/login_action", methods=["POST"])
def login_action():
    email = request.form.get("email")
    senha = request.form.get("password")

    if not email or not senha:
        flash("Preencha todos os campos")
        return redirect(url_for("login"))

    # Buscar usuário no MongoDB
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        flash("Usuário não encontrado")
        return redirect(url_for("login"))

    user = User.from_dict(user_data)

    # Verificar senha
    if not user.verificar_senha(senha):
        flash("Senha incorreta")
        return redirect(url_for("login"))

    # Login bem-sucedido → salvar na sessão
    session.clear()
    session["user_id"] = str(user.id)
    session["user_nome"] = user.nome
    session["user_papel"] = user.papel

    flash(f"Bem-vindo, {user.nome}!")
    return redirect(url_for("principal"))


# ======== Logout ========
@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!")
    return redirect(url_for("login"))


# ===========================
# Rota para ver detalhes
# ===========================
@app.route("/consulta/<consulta_id>", methods=["GET"])
def consulta_detalhes(consulta_id):
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    # Buscar consulta pelo ID
    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)

    return render_template(
        "consulta_detalhes.html",
        user_nome=session.get("user_nome"),
        consulta=consulta
    )


# ===========================
# Rota para finalizar
# ===========================
@app.route("/consulta/<consulta_id>/finalizar", methods=["POST"])
def finalizar_consulta(consulta_id):
    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)
    consulta.finalizar()
    consulta_repository.atualizar(consulta)  # Atualiza no MongoDB

    flash("Consulta finalizada com sucesso!")
    return redirect(url_for("consulta_detalhes", consulta_id=consulta_id))


# ===========================
# Rota para adiar
# ===========================
@app.route("/consulta/<consulta_id>/adiar", methods=["POST"])
def adiar_consulta(consulta_id):
    nova_data_hora_str = request.form.get("nova_data_hora")
    if not nova_data_hora_str:
        flash("Informe a nova data e hora")
        return redirect(url_for("consulta_detalhes", consulta_id=consulta_id))

    nova_data_hora = datetime.fromisoformat(nova_data_hora_str)

    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)
    consulta.adiar(nova_data_hora)
    consulta_repository.atualizar(consulta)

    flash("Consulta adiada com sucesso!")
    return redirect(url_for("consulta_detalhes", consulta_id=consulta_id))


# ===========================
# Rota para cancelar
# ===========================
@app.route("/consulta/<consulta_id>/cancelar", methods=["POST"])
def cancelar_consulta(consulta_id):
    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)
    consulta.cancelar()
    consulta_repository.atualizar(consulta)

    flash("Consulta cancelada com sucesso!")
    return redirect(url_for("consulta_detalhes", consulta_id=consulta_id))

if __name__ == "__main__":
    app.run(debug=True)