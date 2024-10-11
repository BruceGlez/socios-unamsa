# app.py

from flask import Flask, render_template, url_for, flash, redirect, request, Response
from config import Config
from models import db, login_manager, User, Socio, Document
from forms import RegistrationForm, LoginForm, SocioForm, UploadForm, UpdateSocioForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user, login_required
import os
import uuid
import csv
from io import StringIO
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper functions
def get_required_docs(estado_marital):
    docs = [
        'Credencial para votar',
        'Acta de Nacimiento',
        'Constancia de Situación Fiscal',
        'Comprobante de Domicilio'
    ]
    if estado_marital == 'casado':
        docs += [
            'Credencial para votar (Cónyuge)',
            'Acta de Nacimiento (Cónyuge)',
            'Acta de Matrimonio'
        ]
    return docs

def get_optional_docs():
    return ['Comprobante de Domicilio Adicional (Opcional)']

# Routes
@app.route('/')
@app.route('/inicio')
def home():
    return render_template('home.html')

@app.route('/registro', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        with app.app_context():
            db.session.add(user)
            db.session.commit()
        flash('¡Cuenta creada! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/iniciar_sesion', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        with app.app_context():
            user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Inicio de sesión fallido. Verifica tu correo y contraseña.', 'danger')
    return render_template('login.html', form=form)

@app.route('/cerrar_sesion')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    with app.app_context():
        socios = Socio.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', socios=socios)

@app.route('/registrar_socio', methods=['GET', 'POST'])
@login_required
def registrar_socio():
    form = SocioForm()
    if form.validate_on_submit():
        estado_marital = form.estado_marital.data
        socio = Socio(
            nombre=form.nombre.data,
            apellido_paterno=form.apellido_paterno.data,
            apellido_materno=form.apellido_materno.data,
            rfc=form.rfc.data,
            curp=form.curp.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            direccion=form.direccion.data,
            email=form.email.data,
            telefono_fijo=form.telefono_fijo.data,
            telefono_celular=form.telefono_celular.data,
            estado_marital=estado_marital,
            user_id=current_user.id
        )
        if estado_marital == 'casado':
            socio.nombre_conyuge = form.nombre_conyuge.data
            socio.apellido_paterno_conyuge = form.apellido_paterno_conyuge.data
            socio.apellido_materno_conyuge = form.apellido_materno_conyuge.data
        try:
            with app.app_context():
                db.session.add(socio)
                db.session.commit()
            flash('¡Socio registrado exitosamente!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Ocurrió un error al registrar el socio. Por favor, inténtalo de nuevo.', 'danger')
            print(f"Error: {e}")
    return render_template('registrar_socio.html', form=form)

@app.route('/socio/<int:socio_id>')
@login_required
def ver_socio(socio_id):
    with app.app_context():
        socio = Socio.query.get_or_404(socio_id)
        if socio.user_id != current_user.id:
            flash('No tienes permiso para ver este socio.', 'danger')
            return redirect(url_for('dashboard'))
        documentos = Document.query.filter_by(socio_id=socio_id).all()
    return render_template('ver_socio.html', socio=socio, documentos=documentos)

@app.route('/subir', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    with app.app_context():
        socios = Socio.query.filter_by(user_id=current_user.id).all()
    if not socios:
        flash('No hay socios registrados. Por favor, registra un socio primero.', 'warning')
        return redirect(url_for('registrar_socio'))
    form.socio.choices = [(s.id, f"{s.nombre} {s.apellido_paterno}") for s in socios]

    if request.method == 'POST':
        selected_socio = Socio.query.get(form.socio.data)
        estado_marital = selected_socio.estado_marital.value
    else:
        selected_socio = socios[0]
        estado_marital = selected_socio.estado_marital.value

    required_docs = get_required_docs(estado_marital)
    form.doc_type.choices = [(doc, doc) for doc in required_docs + get_optional_docs()]

    if form.validate_on_submit():
        file = form.document.data
        filename = f"{uuid.uuid4()}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = f"uploads/{filename}"
        document = Document(
            doc_type=form.doc_type.data,
            file_path=file_url,
            socio_id=form.socio.data
        )
        with app.app_context():
            db.session.add(document)
            db.session.commit()
        flash('¡Documento subido exitosamente!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('upload.html', form=form)

@app.route('/estado/<int:socio_id>')
@login_required
def status(socio_id):
    with app.app_context():
        socio = Socio.query.get_or_404(socio_id)
        if socio.user_id != current_user.id:
            flash('No tienes permiso para ver este socio.', 'danger')
            return redirect(url_for('dashboard'))
        estado_marital = socio.estado_marital.value
        required_docs = get_required_docs(estado_marital)
        optional_docs = get_optional_docs()
        submitted_docs = [doc.doc_type for doc in Document.query.filter_by(socio_id=socio_id).all()]
    pending_docs = set(required_docs) - set(submitted_docs)
    uploaded_optional_docs = set(optional_docs).intersection(set(submitted_docs))
    pending_optional_docs = set(optional_docs) - set(submitted_docs)
    return render_template(
        'status.html',
        socio=socio,
        pending_docs=pending_docs,
        submitted_docs=submitted_docs,
        uploaded_optional_docs=uploaded_optional_docs,
        pending_optional_docs=pending_optional_docs
    )

@app.route('/consultar_socios')
@login_required
def consultar_socios():
    with app.app_context():
        socios = Socio.query.filter_by(user_id=current_user.id).all()
    return render_template('consultar_socios.html', socios=socios)

@app.route('/exportar_socios')
@login_required
def exportar_socios():
    with app.app_context():
        socios = Socio.query.filter_by(user_id=current_user.id).all()

    # Create a CSV file in memory
    si = StringIO()
    writer = csv.writer(si)

    # Write CSV header
    writer.writerow([
        'Nombre', 'Apellido Paterno', 'Apellido Materno', 'RFC', 'CURP',
        'Fecha de Nacimiento', 'Dirección', 'Correo Electrónico',
        'Teléfono Fijo', 'Teléfono Celular', 'Estado Marital',
        'Nombre del Cónyuge', 'Apellido Paterno del Cónyuge', 'Apellido Materno del Cónyuge'
    ])

    # Write data rows
    for socio in socios:
        writer.writerow([
            socio.nombre,
            socio.apellido_paterno,
            socio.apellido_materno,
            socio.rfc,
            socio.curp,
            socio.fecha_nacimiento.strftime('%Y-%m-%d'),
            socio.direccion,
            socio.email,
            socio.telefono_fijo or '',
            socio.telefono_celular or '',
            socio.estado_marital.value,
            socio.nombre_conyuge or '',
            socio.apellido_paterno_conyuge or '',
            socio.apellido_materno_conyuge or ''
        ])

    # Create a Flask response with the CSV data
    output = si.getvalue()
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=socios.csv'
    return response

@app.route('/socio/<int:socio_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_socio(socio_id):
    socio = Socio.query.get_or_404(socio_id)
    if socio.user_id != current_user.id:
        flash('No tienes permiso para editar este socio.', 'danger')
        return redirect(url_for('dashboard'))
    form = UpdateSocioForm(request.form, obj=socio)
    if form.validate_on_submit():
        # Update socio object with form data
        form.populate_obj(socio)
        # Handle spouse fields
        if socio.estado_marital == 'casado':
            if not socio.nombre_conyuge:
                socio.nombre_conyuge = ''
            if not socio.apellido_paterno_conyuge:
                socio.apellido_paterno_conyuge = ''
            if not socio.apellido_materno_conyuge:
                socio.apellido_materno_conyuge = ''
        else:
            socio.nombre_conyuge = None
            socio.apellido_paterno_conyuge = None
            socio.apellido_materno_conyuge = None
        db.session.commit()
        flash('¡Información del socio actualizada exitosamente!', 'success')
        return redirect(url_for('ver_socio', socio_id=socio.id))
    return render_template('editar_socio.html', form=form, socio=socio)

@app.route('/socio/<int:socio_id>/eliminar', methods=['POST'])
@login_required
def eliminar_socio(socio_id):
    with app.app_context():
        socio = Socio.query.get_or_404(socio_id)
        if socio.user_id != current_user.id:
            flash('No tienes permiso para eliminar este socio.', 'danger')
            return redirect(url_for('dashboard'))
        # Delete associated documents first to maintain referential integrity
        Document.query.filter_by(socio_id=socio.id).delete()
        db.session.delete(socio)
        db.session.commit()
    flash('¡Socio eliminado exitosamente!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

