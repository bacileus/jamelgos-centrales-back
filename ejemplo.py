#imports
from flask_cors import CORS, cross_origin
import json
import os
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request, send_file, render_template, redirect
from flask_pymongo import PyMongo
import hashlib
import datetime
import random
from geojson import Point, MultiPoint, LineString, Polygon, MultiLineString,Feature, FeatureCollection
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
import urllib3
urllib3.disable_warnings()

#creamos app flask y conectamos con mongoDB
app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/users'
dbUsers = PyMongo(app, uri='mongodb://localhost:27017/users')
dbAnnouncements = PyMongo(app, uri='mongodb://localhost:27017/announcements')
dbCompanies = PyMongo(app, uri='mongodb://localhost:27017/companies')
dbActiveSessions = PyMongo(app,uri='mongodb://localhost:27017/activeSessions')
dbAnnouncementsOld = PyMongo(app,uri='mongodb://localhost:27017/announcementsOld')	
dbQR = PyMongo(app,uri='mongodb://localhost:27017/QR')

#START PARA DEBUG
@app.route('/listUsers',methods=['GET'])
def listUsr():
    allUsers = dbUsers.db.users.find()
    for i in allUsers:
        print(i)
        print("----------------")
    return jsonify({"response":"OK"}),200

@app.route('/listCompanies',methods=['GET'])
def listComp():
    allCompanies = dbCompanies.db.companies.find()
    for i in allCompanies:
        print(i)
        print("----------------")
    return jsonify({"response":"OK"}),200
def debugging(x):
    print("")
    print("")
    print("----------------------")
    print(x)
    print("----------------------")
    print("")
    print("")
#END PARA DEBUG


def getCoordinates(location):
    #llamar a la api con el string
    #pillar el JSON y pillar las coordenadas
    apiUrl = 'https://maps.googleapis.com/maps/api/geocode/json?address='+location+'&key=AIzaSyA3Nk69VycAISBKEolQpbNtApVjCYjlj2s'
    s = requests.Session()
    ret = s.get(apiUrl)
    if str(ret.status_code) == str(200):
        return json.loads(ret.text)
    else:
        return "unsuccessful"

def geocoding(location):
    latitude = location.get("lat")
    longitude = location.get("lng")
    key = 'AIzaSyA3Nk69VycAISBKEolQpbNtApVjCYjlj2s'
    s = requests.Session()
    retStr = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + str(latitude) + ','+str(longitude)+'&key='+key
    ret = s.get(retStr)
    if str(ret.status_code) == str(200):
        return json.loads(ret.text)
    return "unsuccessful"



def calculateDistance(location1, location2):
    #id1 = location1.get("placeID")
    ret = geocoding(location1)
    if ret == "unsuccessful":
        return -1
    ret2 = ret.get("results")[0].get("place_id")
    ret3 = location2
    key = 'AIzaSyA3Nk69VycAISBKEolQpbNtApVjCYjlj2s'
    s = requests.Session()
    origen = 'origins=place_id:'+ret2
    destino = '&destinations=place_id:'+ret3
    apiUrl = 'https://maps.googleapis.com/maps/api/distancematrix/json?'+origen+destino+'&mode=walking'+'&key='+key
    r = s.get(apiUrl)
    if r.status_code == 200:
        resp = json.loads(r.text)
        return resp.get("rows")[0].get("elements")[0].get("distance").get("value")
    return "unsuccessful"

def sendd_mail(to):
    title = 'What are you waiting to start searching for offers?'
    msg = '<font color="orange"> <h2>{title} </font></h2>\n'.format(title=title)
    gmail_user = 'deall4all@gmail.com'
    gmail_password = 'deall4allofus!!'
    sent_from = 'deall4all@gmail.com'
    message = MIMEText(msg,'html')
    message['From'] = 'deall4all@gmail.com'
    message['To'] = to
    message['Cco'] = 'deall4all@gmail.com'
    message['Subject'] = 'Welcome to Deall!'
    msg_full = message.as_string()
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, msg_full)
        server.close()

        debugging('Email sent!')
    except Exception as e:
        print(e)
        debugging('Something went wrong...')


