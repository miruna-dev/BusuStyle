import os
import random
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheia-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///busustyle.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

genai.configure(api_key="AIzaSyB1guvxOyQavGQ6RvG74oRCQagyWYBgNN8")
model = genai.GenerativeModel('gemini-flash-latest')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150))

class ClothingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(50))
    color = db.Column(db.String(50))
    is_waterproof = db.Column(db.Boolean, default=False)
    season = db.Column(db.String(50))
    style = db.Column(db.String(50))
    is_favorite = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email deja existent.')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(email=email, password_hash=hashed_pw, first_name=first_name)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
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
    clothes = ClothingItem.query.filter_by(user_id=current_user.id).all()
    quote = {'text': 'Haina il face pe om.', 'author': 'Proverb', 'type': 'style'}
    return render_template('dashboard.html', clothes=clothes, quote=quote, user=current_user)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        color = request.form.get('color')
        season = request.form.get('season')
        style = request.form.get('style')
        
        file = request.files.get('image')
        filename = None

        if file and file.filename != '':
            filename = secure_filename(f"{current_user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_item = ClothingItem(
            user_id=current_user.id,
            category=category,
            subcategory=subcategory,
            color=color,
            season=season,
            style=style,
            image_filename=filename
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_item.html')

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = ClothingItem.query.get(item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    
    system_instruction = """
    Esti un asistent personal de stil numit BusuStyle. 
    Raspunzi DOAR la intrebari legate de moda, haine, stil, culori, outfit-uri si vreme.
    Daca utilizatorul intreaba despre vreme, ofera sfaturi vestimentare pentru vremea respectiva.
    Daca utilizatorul intreaba altceva, raspunde EXACT cu: 
    "Accept doar intrebari despre moda si vreme."
    Raspunde scurt si in limba romana.
    """
    
    try:
        full_prompt = f"{system_instruction}\n\nUser: {user_message}\nAssistant:"
        response = model.generate_content(full_prompt)
        return {'response': response.text}
    except Exception as e:
        print(e)
        return {'response': 'Eroare la conectare.'}

def generate_heuristic_outfit(clothes):
    tops = [c for c in clothes if c.category == 'Top']
    bottoms = [c for c in clothes if c.category == 'Bottom']
    shoes = [c for c in clothes if c.category == 'Incaltaminte']

    if not tops or not bottoms:
        return None

    best_outfit = None
    best_score = -1

    for _ in range(50):
        top = random.choice(tops)
        bottom = random.choice(bottoms)
        shoe = random.choice(shoes) if shoes else None

        current_score = 0

        if top.style == bottom.style:
            current_score += 10
        
        if top.season == bottom.season or top.season == 'Toate' or bottom.season == 'Toate':
            current_score += 5
            
        if shoe:
            if shoe.style == top.style:
                current_score += 5
            if shoe.color == top.color: 
                current_score += 3

        if current_score > best_score:
            best_score = current_score
            best_outfit = {
                'top': top,
                'bottom': bottom,
                'shoes': shoe,
                'score': best_score
            }

    return best_outfit

@app.route('/generator', methods=['GET', 'POST'])
@login_required
def generator():
    outfit = None
    if request.method == 'POST':
        user_clothes = ClothingItem.query.filter_by(user_id=current_user.id).all()
        outfit = generate_heuristic_outfit(user_clothes)
        
        if not outfit:
            flash('Nu ai suficiente haine.', 'warning')

    return render_template('generator.html', outfit=outfit)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)