from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timezone, timedelta
from flask_apscheduler import APScheduler
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

from repositories.consulta_repository import ConsultaRepository
from repositories.user_repository import UserRepository
from jobs.atualizar_atrasadas import atualizar_consultas_atrasadas
from models.consulta import Consulta
from models.user import User

import os

# ======== CARREGAR VARIÁVEIS DE AMBIENTE ========
load_dotenv()

# ======== CONFIGURAÇÃO DO FLASK ========
app = Flask(__name__)
app.secret_key = os.getenv("PSW_SECRET")
app.config["SCHEDULER_API_ENABLED"] = True

# ======== CONEXÃO COM MONGODB ========
client = MongoClient(os.getenv("MONGO_URI"))
db = client["fila_zero"]
users_collection = db["users"]
consultas_collection = db["consultas"]

user_repository = UserRepository(users_collection)
consulta_repository = ConsultaRepository(consultas_collection)

# ======== CONFIGURAÇÃO DO SCHEDULER ========
scheduler = APScheduler()
scheduler.init_app(app)

# Job para atualizar consultas atrasadas a cada 10 minutos
scheduler.add_job(
    id="atualizar_atrasadas",
    func=atualizar_consultas_atrasadas,
    args=[consulta_repository],
    trigger="interval",
    minutes=10
)

scheduler.start()


# ======== FUNÇÃO AUXILIAR ========
def serialize_user(user):
    """Converte ObjectId do usuário para string para uso na sessão."""
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }


# ======== ROTAS DE PÁGINAS ========

@app.route("/", endpoint='login', methods=["GET"])
def login():
    """Página de login."""
    session.clear()
    return render_template("login.html")



@app.route("/principal")
def principal():
    """Dashboard principal com estatísticas e cronograma semanal."""
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
        "scheduled": sum(1 for c in consultas if (c.status == "marcado" and c.data_hora >= agora) or (c.status == "adiado")),
        "waiting": sum(1 for c in consultas if c.status == "atrasado"),
        "completed": sum(1 for c in consultas if c.status == "finalizado" and c.data_hora.date() >= inicio_semana),
    }

    # ===== CRONOGRAMA SEMANAL =====
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
        day_consultas = [c for c in consultas if c.data_hora.date() == day_date]
        week_days.append({
            "date": day_date,
            "day_name": DAYS_PT[day_date.weekday()],
            "is_today": day_date == today,
            "consultas": sorted(day_consultas, key=lambda x: x.data_hora)
        })

    return render_template(
        "principal.html",
        user_papel=session.get("user_papel"),
        user_nome=session.get("user_nome"),
        consultas=consultas,
        stats=stats,
        week_days=week_days
    )

@app.route("/registrar_consultas", methods=["GET"])
def registrar_consultas():
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    return render_template(
        "registrar_consultas.html",
        user_papel=session.get("user_papel")
    )



@app.route("/consultas", methods=["GET"])
def consultas():
    """Lista de consultas com busca e estatísticas."""
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    # ===== BUSCA =====
    termo = request.args.get("q")
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
    consulta_repository.atualizar_atrasadas()
    consultas = [Consulta.from_dict(c) for c in consultas_cursor]

    # ===== ESTATÍSTICAS =====
    agora = datetime.now(timezone.utc)
    inicio_semana = agora.date() - timedelta(days=agora.weekday())
    stats = {
        "scheduled": sum(1 for c in consultas if c.status == "marcado" and c.data_hora >= agora),
        "waiting": sum(1 for c in consultas if c.status == "atrasado"),
        "completed": sum(1 for c in consultas if c.status == "finalizado" and c.data_hora.date() >= inicio_semana),
    }

    return render_template(
        "consultas.html",
        user_papel=session.get("user_papel"),
        user_nome=session.get("user_nome"),
        consultas=consultas,
        stats=stats,
        termo=termo
    )



@app.route("/register", methods=["GET"])
def register():
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    if session.get("user_papel") != "admin":
        flash("Acesso restrito a administradores")
        return redirect(url_for("principal"))

    return render_template(
        "register.html",
        user_nome=session.get("user_nome")
    )



