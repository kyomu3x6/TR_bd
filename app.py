from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/baza'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)


conn = psycopg2.connect(database="baza",
                        host="localhost",
                        user="postgres",
                        password="admin",
                        port="5432")
cursor = conn.cursor()


roles = ['patient', 'nurse', 'doctor', 'superuser', 'HR', 'administrator']
current_role = 'superuser'


class Users(db.Model):
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Department(db.Model):
    __tablename__ = 'departments'
    
    id_department = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(255))
    fio_doctor = db.Column(db.String(255))

    # Relationships
    employees = db.relationship('Employee', backref='department', )
    diseases = db.relationship('Disease', backref='department', )
    patients = db.relationship('Patient', backref='department', )


class Disease(db.Model):
    __tablename__ = 'diseases'

    id_disease = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id_department'))
    name = db.Column(db.String(255))

    # Relationships
    medications = db.relationship('Medication', backref='disease', )
    patients = db.relationship('Patient', backref='disease')


class Editor(db.Model):
    __tablename__ = 'editors'

    id_editor = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(255))
    position = db.Column(db.String(255))
    phnumber = db.Column(db.String(255))

    # Relationships
    patients = db.relationship('Patient', backref='editor')


class Employee(db.Model):
    __tablename__ = 'employees'

    id_employee = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(255))
    position = db.Column(db.String(255))
    birthdate = db.Column(db.Date)
    phnumber = db.Column(db.String(255))
    email = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id_department'))


class Medication(db.Model):
    __tablename__ = 'medications'

    id_medication = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    release_form = db.Column(db.String(255))
    registry_form = db.Column(db.String(255))
    quantity = db.Column(db.Integer)
    expiration_date = db.Column(db.Date)
    price = db.Column(db.Numeric(10, 2))
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id_disease'))


class Patient(db.Model):
    __tablename__ = 'patients'

    id_patient = db.Column(db.Integer, primary_key=True)
    fio = db.Column(db.String(255))
    birthdate = db.Column(db.String(255))
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id_disease'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id_department'))
    editor_id = db.Column(db.Integer, db.ForeignKey('editors.id_editor'))

@app.route("/index")
@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if role not in roles:
            flash("Invalid role!", 'danger')
            return redirect(url_for('register'))

        
        password_hash = generate_password_hash(password)
        
        
        new_user = Users(username=username, password=password_hash, role=role)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful!', 'success')
        redirect(url_for('all_data'))

    return render_template('register.html')  # Ensure to add a field for role selection in your HTML


@app.route("/login", methods=["GET", "POST"])
def login():
    global current_role
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id_user
            session['role'] = user.role
            flash('Login successful!', 'success')
            current_role = user.role
            print(current_role)
            return redirect(url_for('all_data'))

        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route("/logout")
def logout():
    session.clear() 
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/no_rights', methods=['GET'])
def no_rights():
    return render_template('no_rights.html')

@app.route('/all_data', methods=['GET'])
def all_data():
    return render_template('superuser.html')

id
@app.route('/departments', methods=['GET', 'POST'])
def view_departments():
    """Patients and nurses can view information about doctors."""
    if 'role' in session and current_role in ['patient', 'nurse', 'superuser']:
        if request.method == 'POST':
            department_name = request.form['department_name']
            fio_doctor = request.form['fio_doctor']
            cursor.execute(f'INSERT INTO departments (department_name, fio_doctor) VALUES ({department_name}, {fio_doctor})')
            cursor.fetchall()
            return redirect(url_for('view_departments'))
        departments = Department.query.all()
        return render_template('departments.html', departments=departments)
    return redirect(url_for('no_rights'))

@app.route('/medications', methods=['GET', 'POST'])
def edit_medications():
    """Nurses can edit medication details."""
    if 'role' in session and current_role in ['nurse', 'superuser']:
        if request.method == 'POST':
            medication = Medication(
                id_medication=request.form['id'],
                name = request.form['name'],
                quantity = request.form['quantity'],
                expiration_date = request.form['expiration_date']
            )
            db.session.add(medication)
            db.session.commit()
            return redirect(url_for('all_data'))
        return render_template('medications.html', medication=medication)
    return redirect(url_for('no_rights'))

@app.route('/all_data', methods=['GET', 'POST', 'PUT', 'DELETE'])
def superuser_access():
    """Superuser has full access to all data."""
    return render_template('superuser.html')

@app.route('/employees', methods=['GET', 'POST'])
def manage_employees():
    
    """HR can add, delete, and modify employee information."""
    employees = Employee.query.all()
    if request.method == 'POST':
        if 'role' in session and current_role in ['hr', 'superuser']:
            new_employee = Employee(
                fio=request.form['fio'],
                position=request.form['position'],
                birthdate=request.form['birthdate'],
                phnumber=request.form['phnumber'],
                email=request.form['email'],
                department_id=request.form['department_id']
            )
            db.session.add(new_employee)
            db.session.commit()
            return redirect(url_for('manage_employees'))
        else:
            return redirect(url_for('no_rights'))
    if 'role' in session and current_role in ['hr', 'superuser', 'patient', 'nurse']:
        return render_template('employees.html', employees=employees)

@app.route('/patients', methods=['GET'])
def view_patients():
    """Doctors can view information about all patients."""
    if 'role' in session and current_role in ['administrator','doctor', 'superuser']:
        patients = Patient.query.all()
        if request.method == 'POST':
            new_patient = Employee(
                fio=request.form['fio'],
                birthdate=request.form['birthdate'],
                disease_id=request.form['disease_id'],
                department_id=request.form['department_id'],
            )
            db.session.add(new_patient)
            db.session.commit()
            return redirect(url_for('all_data'))
        return render_template('patients.html', patients=patients)
    return redirect(url_for('no_rights'))

@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
    """Administrators can add new patients."""
    print(current_role)
    if 'role' in session and current_role in ['administrator', 'superuser']:
        if request.method == 'POST':
            new_patient = Patient(
                fio=request.form['fio'],
                birthdate=request.form['birthdate'],
                disease_id=request.form['disease_id'],
                department_id=request.form['department_id'],
                editor_id=request.form['editor_id']
            )
            db.session.add(new_patient)
            db.session.commit()
            return redirect(url_for('view_patients'))
        return render_template('add_patient.html')
    return redirect(url_for('no_rights'))


@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
def edit_patient_personal_data(id):
    """Administrators can edit personal data of patients."""
    if 'role' in session and current_role in ['administrator', 'superuser']:
        patient = Patient.query.get_or_404(id)
        if request.method == 'POST':
            patient.fio = request.form['fio']
            patient.birthdate = request.form['birthdate']
            db.session.commit()
            return redirect(url_for('view_patients'))
        return render_template('edit_patient_personal_data.html', patient=patient)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)