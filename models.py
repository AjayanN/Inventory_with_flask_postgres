from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,date
from flask_login import UserMixin


db = SQLAlchemy()

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    designation = db.Column(db.Text,nullable=False)

    def __repr__(self):
        return 'user ' + str(self.id)


class Particular(UserMixin, db.Model):

    __tablename__ = "particulars"
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.Integer)
    date_purchase = db.Column(db.Date,nullable=False,default=datetime.now())
    particular_name = db.Column(db.Text,nullable=False)
    quantity = db.Column(db.Integer,nullable=False)
    pack_unit = db.Column(db.Text)
    price = db.Column(db.Float(precision=2),nullable=False)
    supplier = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    def __repr__(self):
        return 'Particular ' + str(self.id)

class Stock(UserMixin, db.Model):

    __tablename__ = "stocks"
    id = db.Column(db.Integer, primary_key=True)
    particular_name = db.Column(db.Text,nullable=False)
    pack_amount = db.Column(db.Float(precision=2),nullable=False)
    price = db.Column(db.Float(precision=2),nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    unit = db.Column(db.Text,nullable=False)

class Indent(UserMixin, db.Model):
    __tablename__ = "indents"
    id = db.Column(db.Integer, primary_key=True)
    indent_no = db.Column(db.Integer)
    department = db.Column(db.Text)
    indent_dt = db.Column(db.Date,nullable=False,default=date.today())
    particular_name = db.Column(db.Text)
    lab_or_class = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Text)

class Quotation(UserMixin, db.Model):
    __tablename__ = "quotations"
    id = db.Column(db.Integer, primary_key=True)
    supplier = db.Column(db.Text,nullable=False)
    chemical_name = db.Column(db.Text,nullable=False)
    pack_unit = db.Column(db.Text,nullable=False)
    unit_rate = db.Column(db.Float(precision=2),nullable=False)
    discount = db.Column(db.Float(precision=2),nullable=False)
    quantity = db.Column(db.Integer)
    total = db.Column(db.Float(precision=2),nullable=False)
    gst = db.Column(db.Float(precision=2),nullable=False)
    grand_total = db.Column(db.Float(precision=2),nullable=False)
    date_of_entry = db.Column(db.Date,nullable=False,default=date.today())

class Issue(UserMixin, db.Model):
    __tablename__ = "issued"
    id = db.Column(db.Integer, primary_key=True)
    particular_name = db.Column(db.Text)
    quantity = db.Column(db.Text)
    price = db.Column(db.Float(precision=2),nullable=False)
    brand = db.Column(db.Text)
    issue_dt = db.Column(db.Date,nullable=False,default=date.today())
    indent_no = db.Column(db.Integer)