#funcion que nos genera un token para tener constancia de la sesion
def generateToken(username):
    x = datetime.datetime.now()
    y = str(x)+username+str(random.randrange(1000000))
    z = hashlib.sha256(y.encode('utf-8')).hexdigest()
    return z

#funcion que nos apunta los usuarios que tenemos logueados actualmente en el sistema
def registerSession(username,sessionToken):
    activeSessions = dbActiveSessions.db.activeSessions.find({"username":username})
    if len(list(activeSessions)) > 0:
        return False
    dbActiveSessions.db.activeSessions.insert_one({"username":username,"token":sessionToken})
    return True



#funcion para hacer logout
@app.route('/logout', methods=['POST'])
def logout():
    token = request.get_json().get("token")
    dbActiveSessions.db.activeSessions.remove({"token":token})
    return jsonify({"response":"logged out"}),200


#funcion para registrar usuarios
@app.route('/registerUser',methods=['POST'])
def registerUser():
    #coger params de la request
    debugging("Register new user")
    newUser = request.get_json()
    debugging(newUser)
    user = newUser.get("username")
    passwd = newUser.get("password")
    email = newUser.get("email")
    realName = newUser.get("realName")
    favourites = []
    hashedPasswd = hashlib.sha256(passwd.encode('utf-8')).hexdigest()
    existsOne = dbUsers.db.users.find({"username":user})
    existsTwo = dbCompanies.db.companies.find({"username":user})
    debugging("Password: " + hashedPasswd)
    empty = True
    for i in existsOne:
        empty = False
    for i in existsTwo:
        empty = False
    if empty:
        path = "/var/Deall/users/"+user
        dbUsers.db.users.insert_one({"username":user,"password":hashedPasswd,"email":email,"realName":realName, "favourites":favourites, "directory":path})
        response = {"response":"registered"}
        #create directory
        os.mkdir(path)
        #send mail
        sendd_mail(email)
        return jsonify(response),201
    else:
        response = {"response":"exists"}
        return jsonify(response),406

#funcion para loguear usuarios
@app.route('/loginUser',methods=['POST'])
def loginUser():
    #cogemos username y pass
    json = request.get_json()
    user = json.get("username")
    passw = json.get("password")
    #hasheamos password y buscamos en la DB para comparar
    hashedPasswd = hashlib.sha256(passw.encode('utf-8')).hexdigest()
    database = dbUsers.db.users.find({"username":user})
    for i in database:
        if i["password"] == hashedPasswd:
            token = generateToken(user)
            response = {"response":"success", "token":token}
            success = registerSession(user,token)
            if success:
                return jsonify(response),200
    response = {"response":"error"}
    return jsonify(response),403


#funcion para registrar empresas
@app.route('/registerCompany',methods=['POST'])
def registerCompany():
    #coger params de la request
    newCompany = request.get_json()
    user = newCompany.get("username")
    passwd = newCompany.get("password")
    email = newCompany.get("email")
    companyName = newCompany.get("companyName")
    companyNIF = newCompany.get("companyNIF")
    city = newCompany.get("city")
    street = newCompany.get("street")
    number = newCompany.get("number")
    hashedPasswd = hashlib.sha256(passwd.encode('utf-8')).hexdigest()
    existsOne = dbCompanies.db.companies.find({"username":user})
    existsTwo = dbUsers.db.users.find({"username":user})
    existsThree = dbCompanies.db.companies.find({"companyName":companyName})
    empty = True
    for i in existsOne:
        empty = False
    for i in existsTwo:
        empty = False
    for i in existsThree:
        empty = False
    if empty:
        coordinates = getCoordinates(street+',' + number + ','+city)
        path = "/var/Deall/companies/"+user
        debugging(coordinates)
        if str(coordinates) != "unsuccessful":
            placeID = coordinates.get("results")[0].get("place_id")
            debugging(placeID)
            latLong = coordinates.get("results")[0].get("geometry").get("location")
            dbCompanies.db.companies.insert_one({"username":user,"password":hashedPasswd,"email":email,"companyName":companyName, "companyNIF":companyNIF, "city":city, "street":street, "number":number,"directory":path, "latLong": latLong, "placeID":placeID})
            os.mkdir(path)
            sendd_mail(email)
            response = {"response":"registered"}

            return jsonify(response),201
    response = {"response":"exists"}
    return jsonify(response),406


