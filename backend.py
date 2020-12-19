
import json
from flask import Flask, jsonify, request, send_file, render_template, redirect
from flask_pymongo import PyMongo
from pymongo import MongoClient
import hashlib



app = Flask(__name__)

client = MongoClient("mongodb+srv://admin:Jamau@hackathon.0lxfu.mongodb.net/<dbname>?retryWrites=true&w=majority")
dbInfected= client.get_database('COVID-Infected')
infectados = dbInfected.Infected

#funcion para añadir MAC Infectao
@app.route('/registrarInfectado',methods=['POST'])
def registrarInfectado():
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


@app.route('/usuarios',methods=['GET'])
def getUser():
    mac = "AAA"
    existsOne = infectados.Mac.find({"MAC":Mac})
    myvar = "the answer is {}".format(existsOne)
    return myvar

#funcion para devolver toda la tabla

#print (infectados.find_one({"MAC": "AAAAA"}))
