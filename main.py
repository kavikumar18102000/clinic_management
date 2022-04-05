
import email
from enum import unique
from telnetlib import DO
from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_manager, LoginManager, login_user, logout_user
from flask_login import login_required, current_user
from flask_login import UserMixin
from flask_mail import Mail
import json
from datetime import datetime

with open('config.json', 'r') as c:
    params = json.load(c)["params"]


local_server = True

app = Flask(__name__, template_folder='template')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/clinic'
# app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:kavi@localhost/clinic'
app.config['SECRET_KEY'] = 'arya'
db = SQLAlchemy(app)


# SMTP mail server settings
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)


# this is for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return  User.query.get(int(user_id)) or Doctor.query.get(int(user_id)) 


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, unique=True)
    u_name = db.Column(db.String(30))
    u_email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))


class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(50))
    d_name = db.Column(db.String(30))
    c_email = db.Column(db.String(30))
    c_address = db.Column(db.String(30))
    c_phone = db.Column(db.String(12), unique=True)
    open_time = db.Column(db.Time(6))
    close_time = db.Column(db.Time(6))


class Patient(db.Model):
    p_id = db.Column(db.Integer, primary_key=True)
    b_id = db.Column(db.Integer)
    p_name = db.Column(db.String(50))
    p_address = db.Column(db.String(30))
    p_phone = db.Column(db.String(12))
    disease = db.Column(db.String(50))


class Bookings(db.Model):
    b_id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(50))
    c_address = db.Column(db.String(30))
    d_name = db.Column(db.String(20))
    c_email = db.Column(db.String(30))
    p_email = db.Column(db.String(30))
    p_name = db.Column(db.String(30))
    p_gender = db.Column(db.String(10))
    slot = db.Column(db.String(10))
    start_time = db.Column(db.Time(6))
    end_time = db.Column(db.Time(6))
    date = db.Column(db.String(10))
    disease = db.Column(db.String(50))
    p_phone = db.Column(db.String(12))


