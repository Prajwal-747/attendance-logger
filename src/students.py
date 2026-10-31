import data

def list_students()-> None:
    students = data.load_students()
    if not students:
        print("No students found.")
        return
    print("List of Students:")
    print("-----------------")
    print("Roll No\tName")
    for roll_no, name in students:
        print(f"{roll_no}\t{name}")
        
def add_student():
    try:
        roll_no = int(input("Enter Roll Number: "))
    except ValueError:
        print("Roll number must be an integer.")
        return
    name = input("Enter Name: ").strip()
    
    if not name:
        print("Name cannot be empty.")
        return
    
    if data.add_student(roll_no, name):
        print(f"Student {name} with Roll Number {roll_no} added successfully.")
    else:
        print(f"Could not add student. Roll Number {roll_no} may already exist.")
        
def select_student():
    print("Find Student")
    print("1. Search by Roll Number")
    print("2. Search by Name")
    choice = input("Enter your choice: ").strip()
    if choice == "1":
        try:
            roll_no = int(input("Enter Roll Number: "))
        except ValueError:
            print("Roll number must be an integer.")
            return None
        
        student = data.search_student_by_roll_no(roll_no)
        
        if student:
            print(f"Roll No: {student[0]}")
            print(f"Name: {student[1]}")
            return student
        
        print(f"Student not found with Roll Number {roll_no}")
        return None
    
    elif choice == "2":
        name = input("Enter Name: ").strip()
        
        if not name:
            print("Name cannot be empty.")
            return None
        
        students = data.search_student_by_name(name)
        
        if not students:
            print("No matching students found.")
            return None
        
        print("Matching Students:")
        print("------------------")
        print("Roll No\tName")
        for roll_no, name in students:
            print(f"{roll_no}\t{name}")
            
        try:
            selected_roll_no = int(input("Enter the Roll Number of the student to select: "))
        except ValueError:
            print("Roll number must be an integer.")
            return None
        for student in students:
            if student[0] == selected_roll_no:
                return student
        print("Invalid selection")
        return None
    else:
        print("Invalid choice")
        return None

def search_student():
    student = select_student()
    
    if student is None:
        return
    
    roll_no, name = student  
    print("Student Found:")
    print("------------------")
    print(f"Roll No: {roll_no}")
    print(f"Name: {name }")

def update_student():
    student = select_student()
    
    if student is None:
        return
    
    roll_no, name = student
    print(f"Current Name: {name}")
    new_name = input("Enter new name: ").strip()
    
    if not new_name:
        print("Name cannot be empty.")
        return
    if data.update_student(roll_no, new_name):
        print(f"Student with Roll Number {roll_no} updated successfully.")
    else:
        print(f"Could not update student")


def remove_student():
    student = select_student()
    
    if student is None:
        return
    
    roll_no, name = student
    print("Student selected for deletion:")
    print("------------------------------")
    print(f"Roll No: {roll_no}")
    print(f"Name: {name }")
    
    confirm = input("Are your sure you want to delete this student? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Deletion cancelled.")
        return
    
    if data.remove_student(roll_no):
        print(f"Student with Roll Number {roll_no} deleted successfully.")
    else:
        print(f"Could not delete student. They may have existing attendance records.")