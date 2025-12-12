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
            ("Nu te îmbraci pentru alții, ci pentru tine.", "Anonim", "general")
        ]
        cursor.executemany('INSERT INTO DailyQuote (text, author, type) VALUES (?, ?, ?)', quotes)

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()