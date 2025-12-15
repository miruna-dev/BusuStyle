import sqlite3

def init_db():
    conn = sqlite3.connect('busustyle.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ClothingItem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT,
            subcategory TEXT,
            color TEXT,
            is_waterproof INTEGER DEFAULT 0,
            material TEXT,
            warmth_resistance TEXT,
            wind_resistance TEXT,
            season TEXT,
            style TEXT,
            is_favorite INTEGER DEFAULT 0,
            image_filename TEXT,
            FOREIGN KEY (user_id) REFERENCES User (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DailyQuote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            author TEXT,
            type TEXT
        )
    ''')

    cursor.execute('SELECT count(*) FROM DailyQuote')
    if cursor.fetchone()[0] == 0:
        quotes = [
            ("Haina îl face pe om.", "Proverb", "general"),
            ("Simplitatea este nota adevăratei eleganțe.", "Coco Chanel", "fashion"),
            ("Moda trece, stilul rămâne.", "Yves Saint Laurent", "fashion"),
            ("Nu te îmbraci pentru alții, ci pentru tine.", "Anonim", "general"),
            ("O haină cumpărată, o șaorma irosită.", "Proverb din popor", "fashion"),
            ("Când Mercur e retrograd, nici geaca nu te mai avantajează.", "Neti Sandu", "horoscop"),
            ("Dacă plouă, nu e vreme rea, e doar o ținută greșită.", "Busu", "vreme"),
            ("Moda trece, dar frigul în oase rămâne.", "Proverb urban", "fashion"),
            ("O rochie bună nu ține de cald, dar ține de moral.", "Florin Stancu", "fashion"),
            ("Soarele îți luminează ziua, dar paltonul ți-o salvează.", "Mihaela Rădulescu", "vreme"),
            ("Când stelele tac, vorbește puloverul.", "Anonim astrologic", "horoscop"),
            ("Nu există vreme urâtă, doar outfit neinspirat.", "Coco Chanel (probabil)", "fashion"),
            ("Dacă e vânt, e clar: e timpul pentru layering.", "Busu", "fashion"),
            ("Zodia nu-ți alege stilul, dar ți-l poate strica.", "Neti Sandu", "horoscop"),
            ("O eșarfă bine aleasă bate orice prognoză.", "Dana Roba", "fashion"),
            ("Când plouă cu șanse, îmbracă-te cu speranță.", "Floricica Dansatoarea", "vreme"),
            ("Un trench bun valorează mai mult decât un horoscop favorabil.", "Anonim", "fashion"),
            ("Vara nu vine când vrei tu, ci când îți iei sandale.", "Busu", "vreme"),
            ("Dacă îți e frig, ascendentul e de vină.", "Vulpița sau Viorel", "horoscop"),
            ("Moda e ciclică, la fel și ploile.", "Karl Lagerfeld (în alt univers)", "fashion"),
            ("Când cerul e gri, scoate haina statement.", "Andreea Esca", "fashion"),
            ("Geaca groasă e cel mai sincer prieten al iernii.", "Proverb meteorologic", "vreme"),
            ("Dacă te îmbraci prea subțire, Universul nu te ajută.", "Neti Sandu", "vreme"),
            ("Eleganța dispare prima când bate vântul.", "Anonim", "fashion")
        ]
        cursor.executemany('INSERT INTO DailyQuote (text, author, type) VALUES (?, ?, ?)', quotes)

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()