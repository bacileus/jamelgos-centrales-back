from flask_cors import CORS, cross_origin
import json
from flask import Flask, jsonify, request, send_file, render_template, redirect
from flask_pymongo import PyMongo
from pymongo import MongoClient
import hashlib



app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
client = MongoClient("mongodb+srv://admin:Jamau@hackathon.0lxfu.mongodb.net/<dbname>?retryWrites=true&w=majority")
dbInfected= client.get_database('COVID-Infected')
infectados = dbInfected.Infected

#funcion para añadir MAC Infectao

#funcion para devolver toda la tabla

print (infectados.find_one({"MAC": "AAAAA"}))
