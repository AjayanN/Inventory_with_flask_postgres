from flask_wtf import FlaskForm
from wtforms import SubmitField , StringField, PasswordField, SelectField, FileField
from wtforms.fields.html5 import DateField, IntegerField, DecimalField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError
from passlib.hash import pbkdf2_sha256
from models import *
from flask_wtf.file import FileAllowed, FileRequired


def invalid_credentials(form,field):
    # username and password checker

    username_entered = form.username.data
    password_entered = field.data

    # check username
    user_object = User.query.filter_by(username=username_entered).first()
    if user_object is None:
        raise ValidationError("Username or password is incorrect")
    elif not pbkdf2_sha256.verify(password_entered, user_object.password):
        raise ValidationError("Username or password is incorrect")


class RegistrationForm(FlaskForm):
    # Registration form

    username = StringField('username_label',
     validators = [InputRequired(message="Username Required"),
     Length(min=4,max=25, message="Username \
         must be between 4 to 25 characters")])
    password = PasswordField('password_label',
        validators = [InputRequired(message="Password Required"),
     Length(min=4,max=25, message="Password must be \
         between 4 to 25 characters")])
    confirm_pswd = PasswordField('confirm_pswd_label',
        validators = [InputRequired(message="Password Required"),
        EqualTo('password',message="Password must match")])
    designation = SelectField(u'designation_label',choices=[('ADMIN','ADMIN'),('USER','USER')])
    submit_button = SubmitField('Submit',render_kw={'class':'btn btn-success'})

    def validate_username(self,username):
        user_object = User.query.filter_by(username=username.data).first()
        if user_object:
            raise ValidationError("Username already exists")

class LoginForm(FlaskForm):
    username = StringField('username_label',validators = [InputRequired(message="Username Required")])
    password = PasswordField('password_label',
        validators = [InputRequired(message="Password Required"),
        invalid_credentials])
    
    submit_button = SubmitField('Login',render_kw={'class':'btn btn-success'})

class ParticularForm(FlaskForm):
    # Registration form

    invoice_no = IntegerField('quantity_label',
        validators = [InputRequired(message="Invoice Required")])
    date_purchase = DateField('date_purchase_label',
     validators = [InputRequired(message="Purchase Date Required")],
      format="%Y-%m-%d")
    particular_name = StringField('particular_name_label',
        validators = [InputRequired(message="Particular Name Required"),
     Length(min=1,max=50, message="Password must be \
         between 2 to 50 characters")])
    quantity = IntegerField('quantity_label',
        validators = [InputRequired(message="Quantity Required")])
    pack_unit = StringField('packunit_name_label',validators = [InputRequired(message="Invoice Required")])
    price = DecimalField('price_label',places=2,
        validators = [InputRequired(message="Price Required")])
    supplier = StringField('supplier_label',
        validators = [InputRequired(message="Supplier Name Required"),
     Length(min=1,max=50, message="Supplier must be \
         between 2 to 50 characters")])
    brand = StringField('brand_label',
        validators = [InputRequired(message="Brand Required"),
     Length(min=1,max=50, message="Brand must be \
         between 2 to 50 characters")])
    
    
    submit_button = SubmitField('Submit',render_kw={'class':'btn btn-success'})


class SearchForm(FlaskForm):
    search = StringField('search_label',validators = [InputRequired(message="Supplier Name Required")])
    st_date = DateField('start_date_label',
      format="%Y-%m-%d")
    
    end_date = DateField('end_date_label',
    format="%Y-%m-%d")

    submit_button = SubmitField('Search',render_kw={'class':'btn btn-success'})

class IndentForm(FlaskForm):

    indent_no = IntegerField('quantity_label',
        validators = [InputRequired(message="Indent Required")])
    department = StringField('department_label',
        validators = [InputRequired(message="Department Required"),
     Length(min=2,max=50, message="Department must be \
         between 2 to 50 characters")])
    indent_dt = DateField('indent_date_label',
      format="%Y-%m-%d",
     validators = [InputRequired(message="Indent Date Required")])
    particular_name = StringField('particular_name_label')
    lab_or_class = StringField('labclass_label',
        validators = [InputRequired(message="Lab or Class Required"),
     Length(min=2,max=50, message="lab_or_class must be \
         between 2 to 50 characters")])
    quantity = StringField('quantity_label',
        validators = [InputRequired(message="Quantity Required")])
    submit_button = SubmitField('Submit',render_kw={'class':'btn btn-success'})

class IssueForm(FlaskForm):
    indent_no =SelectField(u'indent_no_label',validators = [InputRequired(message="Indent Required")])
    particular_name = SelectField(u'particular_name_label',validators = [InputRequired(message="Particular Required")])
    quantity = StringField('quantity_label',
        validators = [InputRequired(message="Quantity Required")])
    pack_unit = StringField('packunit_name_label')
    price = DecimalField('price_label',places=2,
        validators = [InputRequired(message="Price Required")])
    brand = SelectField(u'brand_label',validators = [InputRequired(message="Brand Required")])
    issue_dt = DateField('issued_date_label',
      format="%Y-%m-%d",
     validators = [InputRequired(message="Issued Date Required")])
    submit_button = SubmitField('Submit',render_kw={'class':'btn btn-success'})


class UploadForm(FlaskForm):
    upload = FileField('upload_label',validators = [FileRequired(),
        FileAllowed(['xlsx'], 'xlsx files only!')])
    submit_button = SubmitField('Submit',render_kw={'class':'btn btn-success'})

    