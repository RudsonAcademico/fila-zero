from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timezone
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
@app.route("/", endpoint='index', methods=["GET"])
def index():
    session["user_id"] = None
    session.clear()
    return render_template("index.html")


@app.route("/home")
def dashboard():
    if "user_id" not in session:
        flash("Faça login primeiro")
        return redirect(url_for("index"))

    # Buscar consultas do MongoDB
    consultas_cursor = consultas_collection.find()
    consultas = [Consulta.from_dict(c) for c in consultas_cursor]

    # Calcular estatísticas
    stats = {
        "scheduled": sum(1 for c in consultas if c.status == "marcado"),
        "waiting": sum(1 for c in consultas if c.status == "aguardando"),
        "completed": sum(1 for c in consultas if c.status == "finalizado")
    }

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        consultas=consultas,
        stats=stats
    )



# ======== Rota de login (POST) ========
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    # Busca usuário no MongoDB
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        flash("Usuário não encontrado")
        return redirect(url_for("index"))

    user = User.from_dict(user_data)

    # Verifica senha
    if not user.check_password(password):
        flash("Senha incorreta")
        return redirect(url_for("index"))

    # Login bem-sucedido → salva dados na session
    session["user_id"] = str(user.id)
    session["user_name"] = user.name
    session["user_role"] = user.role

    flash(f"Bem-vindo, {user.name}!")
    return redirect(url_for("dashboard"))

# ======== Logout ========
@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)