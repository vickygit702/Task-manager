from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = '12345'

# MongoDB Atlas URI
app.config['MONGO_URI'] = "mongodb+srv://vignesh:2KhpYXpmb2kLNcxu@task-manager.sts8ofg.mongodb.net/taskdb?retryWrites=true&w=majority"

mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# --- User class for Flask-Login ---
class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.username = user_doc['username']

@login_manager.user_loader
def load_user(user_id):
    user_doc = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_doc) if user_doc else None

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if mongo.db.users.find_one({'username': username}):
            flash("Username already exists")
            return redirect(url_for('register'))

        password = generate_password_hash(request.form['password'])
        mongo.db.users.insert_one({'username': username, 'password': password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({'username': request.form['username']})
        if user and check_password_hash(user['password'], request.form['password']):
            login_user(User(user))
            return redirect(url_for('dashboard'))
        flash("Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    tasks = mongo.db.tasks.find({'user_id': current_user.id})
    return render_template('dashboard.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        task = {
            'content': request.form['content'],
            'deadline': datetime.strptime(request.form['deadline'], '%Y-%m-%d'),
            'status': 'Pending',
            'user_id': current_user.id
        }
        mongo.db.tasks.insert_one(task)
        return redirect(url_for('dashboard'))
    return render_template('add_task.html')

@app.route('/complete/<task_id>')
@login_required
def complete(task_id):
    mongo.db.tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {'status': 'Completed'}})
    return redirect(url_for('dashboard'))

@app.route('/delete/<task_id>')
@login_required
def delete(task_id):
    mongo.db.tasks.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)