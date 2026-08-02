import java.util.Scanner;

public class Main {
    public static void main(String[] args) {

        Scanner sc = new Scanner(System.in);
        StudentManagementSystem sms = new StudentManagementSystem();

        String adminUser = "admin";
        String adminPass = "1234";

        int mainChoice;

        do {
            System.out.println("\n===== LOGIN SYSTEM =====");
            System.out.println("1. Admin Login");
            System.out.println("2. Student Login");
            System.out.println("3. Exit");
            System.out.print("Enter choice: ");

            mainChoice = sc.nextInt();
            sc.nextLine();

            switch (mainChoice) {

                // ================= ADMIN LOGIN =================
                case 1:
                    System.out.print("Admin Username: ");
                    String user = sc.nextLine();

                    System.out.print("Admin Password: ");
                    String pass = sc.nextLine();

                    if (user.equals(adminUser) && pass.equals(adminPass)) {

                        System.out.println("✅ Admin Login Successful!");

                        int choice;
                        do {
                            System.out.println("\n===== MENU =====");
                            System.out.println("1. Add Student");
                            System.out.println("2. View Students");
                            System.out.println("3. Search Student");
                            System.out.println("4. Update Student");
                            System.out.println("5. Delete Student");
                            System.out.println("6. Exit");
                            System.out.print("Enter choice: ");

                            choice = sc.nextInt();
                            sc.nextLine();

                            switch (choice) {

                                case 1:
                                    System.out.print("Enter ID: ");
                                    int id = sc.nextInt();
                                    sc.nextLine();

                                    System.out.print("Enter Name: ");
                                    String name = sc.nextLine();

                                    System.out.print("Enter Course: ");
                                    String course = sc.nextLine();

                                    System.out.print("Enter Marks: ");
                                    double marks = sc.nextDouble();
                                    sc.nextLine();

                                    System.out.print("Enter Username: ");
                                    String uname = sc.nextLine();

                                    System.out.print("Enter Password: ");
                                    String pwd = sc.nextLine();

                                    sms.addStudent(new Student(id, name, course, marks, uname, pwd));
                                    break;

                                case 2:
                                    sms.viewStudents();
                                    break;

                                case 3:
                                    System.out.print("Enter ID to search: ");
                                    int searchId = sc.nextInt();
                                    sms.searchStudent(searchId);
                                    break;

                                case 4:
                                    System.out.print("Enter ID to update: ");
                                    int upId = sc.nextInt();
                                    sc.nextLine();

                                    System.out.print("Enter New Name: ");
                                    String newName = sc.nextLine();

                                    System.out.print("Enter New Course: ");
                                    String newCourse = sc.nextLine();

                                    System.out.print("Enter New Marks: ");
                                    double newMarks = sc.nextDouble();

                                    sms.updateStudent(upId, newName, newCourse, newMarks);
                                    break;

                                case 5:
                                    System.out.print("Enter ID to delete: ");
                                    int delId = sc.nextInt();
                                    sms.deleteStudent(delId);
                                    break;

                                case 6:
                                    System.out.println("Exiting Admin Menu...");
                                    break;

                                default:
                                    System.out.println("❌ Invalid choice!");
                            }

                        } while (choice != 6);

                    } else {
                        System.out.println("❌ Wrong Admin Credentials!");
                    }
                    break;

                // ================= STUDENT LOGIN =================
                case 2:
                    System.out.print("Student Username: ");
                    String sUser = sc.nextLine();

                    System.out.print("Student Password: ");
                    String sPass = sc.nextLine();

                    Student student = sms.studentLogin(sUser, sPass);

                    if (student != null) {
                        System.out.println("✅ Student Login Successful!");
                        student.display();
                    } else {
                        System.out.println("❌ Invalid Student Login!");
                    }
                    break;

                case 3:
                    System.out.println("Exiting System...");
                    break;

                default:
                    System.out.println("❌ Invalid choice!");
            }

        } while (mainChoice != 3);
    }
}