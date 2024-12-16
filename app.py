from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/PDE_11_TR'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)


conn = psycopg2.connect(database="PDE_11_TR",
                        host="localhost",
                        user="postgres",
                        password="123",
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
    if 'role' in session and current_role in ['nurse', 'superuser']:
        if request.method == 'POST':
            action = request.form['action']
            department_name = request.form['department_name'] if request.form['department_name'] != '' else None
            fio_doctor = request.form['fio_doctor'] if request.form['fio_doctor'] != '' else None
            id_department = request.form['id_department']
            # Используем параметризованный запрос
            if action == 'insert':
                cursor.execute(
                    'INSERT INTO departments (department_name, fio_doctor) VALUES (%s, %s)', 
                    (department_name, fio_doctor)
                )
            elif action == 'update':
                cursor.execute(
                    'UPDATE departments SET department_name = %s, fio_doctor = %s WHERE id_department = %s;', 
                    (department_name, fio_doctor, id_department)
                )
            else:
                cursor.execute(
                    f'DELETE FROM departments WHERE id_department = {id_department};', 
                    #(id_department)
                )
            # Фиксируем изменения в базе данных
            conn.commit()
            return redirect(url_for('view_departments'))
        departments = Department.query.all()
        return render_template('departments.html', departments=departments)
    return redirect(url_for('no_rights'))

@app.route('/medications', methods=['GET', 'POST'])
def edit_medications():
    """Nurses can edit medication details."""
    if 'role' in session and current_role in ['nurse', 'superuser']:
        if request.method == 'POST':
            action = request.form['action']
            name=request.form['name'] if request.form['name'] != '' else None,
            quantity=request.form['quantity'] if request.form['quantity'] != '' else None,
            expiration_date=request.form['expiration_date'] if request.form['expiration_date'] != '' else None,
            id_medication=request.form['id_medication'] if request.form['id_medication'] != '' else None
            # Используем параметризованный запрос
            if action == 'insert':
                cursor.execute(
                    'INSERT INTO medications (name, quantity, expiration_date) VALUES (%s, %s, %s)', 
                    (name, quantity, expiration_date)
                )
            elif action == 'update':
                cursor.execute(
                    'UPDATE medications SET name = %s, quantity = %s, expiration_date = %s WHERE id_medication = %s;', 
                    (name, quantity, expiration_date, id_medication)
                )
            else:
                cursor.execute(
                    f'DELETE FROM medications WHERE id_medication = {id_medication};', 
                    #(id_department)
                )
            conn.commit()
            # # Создаем новый объект медикамента
            # medication = Medication(
            #     name=request.form['name'],
            #     quantity=request.form['quantity'],
            #     expiration_date=request.form['expiration_date']
            # )
            # db.session.add(medication)
            # db.session.commit()
            return redirect(url_for('edit_medications'))
        
        # Получаем все записи медикаментов из базы данных
        medications = Medication.query.all()
        return render_template('medications.html', medications=medications)  # Передаем список объектов
    
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
            # new_employee = Employee(
            #     fio=request.form['fio'],
            #     position=request.form['position'],
            #     birthdate=request.form['birthdate'],
            #     phnumber=request.form['phnumber'],
            #     email=request.form['email'],
            #     department_id=request.form['department_id']
            # )
            # db.session.add(new_employee)
            # db.session.commit()
            action = request.form['action']
            fio=request.form['fio'] if request.form['fio'] != '' else None,
            position=request.form['position'] if request.form['position'] != '' else None,
            birthdate=request.form['birthdate'] if request.form['birthdate'] != '' else None,
            phnumber=request.form['phnumber'] if request.form['phnumber'] != '' else None,
            email=request.form['email'] if request.form['email'] != '' else None,
            department_id=request.form['department_id'] if request.form['department_id'] != '' else None,
            id_employee=request.form['id_employee']
            if action == 'insert':
                cursor.execute('INSERT INTO employees (fio, position, birthdate, phnumber, email, department_id) VALUES (%s, %s, %s, %s, %s, %s)', (
                    fio, position, birthdate, phnumber, email, department_id
                ))
            elif action == 'update':
                cursor.execute(
                    'UPDATE employees SET fio = %s, position = %s, birthdate = %s, phnumber = %s, email = %s, department_id = %s WHERE id_employee = %s;', 
                    (fio, position, birthdate, phnumber, email, department_id, id_employee)
                )
            else:
                cursor.execute(
                    f'DELETE FROM medications WHERE id_medication = {id_medication};', 
                    #(id_department)
                )
            conn.commit()
            return redirect(url_for('manage_employees'))
        else:
            return redirect(url_for('no_rights'))
    if 'role' in session and current_role in ['hr', 'superuser', 'patient', 'nurse']:
        return render_template('employees.html', employees=employees)

@app.route('/patients', methods=['GET', 'POST'])
def view_patients():
    """Doctors can view information about all patients."""
    if 'role' in session and current_role in ['administrator','doctor', 'superuser']:
        patients = Patient.query.all()
        if request.method == 'POST':
            action=request.form['action']
            if action == 'insert':    
                cursor.execute("""
                        CALL ins_patient(%s, %s, %s, %s);
                    """, (
                        request.form['fio'] if request.form['fio'] != '' else None,
                        request.form['birthdate'] if request.form['birthdate'] != '' else None,
                        request.form['disease_id'] if request.form['disease_id'] != '' else None,
                        request.form['department_id'] if request.form['department_id'] != '' else None
                    ))
            elif action == 'update':    
                cursor.execute("""
                        CALL upd_patient(%s, %s, %s, %s, %s);
                    """, (
                        request.form['id_patient'],
                        request.form['fio'],
                        request.form['birthdate'] if request.form['birthdate'] != '' else None,
                        request.form['disease_id'] if request.form['disease_id'] != '' else None,
                        request.form['department_id'] if request.form['department_id'] != '' else None
                    ))
            if action == 'delete':    
                cursor.execute("""
                        CALL del_patient(%s);
                    """, (
                        request.form['id_patient']
                    ))
            conn.commit()
            return redirect(url_for('view_patients'))
        return render_template('patients.html', patients=patients)
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