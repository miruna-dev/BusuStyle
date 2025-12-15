import os
import random
import sqlite3
from database import init_db 
from flask import Flask, render_template, redirect, url_for, request, flash, session
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
import random

SCORE_THRESHOLDS = [3, 6, 10, 15, 20]
MAX_LEVEL = len(SCORE_THRESHOLDS) + 1
IMAGE_NAMES = [f"poza{i+1}.jpg" for i in range(MAX_LEVEL)]

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
PROCESSED_FOLDER = os.path.join(app.config["UPLOAD_FOLDER"], "processed")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(RAW_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(os.path.join("static", "defaults"), exist_ok=True)


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
    @property
    def folder(self):
        return "uploads/processed"

class Outfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    top_id = db.Column(db.Integer, db.ForeignKey("clothing_item.id"))
    bottom_id = db.Column(db.Integer, db.ForeignKey("clothing_item.id"))
    outerwear_id = db.Column(db.Integer, db.ForeignKey("clothing_item.id"))
    shoes_id = db.Column(db.Integer, db.ForeignKey("clothing_item.id"))
    accessories_id = db.Column(db.Integer, db.ForeignKey("clothing_item.id"))

    top = db.relationship("ClothingItem", foreign_keys=[top_id])
    bottom = db.relationship("ClothingItem", foreign_keys=[bottom_id])
    outerwear = db.relationship("ClothingItem", foreign_keys=[outerwear_id])
    shoes = db.relationship("ClothingItem", foreign_keys=[shoes_id])
    accessories = db.relationship("ClothingItem", foreign_keys=[accessories_id])

    created_at = db.Column(db.DateTime, server_default=db.func.now())


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
            "id": item.id,
            "filename": item.image_filename,
            "is_default": False,
            "folder": item.folder,
        }
    else:
        return {
            "id": None,
            "filename": default_filename,
            "is_default": True,
            "folder": "defaults",
        }


def generate_heuristic_outfit(clothes, weather=None):
    
    current_season = 'Primăvară'
    current_temp = 20
    is_rainy = False

    if weather and isinstance(weather, dict):
        current_temp = weather.get('temperature', 20)
        is_rainy = weather.get('is_rainy', False)
    
    if current_temp >= 25:
        current_season = 'Vară'
    elif current_temp >= 16 and current_temp <= 24:
        current_season = 'Primăvară'
    elif current_temp >= 6 and current_temp <= 15:
        current_season = 'Toamnă'
    else:
        current_season = 'Iarnă'

    def filter_items_with_fallback(category, clothes_list, required_season, required_rain_proof=False):
        is_accessory = (category == 'Accesorii')
        
        primary_filter = [
            c for c in clothes_list 
            if c.season == required_season and (
                is_accessory or
                not required_rain_proof or 
                c.is_waterproof
            )
        ]
        
        if primary_filter:
            return primary_filter
        else:
            return clothes_list

    all_tops = [c for c in clothes if c.category == "Top"]
    all_bottoms = [c for c in clothes if c.category == "Bottom"]
    all_outerwear = [c for c in clothes if c.category == "Outerwear"]
    all_shoes = [c for c in clothes if c.category == "Incaltaminte"]
    all_accessories = [c for c in clothes if c.category in ("Accesorii", "Accessory")]
    
    outerwear_needed = current_temp < 15 or is_rainy

    tops = filter_items_with_fallback("Top", all_tops, current_season)
    bottoms = filter_items_with_fallback("Bottom", all_bottoms, current_season)
    shoes = filter_items_with_fallback("Incaltaminte", all_shoes, current_season, is_rainy)
    accessories = filter_items_with_fallback("Accesorii", all_accessories, current_season, is_rainy)
    
    outerwear = []
    if outerwear_needed:
        outerwear = filter_items_with_fallback("Outerwear", all_outerwear, current_season, is_rainy)
    outfit = {
        "top": get_item_or_default(tops, "default_top.png"),
        "bottom": get_item_or_default(bottoms, "default_bottom.png"),
        "shoes": get_item_or_default(shoes, "default_shoes.png"),
        "accessories": get_item_or_default(accessories, "default_accessories.png"),
    }

    if outerwear_needed and outerwear:
        selected_outerwear = random.choice(outerwear)
        outfit["outerwear"] = {
            "id": selected_outerwear.id,
            "filename": selected_outerwear.image_filename,
            "is_default": False,
            "folder": selected_outerwear.folder
        }
    else:
        outfit["outerwear"] = {
            "id": None,
            "filename": "empty_outerwear.png",
            "is_default": True,
            "folder": "defaults"
        }
        
    return outfit


