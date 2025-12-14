import os
import random
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import google.generativeai as genai
from rembg import remove
from PIL import Image
import io



app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheia-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///busustyle.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

RAW_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'raw')
os.makedirs(RAW_FOLDER, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

genai.configure(api_key="PUNE_CHEIA_TA_AICI")
model = genai.GenerativeModel('gemini-1.5-flash')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))

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

def remove_background_and_save(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGBA")
            output = remove(img)
            output.save(output_path, format="PNG")
        return True
    except Exception as e:
        print(f"Eroare remove background: {e}")
        return False

def generate_heuristic_outfit(clothes):
    tops = [c for c in clothes if c.category == 'Top']
    bottoms = [c for c in clothes if c.category == 'Bottom']
    shoes = [c for c in clothes if c.category == 'Incaltaminte']

    warnings = []
    
    if tops:
        selected_top = random.choice(tops)
    else:
        selected_top = {
            'image_filename': 'default_top.png', 
            'subcategory': 'Top Default', 'color': 'Neutru', 'style': 'Casual', 'is_default': True
        }
        warnings.append("Lipsa Top.")

    if bottoms:
        selected_bottom = random.choice(bottoms)
    else:
        selected_bottom = {
            'image_filename': 'default_bottom.png',
            'subcategory': 'Pantaloni Default', 'color': 'Neutru', 'style': 'Casual', 'is_default': True
        }
        warnings.append("Lipsa Pantaloni.")

    if shoes:
        selected_shoe = random.choice(shoes)
    else:
        selected_shoe = {
            'image_filename': 'default_shoes.png',
            'subcategory': 'Pantofi Default', 'color': 'Neutru', 'style': 'Casual', 'is_default': True
        }

    score = 10
    return {
        'top': selected_top,
        'bottom': selected_bottom,
        'shoes': selected_shoe,
        'score': score,
        'warnings': warnings
    }

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
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email deja existent.')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(email=email, password_hash=hashed_pw, first_name=first_name, last_name=last_name)
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
    weather = get_current_weather("Bucharest")
    return render_template('dashboard.html', clothes=clothes, quote=quote, user=current_user, weather=weather)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        color = request.form.get('color')
        season = request.form.get('season')
        style = request.form.get('style')
        is_favorite = True if request.form.get('is_favorite') else False
        is_waterproof = True if request.form.get('is_waterproof') else False
        
        file = request.files.get('image')
        filename = None

        if file and file.filename != '':
            base_name = secure_filename(f"{current_user.id}_{file.filename}")
            raw_path = os.path.join(RAW_FOLDER, base_name)
            file.save(raw_path)

            processed_filename = os.path.splitext(base_name)[0] + ".png"
            processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            
            success = remove_background_and_save(raw_path, processed_path)
            
            if success:
                filename = processed_filename
            else:
                final_path = os.path.join(app.config['UPLOAD_FOLDER'], base_name)
                with open(raw_path, 'rb') as f_in:
                    with open(final_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                filename = base_name

        new_item = ClothingItem(
            user_id=current_user.id,
            category=category,
            subcategory=subcategory,
            color=color,
            season=season,
            style=style,
            image_filename=filename,
            is_favorite=is_favorite,
            is_waterproof=is_waterproof
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
    
    system_instruction = "Esti BusuStyle. Raspunzi scurt despre moda si vreme."
    
    try:
        full_prompt = f"{system_instruction}\n\nUser: {user_message}\nAssistant:"
        response = model.generate_content(full_prompt)
        return {'response': response.text}
    except Exception as e:
        return {'response': 'Eroare la conectare AI.'}

@app.route('/generator', methods=['GET', 'POST'])
@login_required
def generator():
    outfit = None
    if request.method == 'POST':
        user_clothes = ClothingItem.query.filter_by(user_id=current_user.id).all()
        outfit = generate_heuristic_outfit(user_clothes)
    return render_template('generator.html', outfit=outfit)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)