#funcion para loguear empresas
@app.route('/loginCompany',methods=['POST'])
def loginCompany():
    #cogemos username y pass
    json = request.get_json()
    user = json.get("username")
    passw = json.get("password")
    #hasheamos password y buscamos en la DB para comparar
    hashedPasswd = hashlib.sha256(passw.encode('utf-8')).hexdigest()
    database = dbCompanies.db.companies.find({"username":user})
    for i in database:
        if i["password"] == hashedPasswd:
            token = generateToken(user)
            response = {"response":"success", "token":token}
            success = registerSession(user,token)
            if success:
                return jsonify(response),200
    response = {"response":"error"}
    return jsonify(response),403


#funcion para obtener anuncios
@app.route('/getAnnouncementsByRadius', methods=['POST'])
def getAnnouncements():
    debugging("Get announcements by radius")
    jsonR = request.get_json()
    token = jsonR.get("token")
    tag = jsonR.get("type")
    location = json.loads(jsonR.get("actualLocation"))
    tokenFind = dbActiveSessions.db.activeSessions.find({"token":token})
    hasValues = False
    for i in tokenFind:
        hasValues = True
    if not hasValues:
        return jsonify({"response":"you are not logged"}),400
    radio = jsonR.get("radius")
    tagged = str(jsonR.get("byTag"))
    values = None
    if tagged == "True":
        values = dbAnnouncements.db.announcements.find({"type":tag})
    else:
        values = dbAnnouncements.db.announcements.find({"_id":{"$gte":0}})
    responseList = []
    #pillamos todos los valores de la BD y calculamos distancia 1 a 1
    hasAnnouncements = False
    for i in values:
        #pillar la empresa del anuncio
        company = i["company"]
        #buscar las coordenadas de la empresa
        search = dbCompanies.db.companies.find({"companyName":company})
        placeID = None
        for j in search:
            placeID = j["placeID"]
        #calcular distancia entre el tio y la empresa
        dist = calculateDistance(location,placeID)
        debugging("calculamos dist")
        if int(dist) <= radio and int(dist) >= 0:
            hasAnnouncements = True
            responseList.append(json.dumps({"description":i["description"],"announcementID":i["_id"],"company":i["company"],"distance":dist,"type":i["type"],"rate":i["rate"]}))
    if hasAnnouncements:
        debugging("List of announcements: ")
        debugging(responseList)
        return jsonify({"response":responseList}),200
    else:
        return jsonify({"response":"unsuccessful"}),400

#funcion para obtener la img de un anuncio
@app.route('/getAnnouncementImage/<idImg>', methods=['GET'])
def getImage(idImg):
    #image = request.get_json()
    ''' 
    suponemos que para pedir imagen nos pasan el ID que le hemos 
    dado con getAnnouncements()
    '''
    #nos pasan el ID de la img (unico), buscamos el filename
    idImg = int(idImg)
    fileN = dbAnnouncements.db.announcements.find({"_id":idImg})
    fileName = ""
    for i in fileN:
        fileName = i["filename"]
    if fileName == "":
        return jsonify({"response":"this announcement has no image"}),400 
    #cogemos la extension del fichero para saber el mimetype, asi
    #no solo aceptamos jpeg, sino gif, png...
    fileExtension = fileName.split('.')[1]
    mimeType = 'image/' + fileExtension
    return send_file(fileName, mimetype=mimeType)


