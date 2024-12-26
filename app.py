from flask import Flask, render_template, request, jsonify, session, redirect, g, url_for
import csv
import sqlite3
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'sdfguvh6678u8978'

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'farmer_request')  # Adjust the path if needed
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = 'soil_fertility.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = get_db()
    if db is not None:
        db.close()

@app.route('/')
@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/farmer_register', methods=['GET', 'POST'])
def farmer_register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        land_area = request.form['land_area']
        crop_type = request.form['crop_type']
        soil_type = request.form['soil_type']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO FarmerUsers (name, phone, email, land_area, crop_type, soil_type, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (name, phone, email, land_area, crop_type, soil_type, password))
            db.commit()
        except sqlite3.IntegrityError:
            message =  'Username already exists'
            return render_template('farmer_login.html', message=message)
        
        message =  'Account created successfully'
        
        return render_template('farmer_login.html', message=message)

    return render_template('farmer_register.html')

@app.route('/university_register', methods=['GET', 'POST'])
def university_register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        university = request.form['university']
        department = request.form['department']
        expertise = request.form['expertise']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO UniversityUsers (name, phone, email, university, department, expertise, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (name, phone, email, university, department, expertise, password))
            db.commit()
        except sqlite3.IntegrityError:
            message =  'Username already exists'
            return render_template('university_login.html', message=message)
        
        message =  'Account created successfully'
        
        return render_template('university_login.html', message=message)

    return render_template('university_register.html')

@app.route('/farmer_login', methods=['GET', 'POST'])
def farmer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM FarmerUsers WHERE email = ? AND password = ?", (email, password))
        email = cursor.fetchone()

        if email:
            # Set session variables to indicate user is logged in
            session['logged_in'] = True
            session['email'] = email
            return redirect('/farmer_home')
        else:
            message =  'Invalid email or password'
            return render_template('farmer_login.html', message=message)

    return render_template('farmer_login.html')

@app.route('/university_login', methods=['GET', 'POST'])
def university_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM UniversityUsers WHERE email = ? AND password = ?", (email, password))
        email = cursor.fetchone()

        if email:
            # Set session variables to indicate user is logged in
            session['logged_in'] = True
            session['email'] = email
            return redirect('/university_home')
        else:
            message =  'Invalid email or password'
            return render_template('university_login.html', message=message)

    return render_template('university_login.html')

@app.route('/farmer_home')
def farmer_home():
    return render_template('farmer_home.html')

@app.route('/university_home')
def university_home():
    return render_template('university_home.html')


@app.route('/view_request', methods=['GET', 'POST'])
def view_request():
    db = get_db()
    cursor = db.cursor()

    # Fetching all farmer requests from the database
    cursor.execute('SELECT * FROM farmer_requests')
    requests = cursor.fetchall()

    # Handling status update and admin comment assignment (if POST method is used)
    if request.method == 'POST':
        request_id = request.form['request_id']
        new_status = request.form['status']
        university_comment = request.form['university_comment']
        assigned_person = request.form['assigned_person']

        # Printing for debugging
        print(f"Request ID: {request_id}")
        print(f"New Status: {new_status}")
        print(f"University Comment: {university_comment}")
        print(f"Assigned Person: {assigned_person}")

        # Update the request with the new status, comment, and assigned person
        cursor.execute(''' 
            UPDATE farmer_requests 
            SET status = ?, university_comment = ?, assigned_person = ? 
            WHERE id = ?
        ''', (new_status, university_comment, assigned_person, request_id))

        db.commit()

        # Refreshing the page after the status update
        return redirect('/view_request')

    # Rendering the page with the fetched requests
    return render_template('view_request.html', requests=requests)





# Route for handling the form submission
@app.route('/farmer_request', methods=['GET', 'POST'])
def farmer_request():
    if request.method == 'POST':
        # Fetching form data
        name = request.form['name']
        crop = request.form['crop']
        soil_type = request.form['soil']
        email = request.form['email']
        problem = request.form['problem']
        status = "pending"
        farmer_comment = ""
        university_comment = ""
        assigned_person = ""

        # Fetching the uploaded image file
        soil_image = request.files['photo']

        if soil_image:
            safe_email = email.replace('@', '_').replace('.', '_')  # sanitize email to create valid filenames
            image_filename = f"{safe_email}_{soil_image.filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

            soil_image.save(file_path)

        soil_image_data = soil_image.read()  # Read the image as binary data

        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
            INSERT INTO farmer_requests (name, crop, soil_type, email, soil_image, problem, status, university_comment, assigned_person)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, crop, soil_type, email, soil_image_data, problem, status, university_comment, assigned_person))

        db.commit()

        message =  'Request has sent successfully. Our team will contact you shortly.'
        return render_template('farmer_request.html', message=message)

    return render_template('farmer_request.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
