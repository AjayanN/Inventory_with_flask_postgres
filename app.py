from flask import Flask, render_template, request, redirect, url_for, flash, json
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from wtform_fields import *
from flask_mail import Mail, Message
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename
import pandas as pd
from flaskwebgui import FlaskUI
from xlrd import *
import os, sys

base_dir = '.'
if hasattr(sys, '_MEIPASS'):
    base_dir = os.path.join(sys._MEIPASS)

app = Flask(__name__,
        static_folder=os.path.join(base_dir, 'static'),
        template_folder=os.path.join(base_dir, 'templates')
        )

app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
app.secret_key = os.environ.get('SECRET') 

# configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') # format: postgresql+pyscopg2://username:password@server_of_db/dbname


db.init_app(app)

# configure flask login
login_manage = LoginManager(app)
login_manage.init_app(app)

# configure flask mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465

app.config['MAIL_USERNAME'] = os.environ.get('MAIL_NAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PWD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

ui=FlaskUI(app,fullscreen=True)

@login_manage.user_loader
def load_user(id):
    return User.query.get(int(id))

# register a new person


@app.route('/register', methods=['GET', 'POST'])
def index():

    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data
        designation = reg_form.designation.data
        # hash password
        hashed_pswd = pbkdf2_sha256.hash(password)

        #  check username exists
        user = User(username=username, password=hashed_pswd,
                    designation=designation)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully', 'success')

        return redirect(url_for('dashboard'))

    return render_template('index.html', form=reg_form)


# login a new person
@app.route("/", methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    # Allow login if validation success
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(
            username=login_form.username.data).first()
        login_user(user_object)
        return redirect(url_for('dashboard'))

    return render_template('login.html', form=login_form)

# Particulars dashboard


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    part_form = ParticularForm()
    search_form = SearchForm()
    page = 'dashboard'
    particulars = Particular.query.all()
    if request.method == "GET":
        if not current_user.is_authenticated:
            flash('Please login.', 'danger')
            return redirect(url_for('login'))
        else:

            if current_user.designation == 'ADMIN':
                logged = 'admin'
            else:
                logged = 'user'

            canvas = db.session.query(Particular.supplier, db.func.count(
                Particular.id)).group_by(Particular.supplier).all()
            if canvas:
                supplier = json.dumps([x[0] for x in canvas])
                canvas = json.dumps([x[1] for x in canvas])
            else:
                supplier = []
                canvas = []
            return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
    else:
        if part_form.validate_on_submit():
            invoice_no = part_form.invoice_no.data
            date_purchase = part_form.date_purchase.data
            particular_name = part_form.particular_name.data.lower()
            quantity = part_form.quantity.data
            pack_unit = part_form.pack_unit.data.lower()
            price = part_form.price.data
            supplier = part_form.supplier.data.lower()
            brand = part_form.brand.data.lower()

            particular_object = Particular.query.filter_by(
                invoice_no=part_form.invoice_no.data).first()
            if particular_object:
                flash("Invoice number already exists", 'danger')
                return redirect(url_for('dashboard'))

            new_particular = Particular(
                invoice_no=invoice_no,
                date_purchase=date_purchase,
                particular_name=particular_name,
                quantity=quantity,
                pack_unit=pack_unit,
                price=price,
                supplier=supplier,
                brand = brand
            )

            st_num = ''
            st_unit = ''
            stock_val = []
            for i in pack_unit:
                if i.isdigit():
                    st_num += i
                elif i.isalpha():
                    st_unit += i
            stock_val.append(st_num)
            stock_val.append(st_unit)

            if stock_val[1] in ['g', 'ml','g/ml']:
                stock_val[0] = int(stock_val[0])
                stock_val[1] = 'g/ml'
            elif stock_val[1] in ['kg', 'l']:
                stock_val[0] = int(stock_val[0])*1000
                stock_val[1] = 'g/ml'
            else:
                stock_val[1] = 'nos'
            
            
            stocks = Stock.query.filter(
                            Stock.particular_name == particular_name,
                            Stock.brand == brand).all()
                      
            if stocks:
                for each in stocks:
                    id = each.id
                stocks = Stock.query.get_or_404(id)
                if stock_val[1] == 'g/ml':
                    stocks.pack_amount= float(stocks.pack_amount)+(float(stock_val[0])*int(quantity))
                    stocks.price = float(stocks.price)+float(price)
                elif stock_val[1]=='nos':
                    stocks.pack_amount= int(stocks.pack_amount)+(int(stock_val[0])*int(quantity))
                    stocks.price = float(stocks.price)+float(price)

            else:
                if stock_val[1]=='nos':
                    new_stock = Stock(
                        particular_name = particular_name,
                        pack_amount = int(stock_val[0])*int(quantity),
                        price = price,
                        brand = brand,
                        unit = stock_val[1]
                    )
                else:
                    new_stock = Stock(
                        particular_name = particular_name,
                        pack_amount = stock_val[0]*quantity,
                        price = price,
                        brand = brand,
                        unit = stock_val[1]
                    )
                db.session.add(new_stock)

            db.session.add(new_particular)
            db.session.commit()
            flash('Inserted Successfully', 'success')
            return redirect(url_for('dashboard'))

        return redirect(url_for('dashboard'))

#indent by the labs
@app.route('/indent', methods=['GET', 'POST'])
def indent():
    search_form = SearchForm()
    indent_form = IndentForm()
    page = 'indent'
    if request.method == "GET":
        if not current_user.is_authenticated:
            flash('Please login.', 'danger')
            return redirect(url_for('login'))
        else:
            particulars = Indent.query.all()
            if current_user.designation == 'ADMIN':
                logged = 'admin'
            else:
                logged = 'user'
            canvas = db.session.query(Indent.lab_or_class, db.func.count(
                Indent.id)).group_by(Indent.lab_or_class).all()
            if canvas:
                supplier = json.dumps([x[0] for x in canvas])
                canvas = json.dumps([x[1] for x in canvas])
            else:
                supplier = []
                canvas = []
            return render_template('dashboard.html', particulars=particulars, logged=logged,
                                   form=indent_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
    else:
        if indent_form.validate_on_submit():
            indent_no = indent_form.indent_no.data
            department = indent_form.department.data.lower()
            indent_dt = indent_form.indent_dt.data
            particular_name = indent_form.particular_name.data.lower()
            lab_or_class = indent_form.lab_or_class.data.lower()
            quantity = indent_form.quantity.data.lower()

            indent_object = Indent.query.filter_by(
                indent_no=indent_form.indent_no.data).first()
            if indent_object:
                flash("Indent number already exists", 'danger')
                return redirect(url_for('indent'))

            new_indent = Indent(
                indent_no=indent_no,
                department=department,
                indent_dt=indent_dt,
                particular_name=particular_name,
                lab_or_class=lab_or_class,
                quantity=quantity
            )
            db.session.add(new_indent)
            db.session.commit()
            flash('Inserted Successfully', 'success')
            return redirect(url_for('indent'))
        return redirect(url_for('indent'))

#issuing to the indent
@app.route('/issue',methods = ['GET','POST'])
def issue():
    part_form = IssueForm()
    search_form = SearchForm()
    part_form.indent_no.choices = [(row.indent_no, row.indent_no) for row in Indent.query.all() if row.quantity!='0nos']
    part_form.particular_name.choices = [(row.particular_name, row.particular_name) for row in Stock.query.all()]
    part_form.brand.choices = [(row.brand, row.brand) for row in Stock.query.all()]
    page = 'issued'
    particulars = Issue.query.all()
    if request.method == "GET":
        if not current_user.is_authenticated:
            flash('Please login.', 'danger')
            return redirect(url_for('login'))
        else:

            if current_user.designation == 'ADMIN':
                logged = 'admin'
            else:
                logged = 'user'

            canvas = db.session.query(Issue.particular_name,Issue.brand, db.func.count(Issue.id)).group_by(Issue.particular_name,Issue.brand).all()
            if canvas:
                supplier = json.dumps([x[0]+' of '+x[1] for x in canvas])
                canvas = json.dumps([x[2] for x in canvas])
            else:
                supplier = []
                canvas = []

            
            return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
    else:
        if part_form.validate_on_submit():
            indent_no = part_form.indent_no.data
            issue_dt = part_form.issue_dt.data
            particular_name = part_form.particular_name.data.lower()
            quantity = part_form.quantity.data.lower()
            price = part_form.price.data
            
            brand = part_form.brand.data.lower()

            new_issue = Issue(
                indent_no=indent_no,
                issue_dt=issue_dt,
                particular_name=particular_name,
                quantity=quantity,
                price=price,
                brand = brand
            )
            stock_object = Stock.query.filter(Stock.particular_name==particular_name,Stock.brand==brand).first()
            
            if stock_object:
                stock_id = stock_object.id
                pack_amount = stock_object.pack_amount
                unit = stock_object.unit
                
                indent_object = Indent.query.filter_by(
                    indent_no=part_form.indent_no.data).first()
                pack_unit = indent_object.quantity
                id = indent_object.id
                


                indent_val = []
                st_num = ''
                st_unit = ''
                for i in pack_unit:
                    if i.isdigit():
                        st_num += i
                    elif i.isalpha():
                        st_unit += i
                indent_val.append(st_num)
                indent_val.append(st_unit)


                if indent_val[1] in ['g', 'ml','g/ml']:
                    indent_val[0] = int(indent_val[0])
                    indent_val[1] = 'g/ml'
                elif indent_val[1] in ['kg', 'l']:
                    indent_val[0] = int(indent_val[0])*1000
                    indent_val[1] = 'g/ml'
                else:
                    indent_val[1] = 'nos'
                
                issue_val = []
                st_num = ''
                st_unit = ''
                for i in quantity:
                    if i.isdigit():
                        st_num += i
                    elif i.isalpha():
                        st_unit += i
                issue_val.append(st_num)
                issue_val.append(st_unit)


                if issue_val[1] in ['g', 'ml','g/ml']:
                    issue_val[0] = int(issue_val[0])
                    issue_val[1] = 'g/ml'
                elif issue_val[1] in ['kg', 'l']:
                    issue_val[0] = int(issue_val[0])*1000
                    issue_val[1] = 'g/ml'
                else:
                    issue_val[1] = 'nos'

                if int(indent_val[0])<int(issue_val[0]):
                    flash("Indent quantity is less than issue quantity. Please do a new indent", 'danger')
                    return redirect(url_for('issue'))
                
                if int(issue_val[0])>pack_amount:
                    flash("Out of stock", 'danger')
                    return redirect(url_for('issue'))

                indent_change = Indent.query.get_or_404(id)
                indent_change.quantity = str(int(indent_val[0])-int(issue_val[0]))+indent_val[1]
                stock_change = Stock.query.get_or_404(stock_id)
                stock_change.pack_amount = float(pack_amount)-float(issue_val[0])
            else:
                flash("Out of stock", 'danger')
                return redirect(url_for('issue'))

            db.session.add(new_issue)
            db.session.commit()

            flash('Inserted Successfully', 'success')
            return redirect(url_for('issue'))

        return redirect(url_for('issue'))

# stock available
@app.route('/stock',methods=['GET','POST'])
def stock():
    if not current_user.is_authenticated:
        flash('Please login.', 'danger')
        return redirect(url_for('login'))

    stocks = Stock.query.all()
    if current_user.designation == 'ADMIN':
        logged = 'admin'
    else:
        logged = 'user'

    if stocks:
        pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
            if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in stocks]
        canvas = json.dumps([each[0] for each in pack_unit_particular])
        supplier = json.dumps([each[1]+' of '+each[2]+':in:'+each[3] for each in pack_unit_particular])
        
    else:
        supplier = []
        canvas = []
        pack_unit_particular=[]
    
    form1 = SearchForm()

    if request.method == "GET":
        for each in stocks:
            if each.pack_amount<=0:
                db.session.delete(each)
        db.session.commit()
        return render_template('stock.html', form1 = form1,particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)
    else:
        # search in stocks
        st_date = form1.st_date.data
        end_date = form1.end_date.data
        search_data = form1.search.data
        string_val = search_data.split()
        if len(string_val) not in [0, 1] and search_data.upper() != 'ALL':
            search_data = string_val[0].upper()
            if search_data == 'STOCK' and string_val[1].isnumeric():
                if st_date and end_date:
                    particulars = Stock.query.filter(
                        Stock.pack_Amount == string_val[1], Stock.date_purchase >= st_date, Stock.date_purchase <= end_date).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                else:
                    particulars = Stock.query.filter_by(
                        pack_amount=string_val[1]).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                return render_template('stock.html',form1 = form1, particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)
            elif search_data == 'PRICE' and string_val[1].isnumeric():
                if st_date and end_date:
                    particulars = Stock.query.filter(
                        Stock.price == string_val[1], Stock.date_purchase >= st_date, Stock.date_purchase <= end_date).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]            
                else:
                    particulars = Stock.query.filter_by(
                        price=string_val[1]).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                return render_template('stock.html',form1 = form1, particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)
            elif search_data == 'UNIT':
                if st_date and end_date:
                    particulars = Stock.query.filter(Stock.unit.like(
                        f'%{string_val[1].lower()}%'), Stock.date_purchase >= st_date, Stock.date_purchase <= end_date).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                else:
                    particulars = Stock.query.filter(
                        Stock.unit.like(f'%{string_val[1].lower()}%')).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                return render_template('stock.html',form1 = form1, particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)
            elif search_data == 'PARTICULAR':
                if st_date and end_date:
                    particulars = Stock.query.filter(Stock.particular_name.like(
                        f'%{string_val[1].lower()}%'), Stock.date_purchase >= st_date, Stock.date_purchase <= end_date).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                else:
                    particulars = Stock.query.filter(
                        Stock.particular_name.like(f'%{string_val[1].lower()}%')).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                return render_template('stock.html',form1 = form1, particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)
            elif search_data == 'BRAND':
                if st_date and end_date:
                    particulars = Stock.query.filter(Stock.brand.like(
                        f'%{string_val[1].lower()}%'), Stock.date_purchase >= st_date, Stock.date_purchase <= end_date).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                else:
                    particulars = Stock.query.filter(
                        Stock.brand.like(f'%{string_val[1].lower()}%')).all()
                    pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
                return render_template('stock.html',form1 = form1, particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)
            else:
                flash('Something wrong with the format', 'warning')
                return redirect(url_for('stock'))
        else:
            if st_date and end_date:
                particulars = Stock.query.filter(Stock.date_purchase >= st_date, Stock.date_purchase <= end_date).all()
                pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
            else:
                particulars = Stock.query.all()
                pack_unit_particular = [[int(each.pack_amount), each.particular_name, each.brand ,each.unit] \
                        if each.unit=='nos' else [each.pack_amount, each.particular_name, each.brand ,each.unit]  for each in particulars]
            return render_template('stock.html',form1 = form1, particulars=pack_unit_particular, logged=logged,
                                   supplier=supplier, canvas=canvas)

# quotations using pandas for row extraction
@app.route('/quotation', methods=['GET', 'POST'])
def quotation():
    if not current_user.is_authenticated:
        flash('Please login.', 'danger')
        return redirect(url_for('login'))
    upload_form = UploadForm(CombinedMultiDict((request.files, request.form)))
    search_form = SearchForm()
    if current_user.designation == 'ADMIN':
        logged = 'admin'
    else:
        logged = 'user'
    page = 'quotation'
    particular = Quotation.query.all()
    if request.method == 'POST':
        if upload_form.validate_on_submit():
            f = upload_form.upload.data
            filename = secure_filename(f.filename)
            upload_form.upload.data.save(
                app.config['UPLOAD_FOLDER'] + filename)
            flash("CSV saved.", 'success')
            x = pd.read_excel(app.config['UPLOAD_FOLDER'] + filename)
            for i in range(len(x)):
                particular = Quotation(
                    supplier=x.loc[i].Supplier.lower(),
                    chemical_name=x.loc[i].Chemical_name.lower(),
                    pack_unit=x.loc[i].Pack_Unit.lower(),
                    unit_rate=float(x.loc[i].Unit_Rate),
                    discount=float(x.loc[i].Discount),
                    quantity=int(x.loc[i].Quantity),
                    total=float(x.loc[i].Total),
                    gst=float(x.loc[i].GST),
                    grand_total=float(x.loc[i].Grand_Total),
                    date_of_entry=date.today()
                )
                db.session.add(particular)
                db.session.commit()
            return redirect(url_for('quotation'))

    canvas = db.session.query(Quotation.chemical_name, db.func.count(
        Quotation.id)).group_by(Quotation.chemical_name).all()
    if canvas:
        supplier = json.dumps([x[0] for x in canvas])
        canvas = json.dumps([x[1] for x in canvas])
    else:
        supplier = []
        canvas = []
    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)

