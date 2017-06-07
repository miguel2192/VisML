#################################################################
# Author: Miguel Rodriguez
# Technologies: Python, Flask, Bootstrap etc
# Copyright, Miguel, all rights reserved.
#################################################################



from flask import Flask, render_template, url_for, redirect, request, make_response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
# from flask.ext.sqlalchemy import SQLAlchemy
import pdfkit
import flask_whooshalchemy as wa

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s/cms.db' % os.getcwd()
#####
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['WHOOSH_BASE'] = 'whoosh'
###
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password =db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm): 
    name = StringField('name', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    #checks if the form is been submitted
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
        return render_template('invalid.html')
        # return '<h1>' + form.username.data + ' ' +  form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    form = RegisterForm()

    # checks if the form is been submitted
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(name=form.name.data, username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return render_template('new-user.html')
        # return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'


    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    pages = db.session.query(Pages).all()
    return render_template('dashboard.html', pages=pages, name=current_user.name)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#######################################################################################################################

# SQLAlchemy models
class Pages(db.Model):
    __tablename__ = 'pages'
    ####
    __searchable__= ['title']
    ####

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000))
    description = db.Column(db.String(1000))
    content = db.Column(db.BLOB)
    date = db.Column(db.String(1000))

    def __init__(self, title, description, content, date):
        self.title = title
        self.description = description
        self.content = content
        self.date = date

    def __repr__(self):
        return '<Pages : id=%r, title=%s, description=%s, content=%s>, date=%s>' \
              % (self.id, self.title, self.description, self.content, self.date)


###########################################################################################
wa.whoosh_index(app, Pages)

@app.route('/search')
@login_required
def search():
    pages = Pages.query.whoosh_search(request.args.get('query')).all()

    return render_template('dashboard.html', pages=pages)
# app views
# @app.route('/dashboard')
# def index():
#     pages = db.session.query(Pages).all()
#     return render_template('dashboard.html', pages=pages)

@app.route('/generate/')
@login_required
def generate():
    pages = db.session.query(Pages).all()
    rendered =  render_template('generate.html',
                                    pages=pages, name=current_user.name)
    pdf = pdfkit.from_string(rendered, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=journal.pdf'

    return response

####################################################################################################################
@app.route('/generate-page/<int:page_id>')
@login_required
def generate_page(page_id):
    page = db.session.query(Pages).filter_by(id=page_id).first()
    rendered = render_template('page.html', 
                           id=page.id, title=page.title, description=page.description, content=page.content, date=page.date)

    pdf = pdfkit.from_string(rendered, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=journal-page.pdf'

    return response



####################################################################################################################
@app.route('/page/<int:page_id>')
@login_required
def view_page(page_id):
    page = db.session.query(Pages).filter_by(id=page_id).first()
    return render_template('page.html', 
                            id=page.id, title=page.title, description=page.description, content=page.content, date=page.date)

@app.route('/edit-page/<int:page_id>')
@login_required
def edit_page(page_id):
    page = db.session.query(Pages).filter_by(id=page_id).first()
    return render_template('edit-page.html', 
                           id=page.id, title=page.title, description=page.description, content=page.content, date=page.date)


@app.route('/update-page/', methods=['POST'])
@login_required
def update_page():
    page_id = request.form['id']
    title = request.form['title']
    description = request.form['description']
    content = request.form['content']
    date = request.form['date']
    db.session.query(Pages).filter_by(id=page_id).update({'title': title,
                                                          'description': description,  
                                                          'content': content,
                                                          'date': date})
    db.session.commit()
    return redirect('/page/'+page_id)

@app.route('/new-page/')
@login_required
def new_page():
    return render_template('new-page.html')

@app.route('/save-page/', methods=['POST'])
@login_required
def save_page():
    page = Pages(title=request.form['title'],
                 description=request.form['description'],
                 content=request.form['content'],
                 date=request.form['date'])
    db.session.add(page)
    db.session.commit()
    return redirect('dashboard')

@app.route('/delete-page/<int:page_id>')
@login_required
def delete_page(page_id):
    db.session.query(Pages).filter_by(id=page_id).delete()
    db.session.commit()
    return redirect('dashboard')
    
if __name__ == '__main__':
    app.run(port=3000)