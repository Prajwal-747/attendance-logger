import data
import students
from datetime import datetime

def take_attendance():
    student_list = data.load_students()
    if not student_list:
        print("No students found. Add students first.")
        return
    
    print("\nTaking attendance")
    class_date = input("Enter the date (DD/MM/YY): ")
    
    try:
        class_date = datetime.strptime(class_date, "%d/%m/%y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use DD/MM/YY.")
        return
    try:
        hour_no = int(input("Enter the hour number (1-6): "))
        if not 1 <= hour_no <= 6:
            print("Invalid hour number. Enter a number between 1 and 6.")
            return
    except ValueError:
        print("Hour must be an integer.")
        return
    
    print("Choose default attendance for all students(P/A): ")
    try:
        choice = input().strip().upper()
        if choice[0] == 'P':
            default_status = 'Present'
        elif choice[0] == 'A':
            default_status = 'Absent'
        else:
            print("Invalid Choice. Enter 'P' or 'A'.")
            return
    except IndexError:
        print("Invalid Choice. Enter 'P' or 'A'.")
        return
    
    attendance_list = [
        [roll_no, name, default_status] for roll_no, name in student_list
    ]    
    
    while True:
        print("\nAttendance List:")
        print("Roll No\tName\tStatus")
        for roll_no, name, status in attendance_list:
            print(f"{roll_no}\t{name}\t{status}")
        try:
            selected_roll_no = int(input("Enter roll number to change the status (0 to finish): "))
        except ValueError:
            print("Invalid input. Please enter a valid roll number.")
            continue
        
        if selected_roll_no == 0:
            break
        
        for student in attendance_list:
            if student[0] == selected_roll_no:
                if student[2] == 'Present':
                    student[2] = 'Absent'
                else:
                    student[2] = 'Present'
                break
        else:
            print("Roll number not found.")
            
    present_count = 0
    for student in attendance_list:
        if student[2] == 'Present':
            present_count += 1
            
    absent_count = len(attendance_list) - present_count
    
    print("\nATTENDANCE SUMMARY")
    print(f"Date: {class_date}, Hour: {hour_no}")
    print(f"Total Students: {len(attendance_list)}")
    print(f"Present: {present_count}")
    print(f"Absent: {absent_count}")
    
    print("Confirm attendance?(N is cancel) (Y/N): ")
    confirm = input().strip().upper()
    
    if confirm != 'Y':
        print("Attendance not confirmed.")
        return
        
    if data.mark_attendance_batch(attendance_list, class_date, hour_no):
        print("Attendance marked successfull")
    else:
        print("Attendance marking failed.")
        
def view_student_attendance():
    student = students.select_student()
    
    if student is None:
        return
    
    roll_no, name = student
    
    records = data.get_attendance_by_student(roll_no)
    
    if not records:
        print(f"No attendance records found for {name}.")
        return
    
    print("\nStudent Attendance History:")
    print(f"Name: {name}")
    print(f"Roll Number: {roll_no}")
    print("Date\tHour\tStatus")
    present_count = 0
    absent_count = 0
    
    for class_date, hour_no, status in records:
        print(f"{class_date}\t{hour_no}\t{status}")
        if status == "Present":
            present_count += 1
        else:
            absent_count += 1
    
    total = len(records)
    percentage = (present_count/total)*100
    
    print(f"\nTotal recorded classes: {total}")
    print(f"Present: {present_count}")
    print(f"Absent: {absent_count}")
    print(f"Attendance percentage: {percentage:.2f}%")
    