#funcion para subir anuncios
@app.route('/postAnnouncement',methods=['POST'])
def postAnnouncement():
    #pillar el JSON del request
    newAnnouncement = request.get_json()
    debugging("Post announcements")
    debugging(newAnnouncement)
    token = newAnnouncement.get("token")
    companyRow = dbActiveSessions.db.activeSessions.find({"token":token})
    username = None
    for i in companyRow:
        username = i["username"]
    company = None
    companyRowTwo = dbCompanies.db.companies.find({"username":username})
    for i in companyRowTwo:
        company = i["companyName"]
    if (company == None):
        return jsonify({"response":"you are not logged or you are not a company"}),400
     
    description = newAnnouncement.get("description")
    pruebas = dbAnnouncements.db.announcements.find().sort("_id",-1).limit(1)
    pruebasTwo = dbAnnouncementsOld.db.announcementsOld.find().sort("_id",-1).limit(1)
    idTwo = 0
    for i in pruebas:
        idd = i["_id"]
    for i in pruebasTwo:
        idTwo = i["_id"]
    idd = max(idd,idTwo)+1
    now = datetime.datetime.now()
    date = now
    typ = newAnnouncement.get("type")
    usersRating = []
    dbAnnouncements.db.announcements.insert_one({"company":company, "description": description, "date":date,"rate":float(0.000001), "usersRating":usersRating, "_id":idd, "type":typ,"filename":""})
    response = {"response":"success","announcementID":idd}
    return jsonify(response),200

#funcion para subir la img de un anuncio
@app.route('/postImage', methods=['POST','GET'])
def post():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            token = request.form.get('token')
            announcementID = request.form.get("announcementID")
            announcementID = int(announcementID)
            if image.filename == "":
                return jsonify({"response":"you have noy uploaded a file"}),400
            ann = dbAnnouncements.db.announcements.find({"_id":announcementID})
            one = False
            fileName = None
            co = None
            for i in ann:
                one = True
                fileName = i["filename"]
                co = i["company"]
            if not one:
                return jsonify({"response":"no announcement with this ID"}),400
            usern = dbActiveSessions.db.activeSessions.find({"token":token})
            username = None
            for i in usern:
                username = i["username"]
            if username == None:
                return jsonify({"response":"you are not logged"}),400
            comp = dbCompanies.db.companies.find({"username":username})
            companyName = None
            for i in comp:
                companyName = i["companyName"]
            if companyName == None:
                return jsonify({"response":"you are not a company"}),400

            coID = dbCompanies.db.companies.find({"companyName":co})
            coUs = None
            for i in coID:
                coUs = i["username"]
            if coUs != username:
                return jsonify({"response":"this announcement is not yours!"}),400
            if fileName != "" and fileName != None:
                os.remove(fileName)
            s = image.filename.split('.')
            ff = str(announcementID) + "_"+s[0]
            ff = ff +'.'+ s[1]
            path = "/var/Deall/companies/"+username+"/"+ff
            image.save(path)
            dbAnnouncements.db.announcements.update_one({"_id":announcementID},{"$set":{"filename":path}})
            #return redirect(request.url)
            return jsonify({"response":"success"}),200
    return render_template("upload_image.html")


#funcion para borrar anuncios NO DE HISTORIAL 
@app.route('/deleteAnnouncement',methods=['POST'])
def dd():
    debugging("Delete announcement")
    jj = request.get_json()
    token = jj.get("token")
    announcementID = int(jj.get("announcementID"))
    if announcementID < 0:
        return jsonify({"response":"impossible to delete this"}),400
    username = None
    usern = dbActiveSessions.db.activeSessions.find({"token":token})
    for i in usern:
        username = i["username"]
    if username == None:
        return jsonify({"response":"you are not logged"}),400
    company = None
    comp = dbCompanies.db.companies.find({"username":username})
    for i in comp:
        company = i["companyName"]
    if company == None:
        return jsonify({"response":"you are not a company"}),400
    own = dbAnnouncements.db.announcements.find({"_id":announcementID})
    owner = None
    for i in own:
        owner = i["company"]
    if owner != company:
        return jsonify({"response":"this announcement is not yours!"}),400
    anns = dbAnnouncements.db.announcements.find({"_id":announcementID})
    fileName = None
    for i in anns:
        fileName = i["filename"]
    if fileName == None:
        return jsonify({"response":"no filename"})
    os.remove(fileName)
    dbAnnouncements.db.announcements.delete_one({"_id":announcementID})
    allUsers = dbUsers.db.users.find()
    for i in allUsers:
        username = i["username"]
        vect = i["favourites"]
        if announcementID in vect:
            vect.remove(announcementID)
            dbUsers.db.users.update_one({"username":username},{"$set":{"favourites":vect}})
    return jsonify({"response":"successfully deleted"}),200




