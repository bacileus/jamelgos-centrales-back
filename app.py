import flask
from flask import request
import json
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.json_util import dumps, loads
import hashlib

app = flask.Flask(__name__)


myclient = MongoClient("mongodb+srv://admin:Jamau@hackathon.0lxfu.mongodb.net/<dbname>?retryWrites=true&w=majority")
dbInfected = myclient["COVID-Infected"]
#dbInfected= client.get_database('COVID-Infected')
colInfected = dbInfected["Infected"]


@app.route('/', methods=['GET'])
def home():
    info = "AQUÍ NO HAY NADA CARNAL\n ves a /users o /users/MAC="
    return info


@app.route('/users',methods=['GET'])
def getUsers():
    #all_users = [{"MAC": user.MAC, "noticedTime": user.noticedTime} for user in colInfected.find()]
    #macs = "macs: "
    #for mac in colInfected.find():
    #    macs += " // " + str(mac)
    cursor = colInfected.find()
    json_results = []
    for result in cursor:
        json_results.append(result)
    return flask.jsonify(json_results)


@app.route('/users',methods=['POST'])
def postUser():
    MAC = request.args.get('MAC')
    usuerInser = { "MAC": MAC }
    colInfected.insert_one(usuerInser)
    response = {"response":"registered"}
    return jsonify(response),201