def item_to_dict(item):
    return {
        "id": item.id,
        "image_filename": item.image_filename or "",
        "category": item.category,
        "subcategory": item.subcategory or "",
        "is_favorite": item.is_favorite,
        "folder": item.folder,
    }


def get_current_game_state():
    if "game_score" not in session:
        session["game_score"] = 0
        session["item_zone"] = random.randint(1, 3)

    current_level = 1
    if session["game_score"] >= SCORE_THRESHOLDS[-1]:
        current_level = MAX_LEVEL
    else:
        for i, threshold in enumerate(SCORE_THRESHOLDS):
            if session["game_score"] >= threshold:
                current_level = i + 2
            else:
                break

    return {
        "score": session["game_score"],
        "level": current_level,
        "image": IMAGE_NAMES[current_level - 1],
        "item_zone": session["item_zone"],
        "is_game_over": current_level == MAX_LEVEL,
    }


@app.route("/minigame")
@login_required
def minigame_render():
    state = get_current_game_state()
    return render_template("python_game.html", state=state)


@app.route("/minigame_action/<int:zone_clicked>")
@login_required
def minigame_action(zone_clicked):
    state = get_current_game_state()

    if state["is_game_over"]:
        return redirect(url_for("minigame_render"))
    if zone_clicked == state["item_zone"]:
        session["game_score"] += 1
        session["item_zone"] = random.randint(1, 3)
    else:
        session["item_zone"] = random.randint(1, 3)

    session.modified = True
    return redirect(url_for("minigame_render"))


@app.route("/minigame_reset")
@login_required
def minigame_reset():
    session.pop("game_score", None)
    session.pop("item_zone", None)
    session.modified = True
    return redirect(url_for("minigame_render"))


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


@app.route("/dashboard")
@login_required
def dashboard():
    tab = request.args.get("tab", "closet")

    clothes = []
    outfits = []

    if tab == "loved":
        clothes = ClothingItem.query.filter_by(
            user_id=current_user.id, is_favorite=True
        ).all()

    elif tab == "outfits":
        outfits = Outfit.query.filter_by(user_id=current_user.id)\
                              .order_by(Outfit.created_at.desc())\
                              .all()

    else:
        clothes = ClothingItem.query.filter_by(user_id=current_user.id).all()

    quote = get_random_quote()
    weather = get_current_weather("Bucharest")

    return render_template(
        "dashboard.html",
        clothes=clothes,
        outfits=outfits,
        quote=quote,
        user=current_user,
        weather=weather,
        tab=tab,
    )
    
def get_random_quote():
    conn = None
    try:
        conn = sqlite3.connect('busustyle.db')
        cursor = conn.cursor()

        cursor.execute('SELECT text, author FROM DailyQuote')
        quotes = cursor.fetchall()
        
        if quotes:
            selected_quote_data = random.choice(quotes)
            return {"text": selected_quote_data[0], "author": selected_quote_data[1]}
        else:
            return {"text": "Alege un outfit care te inspiră!", "author": "BusuStyle"}

    except sqlite3.Error as e:
        print(f"Eroare SQLite la preluarea citatului: {e}")
        return {"text": "Eroare la baza de date.", "author": "Sistem"}
        
    finally:
        if conn:
            conn.close()