#funcion para mover los anuncios viejos a la bd de historial
@app.route('/toHistory', methods=['POST'])
def delete():
    '''date = datetime.datetime.now() - timedelta(days=1)
    #buscamos anuncios a borrar y guardamos el id maximo
    toDelete = dbAnnouncements.db.announcements.find({"date":{"$lt":date}})
    pruebas = dbAnnouncements.db.announcements.find().sort("_id",-1).limit(1)
    
    maximum = -1
    for i in pruebas:
        maximum = i["_id"]
    #como queremos guardarlos, los insertamos en otra bd de anuncios antiguos
    for i in toDelete:
        
        dbAnnouncementsOld.db.announcementsOld.insert(i)
    #los borramos de la bd de anuncios actualizados
    dbAnnouncements.db.announcements.delete_one({"date":{"$lt":date}})
    newA = dbAnnouncements.db.announcements.find()
    #si hemos borrado todos, necesitamos un anuncio del que podamos sacar el id
    if len(list(newA)) < 3:
        dbAnnouncements.db.announcements.insert({"_id":maximum})

    '''
    debugging("Move announcement to history")
    tt = request.get_json()
    token = tt.get("token")
    announcementID = int(tt.get("announcementID"))
    username = None
    usern = dbActiveSessions.db.activeSessions.find({"token":token})
    for i in usern:
        username = i["username"]
    if username == None:
        return jsonify({"response":"you are not logged"}),400
    ann = dbAnnouncements.db.announcements.find({"_id":announcementID})
    company = None
    comp = dbCompanies.db.companies.find({"username":username})
    for i in comp:
        company = i["companyName"]
    if company == None:
        return jsonify({"response":"you are not a company"}),400
    for i in ann:
        exists = True
        if company != i["company"]:
            return jsonify({"response":"this announcement is not yours!"}),400
        dbAnnouncementsOld.db.announcementsOld.insert({"_id":i["_id"],"description":i["description"],"date":i["date"],"type":i["type"],"company":i["company"],"rate":i["rate"],"usersRating":i["usersRating"],"filename":i["filename"]})
        allUsers = dbUsers.db.users.find()
        for k in allUsers:
            favourites = k["favourites"]
            username = k["username"]
            if announcementID in favourites:
                favourites.remove(announcementID)
                dbUsers.db.users.update_one({"username":username},{"$set":{"favourites":favourites}})
        dbAnnouncements.db.announcements.delete_one({"_id":i["_id"]})
    return jsonify({"response":"updated"}),200

#funcion para crear QR
@app.route('/createQR',methods=['POST'])
def createQR():
    debugging("Create QR")
    pet = request.get_json()
    session = pet.get("token")
    announcementID = int(pet.get("announcementID"))
    activ = dbActiveSessions.db.activeSessions.find({"token":token})
    username = None
    for i in activ:
        username = i["username"]
    if username == None:
        return jsonify({"response":"you are not logged"}),400
    us = dbUsers.db.users.find({"username":username})
    favourites = []
    isUser = False
    for i in us:
        isUser = True
        favourites = i["favourites"]
    if not isUser:
        return jsonify({"response":"you are not a normal user"}),400
    if announcementID not in favourites:
        return jsonify({"response": "you do not have this announcement in favourites"}),400
    string = hashlib.sha1(str(session)+str(announcementID)).encode('utf-8').hexdigest()
    string = 'https://10.4.41.150:8080/exchangeQR/'+string
    debugging("The QR string is: " + string)
    dbQR.db.QR.insert({"stringQR":string,"username":username,"announcementID":announcementID})
    return jsonify({"response":"QR created","stringQR":string}),200