# ======== ROTAS DE AUTENTICAÇÃO ========
@app.route("/login_action", methods=["POST"])
def login_action():
    """Processa login do usuário."""
    email = request.form.get("email")
    senha = request.form.get("password")

    if not email or not senha:
        flash("Preencha todos os campos")
        return redirect(url_for("login"))

    # ===== BUSCAR USUÁRIO =====
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        flash("Usuário não encontrado")
        return redirect(url_for("login"))

    user = User.from_dict(user_data)
    if not user.verificar_senha(senha):
        flash("Senha incorreta")
        return redirect(url_for("login"))

    # ===== SALVAR SESSÃO =====
    session.clear()
    session["user_id"] = str(user.id)
    session["user_nome"] = user.nome
    session["user_papel"] = user.papel

    flash(f"Bem-vindo, {user.nome}!")
    return redirect(url_for("principal"))



@app.route("/register_action", methods=["POST"])
def register_action():
    """Processa o registro de um usuário."""
    nome = request.form.get("name")
    papel = request.form.get("role")
    email = request.form.get("email")
    senha = request.form.get("password")
    user_data = users_collection.find_one({"email": email})
    if user_data:
        flash("Email já cadastrado")
        return redirect(url_for("register"))
    
    funcionario = User.criar(
        nome=nome,
        email=email,
        senha=senha,
        papel=papel
    )

    user_repository.salvar(funcionario)

    return redirect(url_for("register"))



@app.route("/registrar-consulta-action", methods=["POST"])
def registrar_consulta_action():

    # ===== COLETAR DADOS DO FORM =====
    nome_paciente = request.form.get("nome_paciente")
    cpf_paciente = request.form.get("cpf_paciente")
    telefone = request.form.get("telefone")
    tipo_consulta = request.form.get("tipo_consulta")
    data_hora_str = request.form.get("data_hora")

    # ===== VALIDAÇÃO =====
    if not all([nome_paciente, cpf_paciente, telefone, tipo_consulta, data_hora_str]):
        flash("Preencha todos os campos")
        return redirect(url_for("registrar_consultas"))

    # Converter data/hora
    try:
        data_hora = datetime.fromisoformat(data_hora_str)
    except ValueError:
        flash("Data e hora inválidas")
        return redirect(url_for("registrar_consultas"))

    # ===== CRIAR CONSULTA =====
    consulta = Consulta.criar(
        nome_paciente=nome_paciente,
        cpf_paciente=cpf_paciente,
        telefone=telefone,
        tipo_consulta=tipo_consulta,
        data_hora=data_hora
    )

    # ===== SALVAR NO BANCO =====
    consulta_repository.salvar(consulta)

    flash("Consulta registrada com sucesso!")
    return redirect(url_for("registrar_consultas"))



@app.route("/logout")
def logout():
    """Realiza logout do usuário."""
    session.clear()
    flash("Logout realizado com sucesso!")
    return redirect(url_for("login"))



# ======== ROTAS DE CONSULTA INDIVIDUAL ========
@app.route("/consulta/<consulta_id>", methods=["GET"])
def consulta_detalhes(consulta_id):
    """Exibe detalhes de uma consulta específica."""
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))

    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)
    return render_template("consulta_detalhes.html", user_nome=session.get("user_nome"), consulta=consulta, user_papel=session.get("user_papel"))



# ======== ROTAS DE AÇÕES SOBRE CONSULTA ========
@app.route("/consulta/<consulta_id>/finalizar", methods=["POST"])
def finalizar_consulta(consulta_id):
    """Finaliza uma consulta."""
    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)
    consulta.finalizar()
    consulta_repository.atualizar(consulta)

    flash("Consulta finalizada com sucesso!")
    return redirect(url_for("consulta_detalhes", consulta_id=consulta_id))



@app.route("/consulta/<consulta_id>/adiar", methods=["POST"])
def adiar_consulta(consulta_id):
    """Adia uma consulta para nova data e hora."""
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



@app.route("/consulta/<consulta_id>/cancelar", methods=["POST"])
def cancelar_consulta(consulta_id):
    """Cancela uma consulta."""
    consulta_data = consultas_collection.find_one({"_id": ObjectId(consulta_id)})
    if not consulta_data:
        flash("Consulta não encontrada")
        return redirect(url_for("consultas"))

    consulta = Consulta.from_dict(consulta_data)
    consulta.cancelar()
    consulta_repository.atualizar(consulta)

    flash("Consulta cancelada com sucesso!")
    return redirect(url_for("consulta_detalhes", consulta_id=consulta_id))



# ======== EXECUÇÃO DO APP ========
if __name__ == "__main__":
    app.run(debug=True)
