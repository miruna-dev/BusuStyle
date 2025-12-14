import os
import random
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import google.generativeai as genai
from rembg import remove
from PIL import Image

try:
    from weather import get_current_weather
except ImportError:
    def get_current_weather(city):
        return None


app = Flask(__name__)

app.config["SECRET_KEY"] = "cheia-secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///busustyle_v2.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"

RAW_FOLDER = os.path.join(app.config["UPLOAD_FOLDER"], "raw")
PROCESSED_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'processed')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(RAW_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(os.path.join('static', 'defaults'), exist_ok=True)


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

genai.configure(api_key="AIzaSyB1guvxOyQavGQ6RvG74oRCQagyWYBgNN8")
model = genai.GenerativeModel("gemini-flash-latest")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))


class ClothingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(50))
    color = db.Column(db.String(50))
    is_waterproof = db.Column(db.Boolean, default=False)
    season = db.Column(db.String(50))
    style = db.Column(db.String(50))
    is_favorite = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(100))


with app.app_context():
    db.create_all()


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
    except Exception:
        return False


def get_item_or_default(items_list, default_filename):
    if items_list:
        item = random.choice(items_list)
        return {
            'filename': item.image_filename,
            'is_default': False,
            'folder': 'uploads/processed'
        }
    else:
        return {
            'filename': default_filename,
            'is_default': True,
            'folder': 'defaults'
        }


def generate_heuristic_outfit(clothes):
    tops = [c for c in clothes if c.category == 'Top']
    bottoms = [c for c in clothes if c.category == 'Bottom']
    outerwear = [c for c in clothes if c.category == 'Outerwear']
    shoes = [c for c in clothes if c.category == 'Incaltaminte']
    accessories = [c for c in clothes if c.category == 'Accesorii']

    return {
        'top': get_item_or_default(tops, 'default_top.png'),
        'bottom': get_item_or_default(bottoms, 'default_bottom.png'),
        'outerwear': get_item_or_default(outerwear, 'default_outerwear.png'),
        'shoes': get_item_or_default(shoes, 'default_shoes.png'),
        'accessories': get_item_or_default(accessories, 'default_accessories.png')
    }


def item_to_dict(item):
    return {
        "id": item.id,
        "image_filename": item.image_filename,
        "category": item.category,
        "subcategory": item.subcategory,
        "is_favorite": item.is_favorite
    }


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        if not email or not password:
            flash("Completeaza toate campurile.")
            return redirect(url_for("register"))

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email deja existent.")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(
            email=email,
            password_hash=hashed_pw,
            first_name=first_name,
            last_name=last_name,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            flash("Eroare la inregistrare.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Date incorecte.")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route('/dashboard')
@login_required
def dashboard():
    tab = request.args.get('tab', 'closet')

    if tab == 'loved':
        clothes = ClothingItem.query.filter_by(
            user_id=current_user.id,
            is_favorite=True
        ).all()
    else:
        clothes = ClothingItem.query.filter_by(
            user_id=current_user.id
        ).all()

    quote = {'text': 'Haina îl face pe om.', 'author': 'Proverb'}
    weather = get_current_weather("Bucharest")

    return render_template(
        'dashboard.html',
        clothes=clothes,
        quote=quote,
        user=current_user,
        weather=weather,
        tab=tab
    )


@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == "POST":
        category = request.form.get("category")
        subcategory = request.form.get("subcategory")
        color = request.form.get("color")
        season = request.form.get("season")
        style = request.form.get("style")
        is_favorite = True if request.form.get("is_favorite") else False
        is_waterproof = True if request.form.get("is_waterproof") else False

        file = request.files.get("image")
        filename = None

        if file and file.filename != "":
            base_name = secure_filename(f"{current_user.id}_{file.filename}")

            raw_path = os.path.join(RAW_FOLDER, base_name)
            file.save(raw_path)

            processed_filename = os.path.splitext(base_name)[0] + ".png"
            processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)

            success = remove_background_and_save(raw_path, processed_path)

            if success:
                filename = processed_filename
            else:
                try:
                    with Image.open(raw_path) as img:
                        img = img.convert("RGBA")
                        img.save(processed_path, format="PNG")
                    filename = processed_filename
                except Exception:
                    filename = None 


        new_item = ClothingItem(
            user_id=current_user.id,
            category=category,
            subcategory=subcategory,
            color=color,
            season=season,
            style=style,
            image_filename=filename,  
            is_favorite=is_favorite,
            is_waterproof=is_waterproof,
        )

        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_item.html')


@app.route('/toggle_favorite/<int:item_id>', methods=['POST'])
@login_required
def toggle_favorite(item_id):
    item = ClothingItem.query.get(item_id)
    if not item or item.user_id != current_user.id:
        return redirect(url_for('dashboard'))

    item.is_favorite = not item.is_favorite
    db.session.commit()

    tab = request.args.get('tab', 'closet')
    return redirect(url_for('dashboard', tab=tab))


@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = ClothingItem.query.get(item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")

    system_instruction = """Esti BusuStyle, un asistent personal de stil si moda.
Rolul tau este sa ajuti utilizatorul cu sfaturi despre haine, asortare si cum sa se imbrace in functie de vreme.

REGULI IMPORTANTE:
1. Raspunzi DOAR la intrebari legate de moda, haine, stil, culori si vreme.
2. Daca utilizatorul te intreaba despre ORICE altceva (matematica, politica, istorie, glume, etc.), refuza politicos si raspunde exact cu fraza: "Imi pare rau, eu ma pricep doar la moda si vreme. Te pot ajuta cu un sfat vestimentar?"
3. Fii scurt, prietenos si la obiect."""

    try:
        full_prompt = f"{system_instruction}\n\nUser: {user_message}\nAssistant:"
        response = model.generate_content(full_prompt)
        return {"response": response.text}
    except Exception:
        return {"response": "Eroare la conectare AI."}


@app.route('/generator', methods=['GET', 'POST'])
@login_required
def generator():
    placeholder_outfit = {
        'top': {'filename': 'default_top.png', 'folder': 'defaults'},
        'bottom': {'filename': 'default_bottom.png', 'folder': 'defaults'},
        'outerwear': {'filename': 'default_outerwear.png', 'folder': 'defaults'},
        'shoes': {'filename': 'default_shoes.png', 'folder': 'defaults'},
        'accessories': {'filename': 'default_accessories.png', 'folder': 'defaults'}
    }
    
    outfit = placeholder_outfit
    
    if request.method == 'POST':
        user_clothes = ClothingItem.query.filter_by(user_id=current_user.id).all()
        outfit = generate_heuristic_outfit(user_clothes)
        
    return render_template('generator.html', outfit=outfit)


@app.route('/showroom')
@login_required
def showroom():
    items = ClothingItem.query.filter_by(user_id=current_user.id).all()

    tops = [item_to_dict(i) for i in items if i.category == 'Top']
    bottoms = [item_to_dict(i) for i in items if i.category == 'Bottom']
    shoes = [item_to_dict(i) for i in items if i.category == 'Incaltaminte']
    outerwear = [item_to_dict(i) for i in items if i.category == 'Outerwear']
    accessories = [item_to_dict(i) for i in items if i.category == 'Accesorii']

    return render_template(
        'showroom.html',
        tops=tops,
        bottoms=bottoms,
        shoes=shoes,
        outerwear=outerwear,     
        accessories=accessories
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
    app.run(debug=True)