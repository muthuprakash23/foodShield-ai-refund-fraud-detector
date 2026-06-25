import sqlite3
import os


DB_PATH = os.path.join(os.path.dirname(__file__), "fraud_detector.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def seed_database():
    conn = get_connection()
    cursor = conn.cursor()
   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            account_age_days INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            food_item TEXT NOT NULL,
            order_date TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
  
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            refund_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            refund_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """)

    users = [
        ("USR001", "Muthu Prakash", "muthu@example.com", 365),
        ("USR002", "Ravi Kumar",    "ravi@example.com",  180),
        ("USR003", "Priya Nair",    "priya@example.com", 730),
        ("USR004", "Fraud User",    "fraud@example.com", 90),
        ("USR005", "New User",      "new@example.com",   5),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO users (user_id, name, email, account_age_days)
        VALUES (?, ?, ?, ?)
    """, users)

    
    orders = [
        
        ("ORD001", "USR001", "Biryani",        "2026-05-01", 250.0),
        ("ORD002", "USR001", "Dosa",           "2026-05-05", 120.0),
        ("ORD003", "USR001", "Burger",         "2026-05-10", 180.0),
        ("ORD004", "USR001", "Pasta",          "2026-05-15", 220.0),
        ("ORD005", "USR001", "Noodles",        "2026-05-20", 150.0),
        ("ORD006", "USR001", "Pizza",          "2026-05-25", 300.0),
        ("ORD007", "USR001", "Idli",           "2026-06-01", 90.0),
        ("ORD008", "USR001", "Fried Rice",     "2026-06-05", 160.0),
        ("ORD009", "USR001", "Sandwich",       "2026-06-10", 130.0),
        ("ORD010", "USR001", "Biryani",        "2026-06-15", 250.0),

        
        ("ORD011", "USR002", "Pizza",          "2026-05-10", 300.0),
        ("ORD011", "USR002", "Burger",         "2026-05-20", 180.0),
        ("ORD012", "USR002", "Burger",         "2026-05-20", 180.0),
        ("ORD013", "USR002", "Biryani",        "2026-06-01", 250.0),
        ("ORD014", "USR002", "Dosa",           "2026-06-10", 120.0),
        ("ORD015", "USR002", "Noodles",        "2026-06-15", 150.0),

       
        ("ORD016", "USR003", "Pasta",          "2026-04-01", 220.0),
        ("ORD017", "USR003", "Pizza",          "2026-04-10", 300.0),
        ("ORD018", "USR003", "Biryani",        "2026-04-20", 250.0),
        ("ORD019", "USR003", "Sandwich",       "2026-05-01", 130.0),
        ("ORD020", "USR003", "Burger",         "2026-05-10", 180.0),
        ("ORD021", "USR003", "Fried Rice",     "2026-05-20", 160.0),
        ("ORD022", "USR003", "Idli",           "2026-06-01", 90.0),
        ("ORD023", "USR003", "Dosa",           "2026-06-15", 120.0),

        
        ("ORD024", "USR004", "Biryani",        "2026-06-01", 250.0),
        ("ORD025", "USR004", "Pizza",          "2026-06-03", 300.0),
        ("ORD026", "USR004", "Burger",         "2026-06-05", 180.0),
        ("ORD027", "USR004", "Noodles",        "2026-06-08", 150.0),
        ("ORD028", "USR004", "Dosa",           "2026-06-10", 120.0),
        ("ORD029", "USR004", "Pasta",          "2026-06-15", 220.0),

        ("ORD032", "USR005", "Burger,pizza,biryani",         "2026-06-20", 570.0),
        
        ("ORD033", "USR003", "Burger,pizza,biryani,dosa",         "2026-06-20", 570.0),
        ("ORD030", "USR005", "Burger",         "2026-06-20", 180.0),
        ("ORD031", "USR005", "Pizza",          "2026-06-22", 300.0),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO orders (order_id, user_id, food_item, order_date, amount)
        VALUES (?, ?, ?, ?, ?)
    """, orders)

    
    refunds = [
      
        ("REF001", "USR001", "ORD010", "Hair in food",      "2026-06-15"),

        
        ("REF002", "USR002", "ORD013", "Wrong order",       "2026-06-01"),
        ("REF003", "USR002", "ORD015", "Insect in food",    "2026-06-15"),

        ("REF004", "USR004", "ORD024", "Hair in food",      "2026-06-01"),
        ("REF005", "USR004", "ORD025", "Insect in food",    "2026-06-03"),
        ("REF006", "USR004", "ORD026", "Wrong order",       "2026-06-05"),
        ("REF007", "USR004", "ORD027", "Hair in food",      "2026-06-08"),
        ("REF008", "USR004", "ORD028", "Food not delivered", "2026-06-10"),

        ("REF009", "USR005", "ORD030", "Insect in food",    "2026-06-20"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO refunds (refund_id, user_id, order_id, reason, refund_date)
        VALUES (?, ?, ?, ?, ?)
    """, refunds)

    conn.commit()
    conn.close()
    print("Database seeded successfully.")
    print(f"DB location: {DB_PATH}")


if __name__ == "__main__":
    seed_database()