class Doctor(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    did = db.Column(db.Integer,unique=True)
    d_name = db.Column(db.String(30), unique=True)
    d_email = db.Column(db.String(50), unique=True)
    d_phone = db.Column(db.String(12),unique=True)
    d_password = db.Column(db.String(1000))


class Report(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    b_id = db.Column(db.Integer)
    p_name = db.Column(db.String(50))
    p_age = db.Column(db.Integer)
    d_name = db.Column(db.String(20))
    clinic_name = db.Column(db.String(50))
    p_email = db.Column(db.String(30))
    date = db.Column(db.String(10))
    p_phone = db.Column(db.String(12))
    p_disease = db.Column(db.String(50))
    medicine_type = db.Column(db.String(1000))
    nex_app = db.Column(db.String(10))


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/userpage')
@login_required
def userpage():
    return render_template('userpage.html')


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        search = request.form.get('search')
        # res=db.engine.execute('select * from clinic where address=%s',[search])
        res = Clinic.query.filter_by(c_address=search).all()
        if res:
            return render_template('search.html', datas=res)
        else:
            flash("No clinics detected in the entered location......", "danger")

    return render_template('home.html')


@app.route('/usersearch', methods=['GET', 'POST'])
@login_required
def usersearch():
    if request.method == 'POST':
        usersearch = request.form.get('usersearch')
        res = Clinic.query.filter_by(c_address=usersearch).all()
        if res:
            flash("clincis detected,please scroll down to book","success")
            return render_template('book.html', datas=res)
    flash("NO clinics detected....","info")
    return redirect('/book')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        userid = request.form.get('userid')
        username = request.form.get('username')
        useremail = request.form.get('useremail')
        password = request.form.get('userpassword')
        user = User.query.filter_by(u_email=useremail).first()
        u_id = User.query.filter_by(uid=userid).first()
        if user or u_id:
            flash("Email or User ID already exists", "warning")
        uspass = generate_password_hash(password)
        new_user = db.engine.execute(
            f"INSERT INTO `user` (`uid`,`u_name`,`u_email`,`password`) VALUES ('{userid}','{username}','{useremail}','{uspass}')")
        flash("signed up successfully", "success")
        return render_template('login.html')
    return render_template('signup.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        lemail = request.form.get('lemail')
        lpass = request.form.get('lpass')
        user = User.query.filter_by(u_email=lemail).first()
        if user and check_password_hash(user.password, lpass):
            login_user(user)
            return render_template('userpage.html', username=current_user.u_name)
        else:
            flash("invalid email or password", "danger")
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged Out Successfully......", "success")
    return redirect(url_for('login'))


@app.route('/book', methods=['POST', 'GET'])
@login_required
def book():
    if request.method == 'POST':
        cname = request.form.get('c_name')
        caddress = request.form.get('c_address')
        doctor = request.form.get('doctor')
        c_email = request.form.get('doctor_email')
        pemail = request.form.get('pemail')
        pname = request.form.get('pname')
        p_address = request.form.get('p_address')
        pgender = request.form.get('pgender')
        slot = request.form.get('slot')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        date = request.form.get('date')
        disease = request.form.get('disease')
        pphone = request.form.get('pphone')
        d_email = Bookings.query.filter_by(c_email=c_email).first()
        if d_email:
            dates = Bookings.query.filter_by(date=date).all()
            if dates:
                st_time = Bookings.query.filter_by(
                    start_time=start_time).first()
                if st_time:
                    flash(
                        "time slot already taken...please choose different time slot", "danger")
                else:
                    db.engine.execute('INSERT INTO bookings(c_name,c_address,d_name,c_email,p_name,p_email,p_gender,slot,start_time,end_time,date,disease,p_phone) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                      [cname, caddress, doctor, c_email, pname, pemail, pgender, slot, start_time, end_time, date, disease, pphone])
                    db.engine.execute('INSERT INTO patient(p_name,p_email,p_address,p_phone,disease) VALUES(%s,%s,%s,%s,%s)', [
                                      pname, pemail, p_address, pphone, disease])
                    flash("appointment booked successfully", "success")
                    return redirect('/view_appointment')
            else:
                db.engine.execute('INSERT INTO bookings(c_name,c_address,d_name,c_email,p_name,p_email,p_gender,slot,start_time,end_time,date,disease,p_phone) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                      [cname, caddress, doctor, c_email, pname, pemail, pgender, slot, start_time, end_time, date, disease, pphone])
                db.engine.execute('INSERT INTO patient(p_name,p_email,p_address,p_phone,disease) VALUES(%s,%s,%s,%s,%s)', [
                                      pname, pemail, p_address, pphone, disease])
                flash("appointment booked successfully", "ssuccess")
                return redirect('/view_appointment')
        else:
            db.engine.execute('INSERT INTO bookings(c_name,c_address,d_name,c_email,p_name,p_email,p_gender,slot,start_time,end_time,date,disease,p_phone) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                              [cname, caddress, doctor, c_email, pname, pemail, pgender, slot, start_time, end_time, date, disease, pphone])
            db.engine.execute('INSERT INTO patient(p_name,p_email,p_address,p_phone,disease) VALUES(%s,%s,%s,%s,%s)', [
                              pname, pemail, p_address, pphone, disease])
            flash("appointment booked successfully", "success")
            return redirect('/view_appointment')
            # mail.send_message('SMART CLINIC',sender=params['gmail-user'],
            # recipients=[pemail],body="yor booking is confirmed,thanks fo choosing us.....")
            # res=db.engine.execute('SELECT d_email from doctors WHERE d_name=%s',[doctor])
            # mail.send_message('SMART CLINIC',sender=params['gmail-user'],
            # recipients=[doctor_email],body=" An appointment in your clinic is booked by..." +""+current_user.username)
    return render_template('book.html')


@app.route('/view_appointment', methods=['POST', 'GET'])
@login_required
def view():
    pemail = current_user.u_email
    res = Bookings.query.filter_by(p_email=pemail).all()
    if res:
        return render_template('view_appointment.html', datas=res)
    flash("No appointments booked,please book","info")
    return redirect('/book')


@app.route("/cancel_appointment/<string:b_id>", methods=['POST', 'GET'])
@login_required
def delete(b_id):
    db.engine.execute(f"DELETE FROM `bookings` WHERE `b_id`={b_id}")
    # mail.send_message('SMART CLINIC',sender=params['gmail-user'],
    # recipients=[current_user.email],body="yor booking has been cancelled,thanks fo choosing us.....")
    # flash("Appointment Cancelled Successful","danger")
    return redirect('/view_appointment')


@app.route('/doctor_login', methods=['POST', 'GET'])
def doctor_login():
    if request.method == 'POST':
        d_email = request.form.get('d_email')
        d_password = request.form.get('d_password')
        doc = Doctor.query.filter_by(d_email=d_email).first()
        if doc and check_password_hash(doc.d_password, d_password):
            login_user(doc)
            flash("logged in successfully", "info")
            return render_template('doctor.html', username=current_user.d_name)
        else:
            flash("invalid email or password...", "danger")
            return redirect(url_for('doctor_login'))
        print(doc)
    return render_template('doctor_login.html')


@app.route('/doctor')
@login_required
def doctor():
    username = current_user.d_name
    return render_template('doctor.html', username=username)


@app.route('/d_logout')
def doctor_logout():
    logout_user()
    flash("logged out successfully...", "success")
    return redirect(url_for('doctor_login'))


@app.route('/admin_login', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        u_pass = request.form.get('u_pass')
        if(u_name == params['user'] and u_pass == params['password']):
            session['user'] = u_name
            flash("login success", "info")
            return redirect('/admin')
        else:
            flash("Invalid Credentials", "danger")
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route("/logout_admin")
def logoutadmin():
    session.pop('user')
    flash("You are logout admin", "primary")

    return redirect('/admin_login')


@app.route('/d_view')
@login_required
def treatment():
    em=current_user.d_email
    res=db.engine.execute('SELECT * from bookings WHERE date=%s AND c_email=%s',[datetime.date(datetime.now()),em])
    if res:
        return render_template('d_view.html', datas=res)
    flash("NO appointments today....","info")
    return render_template('d_view.html')

@app.route('/date_view',methods=['POST','GET'])
def date_view():
    if request.method == 'POST':
        date=request.form.get('date')
        res=Bookings.query.filter_by(date=date).all()
        if res:
            return render_template('d_view.html',datas=res)
        else:
            flash("NO appoinments ","Danger")
            return redirect('/d_view')
    return redirect('/d_view')

@app.route('/report/<string:b_id>', methods=['POST', 'GET'])
def report(b_id):
    datas=Bookings.query.filter_by(b_id=b_id).first()
    if request.method == 'POST':
        b_id = request.form.get('b_id')
        p_name = request.form.get('p_name')
        p_age = request.form.get('p_age')
        d_name = request.form.get('doctor')
        c_name = request.form.get('clinic')
        p_email = request.form.get('p_email')
        date = request.form.get('date')
        disease = request.form.get('disease')
        p_phone = request.form.get('p_phone')
        m_type = request.form.get('m_type')
        n_app = request.form.get('n_app')
        rep=Report.query.filter_by(b_id=b_id).first()
        if rep:
            flash("Report already entered for this person","warning")
            return redirect('/d_view')
        db.engine.execute('INSERT INTO report(b_id,p_name,p_age,d_name,clinic_name,p_email,date,p_disease,p_phone,medicine_type,nex_app) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        [b_id,p_name,p_age,d_name,c_name,p_email,date,disease,p_phone,m_type,n_app])
        flash("Report entered successfully","success")
        return redirect('/d_view')
    return render_template('report.html',data=datas)

@app.route('/remove/<string:b_id>')
def remove(b_id):
    db.engine.execute('DELETE from report WHERE b_id=%s',[b_id])
    flash("Report removed successfully","info")
    return redirect('/view_report')


@app.route('/add_doc', methods=['POST', 'GET'])
def add_doc():
    if('user' in session and session['user'] == params['user']):
        if request.method == 'POST':
            did = request.form.get('did')
            d_name = request.form.get('d_name')
            d_email = request.form.get('d_email')
            d_phone = request.form.get('d_phone')
            d_pass = request.form.get('d_pass')
            print(did)
            doc_em = Doctor.query.filter_by(d_email=d_email).first()
            doc_id = Doctor.query.filter_by(did=did).first()
            if doc_em or doc_id:
                flash("Email or Doctor ID already exists", "warning")
                return render_template('admin.html')
            d_pas = generate_password_hash(d_pass)
            new_doc = db.engine.execute('INSERT INTO doctor(did,d_name,d_email,d_phone,d_password) VALUES(%s,%s,%s,%s,%s)', [
                                        did, d_name, d_email,d_phone, d_pas])
            # mail.send_message('SMART CLINIC',sender=params['gmail-user'],recipients=[email],body=f"Thanks for choosing us\nYour Login Credentials Are:\n Email Address: {d_email}\nPassword: {d_pass}\n\n\n\n Do not share your password\n\n\nThank You..." )
            flash("Added Doctor Successfully", "success")
            return render_template('admin.html')
    return render_template('admin_login.html')


@app.route('/d_dashboard')
def d_dash():
    res = db.engine.execute(
        'SELECT * from clinic WHERE c_email=%s', [current_user.d_email])
    return render_template('d_dashboard.html', data=res)


@app.route('/c_register', methods=['POST', 'GET'])
def reg():
    if request.method == 'POST':
        c_name = request.form.get('c_name')
        c_address = request.form.get('c_address')
        c_doc = request.form.get('doctor')
        c_email = request.form.get('c_email')
        c_phone = request.form.get('c_phone')
        o_time = request.form.get('o_time')
        c_time = request.form.get('c_time')
        d_add = Clinic.query.filter_by(c_address=c_address).first()
        if d_add:
            d_cli = Clinic.query.filter_by(c_name=c_name).first()
            if d_cli:
                flash(
                    "A clinic already exists in the location,please choose different name", "warning")
                return redirect('c_register')
            else:
                db.engine.execute('INSERT INTO clinic(c_name,d_name,c_email,c_address,c_phone,open_time,close_time) VALUES(%s,%s,%s,%s,%s,%s,%s)', [
                                  c_name, c_doc, c_email, c_address, c_phone, o_time, c_time])
                flash("Clinic registered successfully")
                return redirect('d_dashboard')
        db.engine.execute('INSERT INTO clinic(c_name,d_name,c_email,c_address,c_phone,open_time,close_time) VALUES(%s,%s,%s,%s,%s,%s,%s)', [
                          c_name, c_doc, c_email, c_address, c_phone, o_time, c_time])
        flash("Clinic registered successfully")
        return redirect('d_dashboard')

    return render_template('register.html')


@app.route('/forgot_pass', methods=['POST', 'GET'])
def forgot():
    if request.method == 'POST':
        d_email = request.form.get('d_email')
        d_password = request.form.get('d_password')
        demail = Doctor.query.filter_by(d_email=d_email).first()
        if demail:
            d_pas = generate_password_hash(d_password)
            db.engine.execute(
                'UPDATE doctor SET d_password=%s WHERE d_email=%s', [d_pas, d_email])
            flash("Updated password successfully,please login...", "success")
            return redirect('doctor_login')
        else:
            flash("No email found..", "warning")
            return render_template('d_forgot.html')
    return render_template('d_forgot.html')


@app.route('/u_forgot', methods=['POST', 'GET'])
def u_forgot():
    if request.method == 'POST':
        u_email = request.form.get('u_email')
        u_pass = request.form.get('u_pass')
        uemail = User.query.filter_by(email=u_email).first()
        if uemail:
            u_pas = generate_password_hash(u_pass)
            db.engine.execute(
                'UPDATE user SET password=%s WHERE email=%s', [u_pas, u_email])
            flash("Updated password successfully,please login...", "success")
            return redirect('login')
        else:
            flash("No email found..", "warning")
            return render_template('u_forgot.html')
    return render_template('u_forgot.html')

@app.route('/view_report')
def view_report():
    res=Report.query.filter_by(p_email=current_user.u_email).all()
    if res:
        return render_template('view_report.html',datas=res)
    flash("No reports to show","primary")
    return redirect('/userpage')

@app.route('/a_view',methods=['POST','GET'])
def a_view():
    if request.method == 'POST':
        date = request.form.get('date')
        res=Bookings.query.filter_by(date=date).all()
        if res:
            return render_template('a_view.html',datas=res)
    flash("NO appointment available...","dark")
    return redirect('/admin')

@app.route('/a_remove/<string:date>')
def a_remove(date):
    db.engine.execute('DELETE from bookings WHERE date=%s',[date])
    flash("Removed appoinment successfully......","dark")
    return redirect('/admin')


if __name__ == '__main__':
    app.run(debug=True)