@app.route("/add_item", methods=["GET", "POST"])
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
        return redirect(url_for("dashboard"))

    return render_template("add_item.html")


@app.route("/toggle_favorite/<int:item_id>", methods=["POST"])
@login_required
def toggle_favorite(item_id):
    item = ClothingItem.query.get(item_id)
    if not item or item.user_id != current_user.id:
        return redirect(url_for("dashboard"))

    item.is_favorite = not item.is_favorite
    db.session.commit()

    tab = request.args.get("tab", "closet")
    return redirect(url_for("dashboard", tab=tab))


@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = ClothingItem.query.get(item_id)
    if item and item.user_id == current_user.id:
        if item.image_filename:
            processed_path = os.path.join(PROCESSED_FOLDER, item.image_filename)
            raw_path = os.path.join(RAW_FOLDER, item.image_filename.replace(".png", os.path.splitext(item.image_filename)[-1]))
            if os.path.exists(processed_path):
                os.remove(processed_path)
        db.session.delete(item)
        db.session.commit()
        
    tab = request.args.get("tab", "closet")
    return redirect(url_for("dashboard", tab=tab))

@app.route("/delete_outfit/<int:outfit_id>", methods=["POST"])
@login_required
def delete_outfit(outfit_id):
    outfit = Outfit.query.get(outfit_id)

    if not outfit or outfit.user_id != current_user.id:
        return redirect(url_for("dashboard", tab="outfits"))

    db.session.delete(outfit)
    db.session.commit()
    return redirect(url_for("dashboard", tab="outfits"))

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
    except Exception as e:
        if "Quota exceeded" in str(e):
            return {
                "response": "Am rămas fără energie AI azi :(( Revino mâine sau cere-mi un sfat clasic!"
            }
        return {"response": "Eroare AI."}


@app.route("/generator", methods=["GET", "POST"])
@login_required
def generator():
    placeholder_outfit = {
        "top": {"filename": "default_top.png", "folder": "defaults"},
        "bottom": {"filename": "default_bottom.png", "folder": "defaults"},
        "outerwear": {"filename": "default_outerwear.png", "folder": "defaults"},
        "shoes": {"filename": "default_shoes.png", "folder": "defaults"},
        "accessories": {"filename": "default_accessories.png", "folder": "defaults"},
    }

    outfit = placeholder_outfit
    is_post_request = False
    weather = get_current_weather("Bucharest")

    if request.method == "POST":
        user_clothes = ClothingItem.query.filter_by(user_id=current_user.id).all()
        outfit = generate_heuristic_outfit(user_clothes, weather)
        is_post_request = True

    return render_template(
        "generator.html", outfit=outfit, is_post_request=is_post_request, weather=weather
    )


@app.route("/showroom")
@login_required
def showroom():
    items = ClothingItem.query.filter_by(user_id=current_user.id).all()

    tops = [item_to_dict(i) for i in items if i.category == "Top"]
    bottoms = [item_to_dict(i) for i in items if i.category == "Bottom"]
    shoes = [item_to_dict(i) for i in items if i.category == "Incaltaminte"]
    outerwear = [item_to_dict(i) for i in items if i.category == "Outerwear"]
    accessories = [item_to_dict(i) for i in items if i.category in ("Accesorii", "Accessory")]


    return render_template(
        "showroom.html",
        tops=tops,
        bottoms=bottoms,
        shoes=shoes,
        outerwear=outerwear,
        accessories=accessories,
    )

@app.route("/save_outfit", methods=["POST"])
@login_required
def save_outfit():
    outfit = Outfit(
        user_id=current_user.id,
        top_id=request.form.get("top_id"),
        bottom_id=request.form.get("bottom_id"),
        outerwear_id=request.form.get("outerwear_id"),
        shoes_id=request.form.get("shoes_id"),
        accessories_id=request.form.get("accessories_id"),
    )

    db.session.add(outfit)
    db.session.commit()

    return redirect(url_for("dashboard", tab="outfits"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
        init_db() 
    app.run(debug=True)