from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

app = Flask(__name__)

# Conexão com MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["flaskdb"]
users = db["users"]