#funcion para canjear el QR
@app.route('/exchangeQR/<QRcode>', methods=['GET'])
def canjear(QRcode):
    ann = dbQR.db.QR.find({"stringQR":QRcode})
    announcementID = None
    username = None
    for i in ann:
        announcementID = i["announcementID"]
        username = i["username"]
    if announcementID == None:
        return jsonify({"response":"QR code not generated or already exchanged"}),400

    dbQR.db.QR.delete_many({"username":username,"announcementID":announcementID})   
    favourites = []
    user = dbUsers.db.users.find({"username":username})
    for i in user:
        favourites = i["favourites"]
        if announcementID in favourites:
            favourites.remove(announcementID)
            dbUsers.db.users.update({"username":username},{"$set":{"favourites":favourites}})
    return render_template("successful_QR.html")

@app.route('/toFavourites',methods=['POST'])
def afavoritos():
    debugging("Add announcement to favourites")
    json = request.get_json()
    token = json.get("token")
    announcementID = int(json.get("announcementID"))
    cur = dbActiveSessions.db.activeSessions.find({"token":token})
    user = None
    for i in cur:
        user = i["username"]
    userFull = dbUsers.db.users.find({"username":user})
    favouritesUserOld = [""]
    for i in userFull:
        favouritesUserOld = i["favourites"]
    if announcementID not in favouritesUserOld:
        debugging("Old favourites:")
        debugging(favouritesUserOld)
        favouritesUserOld.append(announcementID)
        debugging("New favourites:")
        debugging(favouritesUserOld)
        string = hashlib.sha1((str(token)+str(announcementID)).encode('utf-8')).hexdigest()
        stringSave = string
        string = 'http://10.6.40.102:8080/exchangeQR/'+string
        debugging("The QR string is: " + string)
        debugging(user)
        dbQR.db.QR.insert({"stringQR":stringSave,"username":user,"announcementID":announcementID})
        dbUsers.db.users.update({"username":user},{"$set":{"favourites":favouritesUserOld}})
        response = {"response":"added"}
        return jsonify(response),200
    return jsonify({"response":"notAdded"}),400


@app.route('/removeFromFavourites',methods=['POST'])
def defavoritos():
    debugging("Remove from favourites")
    json = request.get_json()
    token = json.get("token")
    announcementID = int(json.get("announcementID"))
    cur = dbActiveSessions.db.activeSessions.find({"token":token})
    user = None
    for i in cur:
        user = i["username"]
    userFull = dbUsers.db.users.find({"username":user})
    favouritesUserOld = [""]
    for i in userFull:
        favouritesUserOld = i["favourites"]
    if announcementID in favouritesUserOld:
        debugging("Favourites before removing:")
        debugging(favouritesUserOld)
        favouritesUserOld.remove(announcementID)
        debugging("Favourites after removing:")
        debugging(favouritesUserOld)
        dbUsers.db.users.update({"username":user},{"$set":{"favourites":favouritesUserOld}})
        dbQR.db.QR.delete_one({"username":user,"announcementID":announcementID})
        response = {"response":"removed"}
        return jsonify(response),200
    return jsonify({"response":"notRemoved"}),400




@app.route('/rateAnnouncement',methods=['POST'])
def valor():
    debugging("Rate announcement")
    json = request.get_json()
    idAnnouncement = int(json.get("id"))
    userToken = json.get("token")
    rate = json.get("rate")
    rate = float(rate)
    if rate > 5:
        rate = 5
    if rate < 0:
        rate = 0
    userQuery = dbActiveSessions.db.activeSessions.find({"token":userToken})
    user = None
    for i in userQuery:
        user = i["username"]
    userQueryTwo = dbUsers.db.users.find({"username":user})
    lastIndex = None
    for i in userQueryTwo:
        user = i["username"]
        lastIndex = i
    favourites = None
    if not user == None:
        favourites = lastIndex["favourites"]
    if favourites == None or idAnnouncement not in favourites:
        return jsonify({"response":"user does not have the announcement in favourites"}),400
    announcement = dbAnnouncements.db.announcements.find({"_id":idAnnouncement})
    for i in announcement:
        actualUsers = i["usersRating"]
        if actualUsers != None:
            numberUsers = len(actualUsers) + 1
        else:
            numberUsers = 1
            actualUsers = [""]
        currentRating = i["rate"]
        debugging("Current rate:")
        debugging(currentRating)
        newRating = float((currentRating*(numberUsers-1) + rate)/numberUsers)
        if not user in actualUsers:
            actualUsers.append(user)
            debugging("New rate (the user has not rated before the announcement):")
            debugging(newRating)
            dbAnnouncements.db.announcements.update_one({"_id":idAnnouncement}, {"$set":{"usersRating":actualUsers, "rate":newRating}})   
            return jsonify({"response":"rated"}),200
        else:
            return jsonify({"response":"you have already rated this announcement"}),400
    return jsonify({"response":"unsuccessful"}) 


