import flask
from flask import request
import json
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.json_util import dumps
import hashlib
from datetime import datetime

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
    return dumps(colInfected.find())


@app.route('/users',methods=['POST'])
def postUser():
    MAC = request.args.get('MAC')
    usuerInser = { "MAC": MAC, "noticedTime": datetime.now() }
    colInfected.insert_one(usuerInser)
    response = {"response":"registered"}
    return flask.jsonify(response),201
