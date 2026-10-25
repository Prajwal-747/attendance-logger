import sqlite3

def initialize_db():
    with sqlite3.connect("attendance.db") as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students_list (
                roll_no INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
    
def load_students():
    with sqlite3.connect("attendance.db") as connection:
        cursor = connection.execute(
            """SELECT roll_no, name FROM students_list"""
        )
        return cursor.fetchall()

def add_student(roll_no, name):
    try:
        with sqlite3.connect("attendance.db") as connection:
            cursor = connection.execute(
                """INSERT INTO students_list (roll_no, name) VALUES (?, ?)""",(roll_no,name)
            )
        return True
    except sqlite3.IntegrityError:
        return False

def search_student(roll_no):
    with sqlite3.connect("attendance.db") as connection:
        cursor = connection.execute(
            """SELECT roll_no, name FROM students_list WHERE roll_no = ?""", (roll_no,)
        )
        return cursor.fetchone()

def update_student(roll_no, new_name):
    with sqlite3.connect("attendance.db") as connection:
        cursor = connection.execute(
            "UPDATE students_list SET name = ? WHERE roll_no = ?", (new_name, roll_no)
        )
        return cursor.rowcount > 0

def remove_student(roll_no):
    with sqlite3.connect("attendance.db") as connection:
        cursor = connection.execute(
            "DELETE FROM students_list WHERE roll_no = ?", (roll_no,)
        )
        return cursor.rowcount > 0
