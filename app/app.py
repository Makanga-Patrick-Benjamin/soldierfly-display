from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from passlib.hash import pbkdf2_sha256
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///larvae.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

class TrayData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tray_number = db.Column(db.Integer, nullable=False)
    metrics = db.Column(db.JSON)
    growth_data = db.Column(db.JSON)
    weight_distribution = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    tray_data = TrayData.query.order_by(TrayData.timestamp.desc()).first()
    return render_template('dashboard.html', timestamp=tray_data.timestamp if tray_data else None)

@app.route('/get_tray_data/<int:tray_number>')
@login_required
def get_tray_data(tray_number):
    tray_data = TrayData.query.filter_by(tray_number=tray_number).order_by(TrayData.timestamp.desc()).first()
    return jsonify({
        'metrics': tray_data.metrics,
        'growthData': tray_data.growth_data,
        'weightDistribution': tray_data.weight_distribution,
        'timestamp': tray_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }) if tray_data else jsonify({})

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.json
    new_entry = TrayData(
        tray_number=data['tray_number'],
        metrics=data['metrics'],
        growth_data=data['growth_data'],
        weight_distribution=data['weight_distribution']
    )
    db.session.add(new_entry)
    db.session.commit()
    return jsonify({"message": "Data received"}), 201

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)