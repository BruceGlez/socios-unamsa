# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from datetime import datetime
from sqlalchemy import Enum
import enum

db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class EstadoMaritalEnum(enum.Enum):
    soltero = "Soltero"
    casado = "Casado"
    divorciado = "Divorciado"
    viudo = "Viudo"

class User(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    socios = db.relationship('Socio', backref='creador', lazy=True, foreign_keys='Socio.user_id')

class Socio(db.Model):
    __tablename__ = 'socio'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100), nullable=False)
    rfc = db.Column(db.String(13), nullable=False)
    curp = db.Column(db.String(18), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono_fijo = db.Column(db.String(20))
    telefono_celular = db.Column(db.String(20))
    estado_marital = db.Column(db.Enum(EstadoMaritalEnum), nullable=False)
    nombre_conyuge = db.Column(db.String(100))
    apellido_paterno_conyuge = db.Column(db.String(100))
    apellido_materno_conyuge = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    documentos = db.relationship('Document', backref='socio', lazy=True)

class Document(db.Model):
    __tablename__ = 'documento'
    id = db.Column(db.Integer, primary_key=True)
    doc_type = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    socio_id = db.Column(db.Integer, db.ForeignKey('socio.id'), nullable=False)
