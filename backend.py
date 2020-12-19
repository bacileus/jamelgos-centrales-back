import json
from flask import Flask, jsonify, request, send_file, render_template, redirect
from flask_pymongo import PyMongo
from pymongo import MongoClient
import hashlib



app = Flask(__name__)
client = MongoClient("mongodb+srv://admin:Jamau@hackathon.0lxfu.mongodb.net/<dbname>?retryWrites=true&w=majority")
dbInfected= client.get_database('COVID-Infected')
infectados = dbInfected.Infected

print (infectados.find_one({"MAC": "AAAAA"}))