@app.route('/getAnnouncementsByCompany',methods=['POST'])
def gett():
    debugging("Get announcements by company")
    jsonR = request.get_json()
    debugging(jsonR)
    token = jsonR.get("token")
    company = dbActiveSessions.db.activeSessions.find({"token":token})
    hasActiveAnnouncements = False
    isLogged = False
    usernameCompany = None
    for i in company:
        isLogged = True
        usernameCompany = i["username"]
    company = dbCompanies.db.companies.find({"username":usernameCompany})
    companyName = None
    for i in company:
        hasActiveAnnouncements = True
        companyName = i["companyName"]
    debugging(companyName)
    if hasActiveAnnouncements:
        announcements = dbAnnouncements.db.announcements.find({"company":companyName})
        responseList = []
        for i in announcements:
            responseList.append(json.dumps({"announcementID":i["_id"],"description":i["description"],"rate":i["rate"],"usersRating":len(i["usersRating"])}))
        debugging("Announcements actives on the company:")
        debugging(responseList)
        return jsonify({"response":responseList}),200
    return jsonify({"response":"noAnnouncements"}),400

@app.route('/getHistoryCompany',methods=['POST'])
def gettoo():
    debugging("Get announcement history from a company")
    jsonR = request.get_json()
    token = jsonR.get("token")
    company = dbActiveSessions.db.activeSessions.find({"token":token})
    hasActiveAnnouncements = False
    isLogged = False
    usernameCompany = None
    for i in company:
        isLogged = True
        usernameCompany = i["username"]
    company = dbCompanies.db.companies.find({"username":usernameCompany})
    companyName = None
    for i in company:
        hasActiveAnnouncements = True
        companyName = i["companyName"]
    debugging(companyName)
    if hasActiveAnnouncements:
        announcements = dbAnnouncementsOld.db.announcementsOld.find({"company":companyName})
        responseList = []
        for i in announcements:
            responseList.append(json.dumps({"announcementID":i["_id"],"description":i["description"],"rate":i["rate"],"usersRating":len(i["usersRating"])}))
        debugging("History of announcements:")
        debugging(responseList)
        return jsonify({"response":responseList}),200
    return jsonify({"response":"noAnnouncements"}),400




@app.route('/getRateAnnouncement/<announcementID>',methods=['GET'])
def getting(announcementID):
    announcementRow = dbAnnouncements.db.announcements.find({"_id":int(announcementID)})
    rate = None
    for i in announcementRow:
        rate = i["rate"]
    if rate != None:
        return jsonify({"rate":rate}),200
    return jsonify({"response":"unsuccessful"}),400




@app.route('/getFavouritesUser',methods=['POST'])
def gettTwo():
    debugging("Get favourites")
    jsonR = request.get_json()
    token = jsonR.get("token")
    userSession = dbActiveSessions.db.activeSessions.find({"token":token})
    username = None
    for i in userSession:
        username = i["username"]
    if username == None:
        return jsonify({"response":"you are not logged"}),400
    userFavourites = dbUsers.db.users.find({"username":username})
    favourites = []
    response = []
    for i in userFavourites:
        favourites = i["favourites"]
        for j in favourites:
            findAnnouncement = dbAnnouncements.db.announcements.find({"_id":j})
            for k in findAnnouncement:
                QR = dbQR.db.QR.find({"username":username,"announcementID":j})
                for l in QR:
                    stringQR = l["stringQR"]
                    url = 'https://10.6.40.102:8080/exchangeQR/'+stringQR
                    response.append(json.dumps({"_id":k["_id"],"description":k["description"], "companyName":k["company"],"type":k["type"],"rate":k["rate"],"stringQR":url}))
    if (len(response))  < 1:
        debugging("User has no favourites")
        return jsonify({"response":response}), 200
    else:
        debugging("Favourites user:")
        debugging(favourites)
        return jsonify({"response":response}),200