def view_session_attendance():
    print("\nView Session Attendance")
    class_date = input("Enter Date (DD/MM/YY): ").strip()
    try:
        class_date = datetime.strptime(class_date, "%d/%m/%y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return
    
    try:
        hour_no = int(input("Enter the hour number (1-6): "))
        if not 1 <= hour_no <= 6:
            print("Invalid hour number. Enter a number between 1 and 6.")
            return
    except ValueError:
        print("Hour must be an integer.")
        return
    
    records = data.get_attendance_by_session(class_date, hour_no)
    if not records:
        print("No attendance record found for this session")
        return
    
    print("\nSession Attendance")
    print(f"Date: {class_date}")
    print(f"Hour: {hour_no}")
    print("Roll Number\tName\tStatus")
    
    present_count = 0
    absent_count = 0
    
    for roll_no,name,status in records:
        print(f"{roll_no}\t{name}\t{status}")
        if status == "Present":
            present_count += 1
        else:
            absent_count += 1
            
    print(f"\nTotal Recorded: {len(records)}")
    print(f"Present: {present_count}")
    print(f"Absent: {absent_count}")
    
def view_absentees():
    print("\nView Absentees")
    class_date = input("Enter Date (DD/MM/YY): ").strip()
    try:
        class_date = datetime.strptime(class_date, "%d/%m/%y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return
    
    try:
        hour_no = int(input("Enter the hour number (1-6): "))
        if not 1 <= hour_no <= 6:
            print("Invalid hour number. Enter a number between 1 and 6.")
            return
    except ValueError:
        print("Hour must be an integer.")
        return
    
    absentees = data.get_absentees(class_date,hour_no)
    
    if not absentees:
        print("No absentees found")
        return
    
    print("\nAbsentee List:")
    print(f"Date: {class_date}")
    print(f"Hour: {hour_no}")
    print("Roll Number\tName")
    for roll_no, name in absentees:
        print(f"{roll_no}\t{name}")
        
    print(f"\nTotal absentees: {len(absentees)}")
        
def view_unmarked():
    print("\nView Unmarked Students")
    class_date = input("Enter Date (DD/MM/YY): ").strip()
    try:
        class_date = datetime.strptime(class_date, "%d/%m/%y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return
    
    try:
        hour_no = int(input("Enter the hour number (1-6): "))
        if not 1 <= hour_no <= 6:
            print("Invalid hour number. Enter a number between 1 and 6.")
            return
    except ValueError:
        print("Hour must be an integer.")
        return
    
    unmarked = data.get_unmarked(class_date,hour_no)
    
    if not unmarked:
        print("All students have been marked")
        return
    
    print("\nUnmarked Students List:")
    print(f"Date: {class_date}")
    print(f"Hour: {hour_no}")
    print("Roll Number\tName")
    for roll_no, name in unmarked:
        print(f"{roll_no}\t{name}")
        
    print(f"\nTotal Unmarked Students: {len(unmarked)}")

def edit_attendance():
    print("\nEdit Attendance")
    
    class_date = input("Enter Date (DD/MM/YY): ").strip()
    try:
        class_date = datetime.strptime(class_date, "%d/%m/%y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return
    
    try:
        hour_no = int(input("Enter the hour number (1-6): "))
        if not 1 <= hour_no <= 6:
            print("Invalid hour number. Enter a number between 1 and 6.")
            return
    except ValueError:
        print("Hour must be an integer.")
        return
    
    while True:
        records = data.get_attendance_by_session(class_date, hour_no)
        unmarked = data.get_unmarked(class_date, hour_no)
        
        if not records and not unmarked:
            print("No students found")
            return
        
        print("\nAttendance Session")
        print("Roll No.\tName\tStatus")
        for roll_no, name, status in records:
            print(f"{roll_no}\t{name}\t{status}")
        for roll_no, name in unmarked:
            print(f"{roll_no}\t{name}\tUnmarked")
            
        try:
            selected_roll_no = int(input("Enter roll number to edit (0 to finish): "))
        except ValueError:
            print("Invalid input. Please enter a valid roll number.")
            continue
    
        if selected_roll_no == 0:
            break
        
        current_status = None
        is_unmarked = False
    
        for student in records:
            if student[0] == selected_roll_no:
                current_status = student[2]
                break
        else:
            for student in unmarked:
                if student[0] == selected_roll_no:
                    is_unmarked = True
                    break
            else:
                print("Student not found")
                continue
        if is_unmarked:
            print("Current Status: Unmarked")
        else:
            print(f"Current Status: {current_status}")
            
        new_status = input("Enter new status (P/A): ").strip().upper()
        if new_status == 'P':
            new_status = "Present"
        elif new_status == 'A':
            new_status = "Absent"
        else:
            print("Invalid Status")
            continue
            
        if not is_unmarked and new_status == current_status:
            print("Attendance is already set to this status")
            continue
        
        if is_unmarked:
            success = data.mark_attendance(selected_roll_no, class_date, hour_no, new_status)
        else:
            success = data.update_attendance(selected_roll_no, class_date, hour_no, new_status)
        
        if success:
            print("Attendance updated successfully")
        else:
            print("Attendance update failed")
