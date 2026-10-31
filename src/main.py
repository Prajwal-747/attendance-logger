import attendance
import data
import students

def student_menu():
    while True:
        print("STUDENT MANAGEMENT")
        print("1. List Students")
        print("2. Add Student")
        print("3. Search Student")
        print("4. Update Student")
        print("5. Remove Student")
        print("0. Back to Main Menu")
        choice = input("Enter your choice: ").strip()
        if choice == '1':
            students.list_students()
        elif choice == '2':
            students.add_student()
        elif choice == '3':
            students.search_student()
        elif choice == '4':
            students.update_student()
        elif choice == '5':
            students.remove_student()
        elif choice == '0':
            print("Exiting...")
            break
        else:
            print("Invalid Choice")

def attendance_menu():
    while True:
           print("ATTENDANCE MANAGEMENT")
           print("1. Take Attendance")
           print("2. View Student Attendance")
           print("3. View Session Attendance")
           print("4. View Absentees")
           print("5. View Unmarked Students")
           print("6. Edit Attendance")
           print("0. Back to Main Menu")
           choice = input("Enter your choice: ").strip()
           if choice == '1':
               attendance.take_attendance()
           elif choice == '2':
               attendance.view_student_attendance()
           elif choice == '3':
               attendance.view_session_attendance()
           elif choice == '4':
               attendance.view_absentees()
           elif choice == '5':
               attendance.view_unmarked()
           elif choice == '6':
               attendance.edit_attendance()
           elif choice == '0':
               print("Exiting...")
               break
           else:
               print("Invalid Choice")

def main():
    print("App Started")
    data.initialize_db()
    
    while True:
        print("Attendance Logger")
        print("1. Student Management")
        print("2. Attendance Management")
        print("0. Exit")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            student_menu()
        elif choice == '2':
            attendance_menu()
        elif choice == '0':
            print("Exiting...")
            break
        else:
            print("Invalid Choice")
        
if __name__ == "__main__":
    main()