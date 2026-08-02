import java.util.ArrayList;

class StudentManagementSystem {

    private ArrayList<Student> students = new ArrayList<>();

    // Add Student
    public void addStudent(Student s) {
        for (Student st : students) {
            if (st.getId() == s.getId()) {
                System.out.println("❌ ID already exists!");
                return;
            }
        }
        students.add(s);
        System.out.println("✅ Student added!");
    }

    // View Students
    public void viewStudents() {
        if (students.isEmpty()) {
            System.out.println("No students found.");
            return;
        }
        for (Student s : students) {
            s.display();
        }
    }

    // ✅ FIX: Search Student (THIS WAS MISSING)
    public void searchStudent(int id) {
        for (Student s : students) {
            if (s.getId() == id) {
                s.display();
                return;
            }
        }
        System.out.println("❌ Student not found!");
    }

    // Update Student
    public void updateStudent(int id, String name, String course, double marks) {
        for (Student s : students) {
            if (s.getId() == id) {
                s.setName(name);
                s.setCourse(course);
                s.setMarks(marks);
                System.out.println("✅ Updated!");
                return;
            }
        }
        System.out.println("❌ Not found!");
    }

    // Delete Student
    public void deleteStudent(int id) {
        for (Student s : students) {
            if (s.getId() == id) {
                students.remove(s);
                System.out.println("✅ Deleted!");
                return;
            }
        }
        System.out.println("❌ Not found!");
    }

    // Student Login
    public Student studentLogin(String username, String password) {
        for (Student s : students) {
            if (s.getUsername().equals(username) && s.getPassword().equals(password)) {
                return s;
            }
        }
        return null;
    }
}