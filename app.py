from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from models.user import User
from models.consulta import Consulta


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("PSW_SECRET")

# Conexão com MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["flaskdb"]
users_collection = db["users"]
consultas_collection = db["consultas"]



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
        return redirect(url_for("login_page"))

    # Buscar consultas
    consultas_cursor = consultas_collection.find()
    consultas = [Consulta.from_dict(c) for c in consultas_cursor]

    # Estatísticas
    stats = {
        "scheduled": sum(1 for c in consultas if c.status == "marcado"),
        "waiting": sum(1 for c in consultas if c.status == "aguardando"),
        "completed": sum(1 for c in consultas if c.status == "finalizado")
    }

    # ===== CRONOGRAMA DA SEMANA =====
    today = datetime.now(timezone.utc).date()

    week_days = []
    DAYS_PT = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }

    for i in range(7):
        day_date = today + timedelta(days=i)

        day_consultas = [
            c for c in consultas
            if c.scheduled_at.date() == day_date
        ]

        week_days.append({
            "date": day_date,
            "day_name": DAYS_PT[day_date.weekday()],
            "is_today": day_date == today,
            "consultas": sorted(day_consultas, key=lambda x: x.scheduled_at)
        })

    return render_template(
        "principal.html",
        user_name=session.get("user_name"),
        consultas=consultas,
        stats=stats,
        week_days=week_days
    )


@app.route("/consultas", methods=["GET"])
def consultas():
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("login"))
    return render_template("consultas.html")



# ======== Rota de login (POST) ========
@app.route("/login_action", methods=["POST"])
def login_action():
    email = request.form["email"]
    password = request.form["password"]

    # Busca usuário no MongoDB
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        flash("Usuário não encontrado")
        return redirect(url_for("login"))

    user = User.from_dict(user_data)

    # Verifica senha
    if not user.check_password(password):
        flash("Senha incorreta")
        return redirect(url_for("login"))

    # Login bem-sucedido → salva dados na session
    session["user_id"] = str(user.id)
    session["user_name"] = user.name
    session["user_role"] = user.role

    flash(f"Bem-vindo, {user.name}!")
    return redirect(url_for("principal"))

# ======== Logout ========
@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)