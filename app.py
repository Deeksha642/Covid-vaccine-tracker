from flask import Flask,render_template,request,session,redirect,url_for
from flask_wtf import FlaskForm
from wtforms import (StringField,SelectField,SubmitField,IntegerField)
from wtforms import TextField
from wtforms import validators
from wtforms.validators import DataRequired,Email
import sqlite3 as sql
import os
from datetime import datetime
import requests
from flask_mail import Mail, Message

currentdirectory = os.path.dirname(os.path.abspath(__file__))
#__file__ -> app.py
#os.path.abspath(__file__) -> grabing absolute path for app.py
#o.apth.dirname ->grab directory name
#o/p look like C:\users\deeksha\pycharmProject\cvt\app.py

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'

#configuring flask-mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'dpbp2022@gmail.com'
app.config['MAIL_PASSWORD'] = 'Dpbpnie@2022'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


class InfoForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    email = TextField('Email',[validators.DataRequired("Please enter your email address"),validators.Email("Please enter your valid email address")])
    district = SelectField(u'District:',
                          choices = [('270', 'Bagalkot'), ('276', 'Bangalore Rural'),('265','Banglaore Urban'),('294','BBMP'),
                                     ('264','Belgaum'),('274','Bellary'),('272','Bidar'),('271','Chamarajanagar'),('273','Chikamagalur'),
                                     ('291','Chikkaballapur'),('268','Chitradurga'),('269','Dakshina Kannada'),('275','Davanagere'),
                                     ('278','Dharwad'),('280','Gadag'),('267','Gulbarga'),('289','Hassan'),('279','Haveri'),
                                     ('283','Kodagu'),('277','Kolar'),('282','Koppal'),('290','Mandya'),('266','Mysore'),
                                     ('284','Raichur'),('292','Ramanagara'),('287','Shimoga'),('288','Tumkur'),('286','Udupi'),
                                     ('281','Uttar Kannada'),('293','Vijayapura'),('285','Yadgir')])
    submit = SubmitField('Submit')
    age = IntegerField('Age', [DataRequired()])

@app.route('/',methods = ['GET','POST'])
def index():
    form = InfoForm()
    error=None
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['email'] = form.email.data
        session['dist'] = form.district.data
        session['age'] = form.age.data
        d = { 270:'Bagalkot',276:'Bangalore_Rural',265:'Banglaore Urban',294:'BBMP',264:'Belgaum',
        274:'Bellary',272: 'Bidar',271:'Chamarajanagar',273:'Chikamagalur',
         291:'Chikkaballapur',268:'Chitradurga',269:'Dakshina Kannada',275:'Davanagere',
         278:'Dharwad',280:'Gadag',267:'Gulbarga',289:'Hassan',279:'Haveri',
         283:'Kodagu',277:'Kolar',282:'Koppal',290:'Mandya',266:'Mysore',
         284:'Raichur',292:'Ramanagara',287:'Shimoga',288:'Tumkur',286:'Udupi',
         281:'Uttar Kannada',293:'Vijayapura',285:'Yadgir'}
        name = session['name']
        email = session['email']
        di = session['dist']
        m = d[int(di)]
        age = session['age']
        #district = request.args.get('district')
        try:
            with sql.connect(currentdirectory + "\coviddatabase.db") as con:
                cur=con.cursor()
                    #cur.execute("CREATE TABLE stud(name TEXT,addr TEXT,city TEXT,pin TEXT)")
                cur.execute("INSERT INTO Users(name,email,district,district_id,age) VALUES(?,?,?,?,?)",(name,email,m,di,age))
                con.commit()
            receiver = email
            msg = Message('Vaccine Notifier', sender='dpbp2022@gmail.com', recipients=[receiver])
            msg.body = 'Thank you for registering to our website we will notify the vaccination slots' \
                       'near you soon as and when it is available'
            mail.send(msg)
            return redirect(url_for("thankyou"))
        except sql.Error as e:
            if con:
                con.rollback()
            print(f"Error {e.args[0]}")
            error="Email Id already exists,Please try with different email id"
            return render_template("index.html", form=form, error=error)

    return render_template("index.html",form=form)


@app.route('/thankyou')
def thankyou():
    name = request.args.get('name')
    district = request.args.get('district')
    return render_template('thank_you.html', name=name,district=district )

@app.route('/list')
def list():
    con = sql.connect("coviddatabase.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM Users")
    rows = cur.fetchall()
    for row in rows:
        print(row[0],row[1],row[2],row[3],row[4])
        name = row[0]
        email = row[1]
        district = row[2]
        district_id = row[3]
        age = row[4]
        start_date = datetime.today().strftime("%d-%m-%Y")
        url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict"
        params = {"district_id": district_id, "date": start_date}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"}
        result = requests.get(url, params=params, headers=headers)
        s = "Dear {} ".format(name)
        s = s + "As requested by you, notifying you of some new vaccine slots centers around {} ".format(district)
        s = s + "that have available slots on CoWIN.Here is the list\n\n"
        flag=0
        if result.ok:
            response_json = result.json()
            if response_json["centers"]:
                flag = 1
                for center in response_json["centers"]:
                    for session in center["sessions"]:
                        if age >= 45:
                            if (session["min_age_limit"] == 45 and session["available_capacity"] > 0):
                                s = s + 'Pincode: {}\n'.format(center["pincode"])
                                s = s + "Available on: {}\n".format(start_date)
                                s = s + "\tHospital: {}\n".format(center["name"])
                                s = s + "\tAddress: {}\n".format(center["address"])
                                s = s + "\tBlock_name: {}\n".format(center["block_name"])
                                s = s + "\tPrice: {}\n".format(center["fee_type"])
                                s = s + "\tDose1 Capacity : {}\n".format(session["available_capacity_dose1"])
                                s = s + "\tDose2 Capacity : {}\n".format(session["available_capacity_dose2"])
                                if (session["vaccine"] != ''):
                                    s = s + "\tVaccine type: {}\n\n".format(session["vaccine"])

                        elif age >= 18:
                            if (session["min_age_limit"] == 18 and session["available_capacity"] > 0):
                                s = s + 'Pincode: {}\n'.format(center["pincode"])
                                s = s + "Available on: {}\n".format(start_date)
                                s = s + "\tHospital: {}\n".format(center["name"])
                                s = s + "\tAddress: {}\n".format(center["address"])
                                s = s + "\tBlock_name: {}\n".format(center["block_name"])
                                s = s + "\tPrice: {}\n".format(center["fee_type"])
                                s = s + "\tDose1 Capacity : {}\n".format(session["available_capacity_dose1"])
                                s = s + "\tDose2 Capacity : {}\n".format(session["available_capacity_dose2"])
                                if (session["vaccine"] != ''):
                                    s = s + "\tVaccine type: {}\n\n".format(session["vaccine"])
            s = s + "\n\nBook your slots at the official CoWIN portal:https://selfregistration.cowin.gov.in/"
            # print(s)
            if flag == 1:
                receiver = email
                msg = Message('Vaccine Notifier', sender='dpbp2022@gmail.com', recipients=[receiver])
                msg.body = s
                mail.send(msg)
    return render_template("notify.html")



if __name__ == '__main__':
    app.run(debug=True)
