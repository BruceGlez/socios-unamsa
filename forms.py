# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_wtf.file import FileAllowed, FileRequired

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class SocioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()], render_kw={"id": "nombre"})
    apellido_paterno = StringField('Apellido Paterno', validators=[DataRequired()], render_kw={"id": "apellido_paterno"})
    apellido_materno = StringField('Apellido Materno', validators=[DataRequired()], render_kw={"id": "apellido_materno"})
    rfc = StringField('RFC', validators=[DataRequired(), Length(min=12, max=13)], render_kw={"id": "rfc"})
    curp = StringField('CURP', validators=[DataRequired(), Length(min=18, max=18)], render_kw={"id": "curp"})
    fecha_nacimiento = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[DataRequired()], render_kw={"id": "fecha_nacimiento"})
    direccion = StringField('Dirección', validators=[DataRequired()], render_kw={"id": "direccion"})
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()], render_kw={"id": "email"})
    telefono_fijo = StringField('Teléfono Fijo', render_kw={"id": "telefono_fijo"})
    telefono_celular = StringField('Teléfono Celular', render_kw={"id": "telefono_celular"})
    estado_marital = SelectField('Estado Marital', choices=[
        ('soltero', 'Soltero'),
        ('casado', 'Casado'),
        ('divorciado', 'Divorciado'),
        ('viudo', 'Viudo')
    ], validators=[DataRequired()], render_kw={"id": "estado_marital"})
    # Spouse fields
    nombre_conyuge = StringField('Nombre del Cónyuge', render_kw={"id": "nombre_conyuge"})
    apellido_paterno_conyuge = StringField('Apellido Paterno del Cónyuge', render_kw={"id": "apellido_paterno_conyuge"})
    apellido_materno_conyuge = StringField('Apellido Materno del Cónyuge', render_kw={"id": "apellido_materno_conyuge"})
    submit = SubmitField('Registrar Socio')
    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False

        if self.estado_marital.data == 'casado':
            missing_fields = False
            if not self.nombre_conyuge.data:
                self.nombre_conyuge.errors.append('Este campo es requerido si el estado marital es Casado.')
                missing_fields = True
            if not self.apellido_paterno_conyuge.data:
                self.apellido_paterno_conyuge.errors.append('Este campo es requerido si el estado marital es Casado.')
                missing_fields = True
            if not self.apellido_materno_conyuge.data:
                self.apellido_materno_conyuge.errors.append('Este campo es requerido si el estado marital es Casado.')
                missing_fields = True
            if missing_fields:
                return False
        return True

class UpdateSocioForm(SocioForm):
    submit = SubmitField('Actualizar Socio')

class UploadForm(FlaskForm):
    socio = SelectField('Seleccionar Socio', validators=[DataRequired()], coerce=int)
    doc_type = SelectField('Tipo de Documento', validators=[DataRequired()])
    document = FileField('Subir Documento', validators=[FileRequired(), FileAllowed(['pdf', 'docx', 'jpg', 'png'])])
    submit = SubmitField('Subir')
