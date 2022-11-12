from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_cors import CORS
import requests, json, os
import ibm_db
import re

app = Flask(__name__)

app.secret_key = 'a'


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=6667d8e9-9d4d-4ccb-ba32-21da3bb5aafc.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=30376;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=qfn70649;PWD=aXek5nfjbJy0IGQV",'','')



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    global userid
    msg=''

    if request.method =='POST':
        username = request.form['username']
        password =request.form['password']
        sql ="SELECT * FROM users WHERE username =? AND password=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print (account)
        if account:
            session['loggedin']=True
            session['id'] = account ['USERNAME']
            userid = account['USERNAME']
            session['username'] = account['USERNAME']
            msg = 'logged in successfully !'

            return render_template('submission.html',msg = msg)

        else:
            msg ='Incorrect username / password !'
    return render_template('login.html',msg=msg)

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        sql = "SELECT * FROM users WHERE username = ?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            msg ='Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+',email):
            msg ='Invaild email address !'
        elif not re.match(r'[A-Za-z0-9]+',username):
            msg = 'Name must contain only characters and numbers!'
        else:
            insert_sql = "INSERT INTO users VALUES (?,?,?)"
            prep_stmt= ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1 , username)
            ibm_db.bind_param(prep_stmt, 2, email)
            ibm_db.bind_param(prep_stmt, 3, password)
            ibm_db.execute(prep_stmt)
            msg = ' you have successfully registered !'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)
@app.route('/submission')
def submission():

    return render_template('submission.html')

@app.route('/pythonlogin/submission/display', methods = ["POST", "GET"])
def display():
    if request.method == "POST":
        image = request.files["food"] 
        authenticator = IAMAuthenticator('2A6BucKErMHbNpKGwdyGMBTsAZYxRYmm8Rxr0chzTvfm')
        visual_recognition = VisualRecognitionV3(
        version='2018-03-19',
        authenticator=authenticator)
        visual_recognition.set_service_url('https://api.us-south.visual-recognition.watson.cloud.ibm.com/instances/80c78105-880f-4bb7-b79c-93764795ee73') 
        classes = visual_recognition.classify(images_filename=image.filename, 
                                              images_file=image ,classifier_ids='food').get_result() 
        data=json.loads(json.dumps(classes,indent=4))

        foodName=data["images"][0]['classifiers'][0]["classes"][0]["class"]
        nutrients = {}
        USDAapiKey = '9f8yGs19GGo5ExPpBj7fqjKOFlXXxkJdMyJKXwG3'
        response = requests.get('https://api.nal.usda.gov/fdc/v1/foods/search?api_key={}&query={}&requireAllWords={}'.format(USDAapiKey, foodName, True))

        data = json.loads(response.text)
        concepts = data['foods'][0]['foodNutrients']
        arr = ["Sugars","Energy", "Vitamin A","Vitamin D","Vitamin B", "Vitamin C", "Protein","Fiber","Iron","Magnesium",
               "Phosphorus","Cholestrol","Carbohydrate","Total lipid (fat)", "Sodium", "Calcium",]
        for x in concepts:
            if x['nutrientName'].split(',')[0] in arr:
                if(x['nutrientName'].split(',')[0]=="Total lipid (fat)"):
                    nutrients['Fat'] = str(x['value'])+" " + x['unitName']
                else:    
                    nutrients[x['nutrientName'].split(',')[0]] = str(x['value'])+" " +x['unitName']
                    
        return render_template('display.html', x = foodName, data = nutrients, account = session['username'])
    else:
        return render_template('submission.html')



if __name__=='__main__':
    app.run(host='0.0.0.0',debug = True, port = 8080)