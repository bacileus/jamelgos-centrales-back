
import flask
from flask import request
import json
from flask_pymongo import PyMongo
from pymongo import MongoClient
import hashlib

app = flask.Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return "Aqui no hay nada carnal"



client = MongoClient("mongodb+srv://admin:Jamau@hackathon.0lxfu.mongodb.net/<dbname>?retryWrites=true&w=majority")
dbInfected= client.get_database('COVID-Infected')
infectados = dbInfected.Infected



@app.route('/usuarios',methods=['GET'])
def getUser():
    Mac = "AAAAA"
    existsOne = infectados.Mac.find({"MAC":Mac})
    myvar = "the answer is {}".format(existsOne)
    return myvar



@app.route('/usuarios',methods=['POST'])
def registrarUsuario():
    NewInfected = request.get_json()
    Mac = NewInfected.get("MAC")
    existsOne = infectados.Mac.find({"MAC":Mac})
    empty = True
    for i in existsOne:
        empty = False
    if empty:
        infectados.Mac.insert_one({"MAC":Mac})
        response = {"response":"registered"}
        return jsonify(response),201
    else:
        response = {"response":"exists"}
        return jsonify(response),406