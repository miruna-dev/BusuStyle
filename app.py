import os
import sqlite3
from flask import Flask, render_template, redirect, url_for, g, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user
from weather import get_current_weather


app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheie-secreta-proiect'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('busustyle.db')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, first_name, last_name):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM User WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(
            user['id'],
            user['email'],
            user['first_name'],
            user['last_name']
        )
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM User WHERE email = ?',
            (email,)
        ).fetchone()

        if user:
            flash('Email deja existent.')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='scrypt')

        conn.execute(
            'INSERT INTO User (email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?)',
            (email, hashed_pw, first_name, last_name)
        )
        conn.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db()
        user_data = conn.execute('SELECT * FROM User WHERE email = ?', (email,)).fetchone()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user_obj = User(
                user_data['id'],
                user_data['email'],
                user_data['first_name'],
                user_data['last_name']
            )
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('Date incorecte.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()

    clothes = conn.execute(
        'SELECT * FROM ClothingItem WHERE user_id = ?',
        (current_user.id,)
    ).fetchall()

    quote = conn.execute(
        'SELECT * FROM DailyQuote ORDER BY RANDOM() LIMIT 1'
    ).fetchone()

    weather = get_current_weather("Bucharest")

    tab = request.args.get("tab", "closet")

    return render_template(
        'dashboard.html',
        clothes=clothes,
        quote=quote,
        weather=weather,
        tab=tab,
        user=current_user
    )

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        file = request.files.get('image')
        filename = None
        
        if file and file.filename != '':
            filename = secure_filename(f"{current_user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        conn = get_db()
        conn.execute('INSERT INTO ClothingItem (user_id, category, subcategory, image_filename) VALUES (?, ?, ?, ?)',
                     (current_user.id, category, subcategory, filename))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_item.html')

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    conn = get_db()
    conn.execute('DELETE FROM ClothingItem WHERE id = ? AND user_id = ?', (item_id, current_user.id))
    conn.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)