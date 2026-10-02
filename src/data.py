import csv

students_list = "./Students_List.csv"
attendance_list = "./Attendance_List.csv"

def load_students():
    with open(students_list, 'r') as f:
        reader = csv.reader(f)
        fields = next(reader)
        rows = list(reader)

        return fields, rows

def add_student(student):
    roll_number = student[0]
    if search_student(roll_number) is not None:
        print("Student Added")
    with open(students_list, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(student)
    print("Roll number exists")

def search_student(roll_number):
    fields, students = load_students()
    for student in students:
        if student[0] == str(roll_number):
            return student
    return None

def update_student(roll_number, new_name):
    fields, students = load_students()
    for student in students:
        if student[0] == str(roll_number):
            student[1] = new_name
            break
    with open(students_list, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(students)

def remove_student(roll_number):
    fields, students = load_students()
    for student in students:
        if student[0] == str(roll_number):
            students.remove(student)
            break
    with open(students_list, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(students)