#search for every url other than stocks
@app.route('/view/<string:page>', methods=['GET', 'POST'])
def retrieve(page):
    search_form = SearchForm()
    search_data = search_form.search.data
    particulars = Particular.query.all()
    if current_user.designation == 'ADMIN':
        logged = 'admin'
    else:
        logged = 'user'

    st_date = search_form.st_date.data
    end_date = search_form.end_date.data
    if page == 'dashboard':
        if particulars:
            canvas = json.dumps([each.price for each in particulars])
            supplier = json.dumps([f'{each.particular_name}:{each.supplier} in nos' if each.pack_unit ==
                                   '' else f'{each.particular_name}:{each.supplier} in (g/ml)' for each in particulars])
        else:
            supplier = []
            canvas = []
        part_form = ParticularForm()
        if request.method == 'POST':
            string_val = search_data.split()
            if len(string_val) not in [0, 1] and search_data.upper() != 'ALL':
                search_data = string_val[0].upper()
                if search_data == 'INVOICE_NO' and string_val[1].isnumeric():
                    
                    if st_date and end_date:
                        particulars = Particular.query.filter(
                            Particular.invoice_no == string_val[1], Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter_by(
                            invoice_no=string_val[1]).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'PARTICULAR':
                    if st_date and end_date:
                        particulars = Particular.query.filter(Particular.particular_name.like(
                            f'%{string_val[1].lower()}%'), Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter(
                            Particular.particular_name.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'QUANTITY' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particulars = Particular.query.filter(
                            Particular.quantity == string_val[1], Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter_by(
                            quantity=string_val[1]).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'PACK_UNIT':
                    if st_date and end_date:
                        particulars = Particular.query.filter(Particular.pack_unit.like(
                            f'%{string_val[1].lower()}%'), Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter(
                            Particular.pack_unit.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'PRICE' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particulars = Particular.query.filter(
                            Particular.price == string_val[1], Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter_by(
                            price=string_val[1]).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'SUPPLIER':
                    if st_date and end_date:
                        particulars = Particular.query.filter(Particular.supplier.like(
                            f'%{string_val[1].lower()}%'), Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter(
                            Particular.supplier.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'BRAND':
                    if st_date and end_date:
                        particulars = Particular.query.filter(Particular.brand.like(
                            f'%{string_val[1].lower()}%'), Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Particular.query.filter(
                            Particular.brand.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                else:
                    flash('Something wrong with the format', 'warning')
                    return redirect(url_for('dashboard'))
            else:
                if st_date and end_date:
                    particulars = Particular.query.filter(
                        Particular.date_purchase >= st_date, Particular.date_purchase <= end_date).all()
                else:
                    particulars = Particular.query.all()
                return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
        else:
            return redirect(url_for('dashboard'))

    elif page == 'indent':
        canvas = db.session.query(Indent.lab_or_class, db.func.count(
            Indent.id)).group_by(Indent.lab_or_class).all()
        if canvas:
            supplier = json.dumps([x[0] for x in canvas])
            canvas = json.dumps([x[1] for x in canvas])
        else:
            supplier = []
            canvas = []
        part_form = IndentForm()
        if request.method == 'POST':
            string_val = search_data.split()
            if len(string_val) not in [0, 1] and search_data.upper() != 'ALL':
                search_data = string_val[0].upper()
                if search_data == 'INDENT_NO' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particulars = Indent.query.filter(
                            Indent.indent_no == string_val[1], Indent.indent_dt >= st_date, Indent.indent_dt <= end_date).all()
                    else:
                        particulars = Indent.query.filter_by(
                            indent_no=string_val[1]).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'DEPARTMENT':
                    if st_date and end_date:
                        particulars = Indent.query.filter(Indent.department.like(
                            f'%{string_val[1].lower()}%'), Indent.indent_dt >= st_date, Indent.indent_dt <= end_date).all()
                    else:
                        particulars = Indent.query.filter(
                            Indent.department.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'QUANTITY':
                    if st_date and end_date:
                        particulars = Indent.query.filter(Indent.quantity.like(
                            f'%{string_val[1].lower()}%'), Indent.indent_dt >= st_date, Indent.indent_dt <= end_date).all()
                    else:
                        particulars = Indent.query.filter(
                            Indent.quantity.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'PARTICULAR':
                    if st_date and end_date:
                        particulars = Indent.query.filter(Indent.particular_name.like(
                            f'%{string_val[1].lower()}%'), Indent.indent_dt >= st_date, Indent.indent_dt <= end_date).all()
                    else:
                        particulars = Indent.query.filter(
                            Indent.particular_name.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'LAB/CLASS':
                    if st_date and end_date:
                        particulars = Indent.query.filter(Indent.lab_or_class.like(
                            f'%{string_val[1].lower()}%'), Indent.indent_dt >= st_date, Indent.indent_dt <= end_date).all()
                    else:
                        particulars = Indent.query.filter(
                            Indent.lab_or_class.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                else:
                    flash('Something wrong with the format', 'warning')
                    return redirect(url_for('indent'))
            else:
                if st_date and end_date:
                    particulars = Indent.query.filter(
                        Indent.indent_dt >= st_date, Indent.indent_dt <= end_date).all()
                else:
                    particulars = Indent.query.all()
                return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
        else:
            return redirect(url_for('indent'))

    elif page == 'quotation':
        canvas = db.session.query(Quotation.chemical_name, db.func.count(
            Quotation.id)).group_by(Quotation.chemical_name).all()
        if canvas:
            supplier = json.dumps([x[0] for x in canvas])
            canvas = json.dumps([x[1] for x in canvas])
        else:
            supplier = []
            canvas = []
        upload_form = UploadForm(
            CombinedMultiDict((request.files, request.form)))
        if request.method == 'POST':
            string_val = search_data.split()
            if len(string_val) not in [0, 1] and search_data.upper() != 'ALL':
                search_data = string_val[0].upper()
                if search_data == 'SUPPLIER':
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.supplier.like(
                            f'%{string_val[1].lower()}%'), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter(
                            Quotation.supplier.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'PARTICULAR':
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.chemical_name.like(
                            f'%{string_val[1].lower()}%'), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                        particulars = Quotation.query.filter(Quotation.chemical_name == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter(
                            Quotation.chemical_name.like(f'%{string_val[1].lower()}%')).all()
                        particulars = Quotation.query.filter_by(
                            chemical_name=string_val[1].lower()).all()
                    if particulars:
                        particular = particulars
                    pack_unit = [each.pack_unit for each in particular]
                    canvas = []
                    for each in pack_unit:
                        st_num = ''
                        st_unit = ''
                        for i in each:
                            if i.isdigit():
                                st_num += i
                            elif i.isalpha():
                                st_unit += i
                        canvas.append([st_num, st_unit])

                    for each in canvas:
                        if each[1] in ['g', 'ml']:
                            each[0] = int(each[0])
                        elif each[1] in ['kg', 'l']:
                            each[0] = int(each[0])*1000

                    new = []

                    for val, each in zip(particular, canvas):
                        new.append(
                            round(val.grand_total/(each[0]*val.quantity), 5))
                    canvas = json.dumps(new)
                    supplier = json.dumps(
                        [each.supplier for each in particular])

                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'QUANTITY' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.quantity == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter_by(
                            quantity=string_val[1]).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'PACK_UNIT':
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.pack_unit.like(
                            f'%{string_val[1].lower()}%'), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter(
                            Quotation.pack_unit.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'UNIT_RATE' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.unit_rate == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter_by(
                            unit_rate=string_val[1]).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'DISCOUNT' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.discount == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter_by(
                            discount=string_val[1]).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'TOTAL' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.total == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter_by(
                            total=string_val[1]).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'GST' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.gst == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter_by(
                            gst=string_val[1]).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                elif search_data == 'GRAND_TOTAL' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particular = Quotation.query.filter(Quotation.grand_total == string_val[1].lower(
                        ), Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                    else:
                        particular = Quotation.query.filter_by(
                            grand_total=string_val[1]).all()
                    return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
                else:
                    flash('Something wrong with the format', 'warning')
                    return redirect(url_for('quotation'))
            else:
                if st_date and end_date:
                    particular = Quotation.query.filter(
                        Quotation.date_of_entry >= st_date, Quotation.date_of_entry <= end_date).all()
                else:
                    particular = Quotation.query.all()
                return render_template('quotation.html', form=upload_form, form1=search_form, logged=logged, particular=particular, page=page, canvas=canvas, supplier=supplier)
        else:

            return redirect(url_for('quotation'))

    elif page == 'issued':

        canvas = db.session.query(Issue.particular_name,Issue.brand, db.func.count(
            Issue.id)).group_by(Issue.particular_name,Issue.brand).all()
        if canvas:
            supplier = json.dumps([x[0]+' of '+x[1] for x in canvas])
            canvas = json.dumps([x[2] for x in canvas])
        else:
            supplier = []
            canvas = []
        part_form = IssueForm()
        if request.method == 'POST':
            string_val = search_data.split()
            if len(string_val) not in [0, 1] and search_data.upper() != 'ALL':
                search_data = string_val[0].upper()
                if search_data == 'INDENT_NO' and string_val[1].isnumeric():
                    
                    if st_date and end_date:
                        particulars = Issue.query.filter(
                            Issue.indent_no == string_val[1], Issue.issue_dt >= st_date, Issue.issue_dt <= end_date).all()
                    else:
                        particulars = Issue.query.filter_by(
                            indent_no=string_val[1]).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'PARTICULAR':
                    if st_date and end_date:
                        particulars = Issue.query.filter(Issue.particular_name.like(
                            f'%{string_val[1].lower()}%'), Issue.issue_dt >= st_date, Issue.issue_dt <= end_date).all()
                    else:
                        particulars = Issue.query.filter(
                            Issue.particular_name.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'QUANTITY':
                    if st_date and end_date:
                        particulars = Issue.query.filter(Issue.quantity.like(
                            f'%{string_val[1].lower()}%'), Issue.issue_dt >= st_date, Issue.issue_dt <= end_date).all()
                    else:
                        particulars = Issue.query.filter(
                            Issue.quantity.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'PRICE' and string_val[1].isnumeric():
                    if st_date and end_date:
                        particulars = Issue.query.filter(
                            Issue.price == string_val[1], Issue.issue_dt >= st_date, Particular.date_purchase <= end_date).all()
                    else:
                        particulars = Issue.query.filter_by(
                            price=string_val[1]).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                elif search_data == 'BRAND':
                    if st_date and end_date:
                        particulars = Issue.query.filter(Issue.brand.like(
                            f'%{string_val[1].lower()}%'), Issue.issue_dt >= st_date, Issue.issue_dt <= end_date).all()
                    else:
                        particulars = Issue.query.filter(
                            Issue.brand.like(f'%{string_val[1].lower()}%')).all()
                    return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
                else:
                    flash('Something wrong with the format', 'warning')
                    return redirect(url_for('dashboard'))
            else:
                if st_date and end_date:
                    particulars = Issue.query.filter(
                        Issue.issue_dt >= st_date, Issue.issue_dt <= end_date).all()
                else:
                    particulars = Issue.query.all()
                return render_template('dashboard.html', particulars=particulars, logged=logged, form=part_form, form1=search_form, page=page, supplier=supplier, canvas=canvas)
        else:
            return redirect(url_for('dashboard'))
    

#delete for purchases
@app.route('/delete/<string:page>/<int:id>')
def delete(page, id):
    if not current_user.is_authenticated:
        flash('Please login.', 'danger')
        return redirect(url_for('login'))

    if page == 'dashboard':
        particular = Particular.query.get_or_404(id)

        stock_object = Stock.query.filter(Stock.particular_name==particular.particular_name,Stock.brand==particular.brand).first()
            
        pack_unit = particular.pack_unit

        st_num = ''
        st_unit = ''
        part_val = []
        for i in pack_unit:
            if i.isdigit():
                st_num += i
            elif i.isalpha():
                st_unit += i
        part_val.append(st_num)
        part_val.append(st_unit)


        if part_val[1] in ['g', 'ml','g/ml']:
            part_val[0] = int(part_val[0])
            part_val[1] = 'g/ml'
        elif part_val[1] in ['kg', 'l']:
            part_val[0] = int(part_val[0])*1000
            part_val[1] = 'g/ml'
        else:
            part_val[1] = 'nos'

        if part_val[1] == 'g/ml':
            stock_object.pack_amount= float(stock_object.pack_amount)-(float(part_val[0])*int(particular.quantity))
            stock_object.price = float(stock_object.price)-float(particular.price)
        elif part_val[1]=='nos':
            stock_object.pack_amount= int(stock_object.pack_amount)-(int(part_val[0])*int(particular.quantity))
            stock_object.price = float(stock_object.price)-float(particular.price)

        db.session.delete(particular)
        db.session.commit()
        msg = Message(
            'Delete on inventory',
            sender= os.environ.get('MAIL_NAME')
            recipients=['fameinfist@gmail.com']
        )

        msg.body = f'''The particular details that was deleted by {current_user.username}
                        is
                            1. date of purchase: {particular.date_purchase}
                            2. particular_name:  {particular.particular_name}
                            3. quantity: {particular.quantity}
                            4. price: {particular.price}
                            5. supplier: {particular.supplier}
                            6. Brand: {particular.brand}'''
        mail.send(msg)
        flash('Deleted Successfully', 'success')
        return redirect('/dashboard')

    elif page == 'indent':
        indent_object = Indent.query.get_or_404(id)
        db.session.delete(indent_object)
        db.session.commit()
        msg = Message(
            'Delete on inventory',
            sender=os.environ.get('MAIL_NAME'),  
            
            recipients=['fameinfist@gmail.com']
        )

        msg.body = f'''The particular details that was deleted by {current_user.username}
                        is
                            1. particular_name : {indent_object.particular_name}
                            2. quantity : {indent_object.quantity} 
                            3. department : {indent_object.department} 
                            4. Indent date : {indent_object.indent_dt} 
                            5. Lab or class : {indent_object.lab_or_class}'''
        mail.send(msg)
        flash('Deleted Successfully', 'success')
        return redirect('/indent')

    elif page == 'quotation':
        quotation_object = Quotation.query.get_or_404(id)
        db.session.delete(quotation_object)
        db.session.commit()
        flash('Deleted Successfully', 'success')
        return redirect('/quotation')

# issue return
@app.route('/update/<string:page>/<int:id>', methods=["GET", "POST"])
def update(page, id):
    if page == 'issued':
        particular = Issue.query.get_or_404(id)
        part_form = IssueForm()
        if request.method == 'GET':
            if not current_user.is_authenticated:
                flash('Please login.', 'danger')
                return redirect(url_for('login'))
            return render_template('edit.html',
                                   particular=particular,
                                   form=part_form,
                                   page=page)
        else:
            stock_object = Stock.query.filter(Stock.particular_name==particular.particular_name,Stock.brand==particular.brand).first()
                
            indent_object = Indent.query.filter_by(
                indent_no=particular.indent_no).first()
            pack_unit = indent_object.quantity
            id = indent_object.id

            indent_val = []
            st_num = ''
            st_unit = ''
            for i in pack_unit:
                if i.isdigit():
                    st_num += i
                elif i.isalpha():
                    st_unit += i
            indent_val.append(st_num)
            indent_val.append(st_unit)


            if indent_val[1] in ['g', 'ml','g/ml']:
                indent_val[0] = int(indent_val[0])
                indent_val[1] = 'g/ml'
            elif indent_val[1] in ['kg', 'l']:
                indent_val[0] = int(indent_val[0])*1000
                indent_val[1] = 'g/ml'
            else:
                indent_val[1] = 'nos'
            
            issue_val = []
            st_num = ''
            st_unit = ''
            for i in part_form.quantity.data.lower():
                if i.isdigit():
                    st_num += i
                elif i.isalpha():
                    st_unit += i
            issue_val.append(st_num)
            issue_val.append(st_unit)


            if issue_val[1] in ['g', 'ml','g/ml']:
                issue_val[0] = int(issue_val[0])
                issue_val[1] = 'g/ml'
            elif issue_val[1] in ['kg', 'l']:
                issue_val[0] = int(issue_val[0])*1000
                issue_val[1] = 'g/ml'
            else:
                issue_val[1] = 'nos'

            issue_val_og = []
            st_num = ''
            st_unit = ''
            for i in particular.quantity:
                if i.isdigit():
                    st_num += i
                elif i.isalpha():
                    st_unit += i
            issue_val_og.append(st_num)
            issue_val_og.append(st_unit)


            if issue_val_og[1] in ['g', 'ml','g/ml']:
                issue_val_og[0] = int(issue_val_og[0])
                issue_val_og[1] = 'g/ml'
            elif issue_val_og[1] in ['kg', 'l']:
                issue_val_og[0] = int(issue_val_og[0])*1000
                issue_val_og[1] = 'g/ml'
            else:
                issue_val_og[1] = 'nos'

            if int(issue_val[0])>int(issue_val_og[0]):
                flash("You cant update to a greater amount than value provided before", 'danger')
                return redirect(url_for('issue'))

            indent_change = Indent.query.get_or_404(id)
            indent_change.quantity = str(int(indent_val[0])+int(issue_val[0]))+indent_val[1]

            if stock_object:
                stock_id = stock_object.id
                pack_amount = stock_object.pack_amount
                unit = stock_object.unit
                stock_change = Stock.query.get_or_404(stock_id)
                stock_change.pack_amount = float(pack_amount)+float(issue_val[0])
            
            else:
                if issue_val_og[1]=='nos':
                    new_stock = Stock(
                        particular_name = particular.particular_name,
                        pack_amount = int(issue_val[0]),
                        price = particular.price,
                        brand = particular.brand,
                        unit = issue_val_og[1]
                    )
                else:
                    new_stock = Stock(
                        particular_name = particular.particular_name,
                        pack_amount = float(issue_val[0]),
                        price = particular.price,
                        brand = particular.brand,
                        unit = issue_val_og[1]
                    )
                db.session.add(new_stock)
            
            if issue_val_og[1]=='nos':
                particular.quantity = str(int(issue_val_og[0])-int(issue_val[0]))
            else:
                particular.quantity = str(float(issue_val_og[0])-float(issue_val[0]))+issue_val_og[1]

            db.session.commit()


            flash('Updated Successfully', 'success')
            return redirect('/issue')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    flash('You have logged out successfully', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    try:
        ui.run()
    except Exception as e:
        print(e)