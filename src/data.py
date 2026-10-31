from contextlib import closing
import sqlite3
    
def get_connection()-> sqlite3.Connection:
    connection = sqlite3.connect("attendance.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def initialize_db()-> None:
    with closing(get_connection()) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS students_list (
                    roll_no INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    roll_no INTEGER NOT NULL,
                    class_date TEXT NOT NULL,
                    hour_no INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('Present','Absent')),
                    PRIMARY KEY (roll_no, class_date, hour_no),
                    FOREIGN KEY (roll_no) REFERENCES students_list (roll_no)
                )
                """
            )

def load_students()-> list:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """SELECT roll_no, name FROM students_list"""
        )
        return cursor.fetchall()

def add_student(roll_no: int, name: str)-> bool:
    try:
        with closing(get_connection()) as connection:
            with connection:
                connection.execute(
                    """INSERT INTO students_list (roll_no, name) VALUES (?, ?)""",(roll_no,name)
                )
        return True
    except sqlite3.IntegrityError:
        return False

def search_student_by_roll_no(roll_no: int)-> tuple | None:    
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """SELECT roll_no, name FROM students_list WHERE roll_no = ?""", (roll_no,)
        )
        return cursor.fetchone()

def search_student_by_name(name: str)-> list:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT roll_no, name
            FROM students_list
            WHERE name LIKE ?
            """, (f"%{name}%",)
        )
        return cursor.fetchall()
    
def update_student(roll_no: int, new_name: str)-> bool:
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE students_list SET name = ? WHERE roll_no = ?", (new_name, roll_no)
            )
            return cursor.rowcount > 0

def remove_student(roll_no: int)-> bool:
    try:
        with closing(get_connection()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM students_list WHERE roll_no = ?", (roll_no,)
            )
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False

def mark_attendance(roll_no: int, class_date: str, hour_no: int, status:str)-> bool:
    if (status not in ['Present', 'Absent']):
        return False
    try:
        with closing(get_connection()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO attendance (roll_no, class_date, hour_no, status) 
                    VALUES (?, ?, ?, ?)
                    """, (roll_no, class_date, hour_no, status)
                )
        return True
    except sqlite3.IntegrityError:
        return False
    
def get_absentees(class_date:str, hour_no: int)-> list:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT s.roll_no, s.name
            FROM students_list s
            LEFT JOIN attendance a ON s.roll_no = a.roll_no AND a.class_date = ? AND a.hour_no = ?
            WHERE a.status = 'Absent'
            """, (class_date, hour_no)
        )
        return cursor.fetchall()
    
def get_unmarked(class_date:str, hour_no: int)-> list:
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            SELECT s.roll_no, s.name
            FROM students_list s
            LEFT JOIN attendance a ON s.roll_no = a.roll_no AND a.class_date = ? AND a.hour_no = ?
            WHERE a.status IS NULL
            """, (class_date, hour_no)
        )
        return cursor.fetchall()
    
def update_attendance(roll_no: int, class_date: str, hour_no: int, new_status: str)-> bool:
    if (new_status not in ['Present', 'Absent']):
        return False
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                """
                UPDATE attendance
                set status = ?
                WHERE roll_no = ? AND class_date = ? AND hour_no = ?
                """, (new_status, roll_no, class_date, hour_no)
            )
            return cursor.rowcount > 0