@app.route('/toAnnouncement',methods=['POST'])
def gogo():
    debugging("Go to an announcement")
    json = request.get_json()
    token = json.get("token")
    idAnnouncement = json.get("idAnnouncement")
    activeS = dbActiveSessions.db.activeSessions.find({"token":token})
    username = None
    for i in activeS:
        username = i["username"]
    if username == None:
        return jsonify({"response":"you are not logged"}),404
    idAnn = int(idAnnouncement)
    isInfavourites = dbUsers.db.users.find({"username":username})
    favourites = []
    for i in isInfavourites:
        favourites = i["favourites"]
    if idAnn not in favourites:
        return jsonify({"response":"you do not have the announcement in favourites"}),400
    company = dbAnnouncements.db.announcements.find({"_id":idAnn})
    cmpa = None
    for i in company:
        cmpa = i["company"]
    loc = dbCompanies.db.companies.find({"companyName":cmpa})
    locat = None
    placeID = None
    for i in loc:
        locat = i["latLong"]
        placeID = i["placeID"]
    debugging("Latitude and longitude:")
    debugging(locat)
    return jsonify({"response":"successful","latLong":locat,"placeID":placeID}),200

@app.route('/getAnnouncementByID',methods=['POST'])
def geing():
    jsonR = request.get_json()
    idd = int(jsonR.get("announcementID"))
    token = jsonR.get("token")
    activeS = dbActiveSessions.db.activeSessions.find({"token":token})
    hasActiveSession = False
    for i in activeS:
        hasActiveSession = True
    if not hasActiveSession:
        return jsonify({"response":"you are not logged"}),404
    ann = dbAnnouncements.db.announcements.find({"_id":idd})
    announcement = []
    for i in ann:
        debugging(i)
        announcement.append(json.dumps({"idAnnouncement":idd,"description":i["description"],"companyName":i["company"], "type":i["type"]}))
        return jsonify({"response":announcement}),200
    return jsonify({"response":"unsuccessful"}),400


@app.route('/changePassword',methods=['POST'])
def channge():
    j = request.get_json()
    token = j.get("token")
    passw = j.get("oldPassword")
    newPassw = j.get("newPassword")
    #0 = usuario, diferente a 0 => empresa
    isCompany = int(j.get("isCompany"))
    ses = dbActiveSessions.db.activeSessions.find({"token":token})
    username = None
    for i in ses:
        username = i["username"]
    if username == None:
        return jsonify({"response":"you are not logged"}),400
    hashedPasswd = hashlib.sha256(passw.encode('utf-8')).hexdigest()
    hashedNewPasswd = hashlib.sha256(newPassw.encode('utf-8')).hexdigest()
    if isCompany > 0:
        us = dbCompanies.db.companies.find({"username":username})
        antiguaPass = None
        for i in us:
            antiguaPass = i["password"]
        if antiguaPass != hashedPasswd:
            return jsonify({"response":"the password you introduced is not correct"}),400
        else:
            dbCompanies.db.companies.update({"username":username},{"$set":{"password":hashedNewPasswd}})
            return jsonify({"response":"you have updated your password successfully"}),200
    else:
        us = dbUsers.db.users.find({"username":username})
        antiguaPass = None
        for i in us:
            antiguaPass = i["password"]
        if antiguaPass != hashedPasswd:
            return jsonify({"response":"the password you introduced is not correct"}),400
        else:
            dbUsers.db.users.update({"username":username},{"$set":{"password":hashedNewPasswd}})
            return jsonify({"response":"you have updated your password successfully"}),200
  




if __name__=="__main__":
    '''
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080, type=int, help='port to listen on')
    args = parser.parse_args()
    portUsed=args.port
    '''
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    app.run(host='10.6.40.102', port=8080, ssl_context=('cert.pem','key.pem')) #ssl_context='adhoc')

