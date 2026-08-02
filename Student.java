class Student {
    private int id;
    private String name;
    private String course;
    private double marks;
    private String username;
    private String password;

    public Student(int id, String name, String course, double marks, String username, String password) {
        this.id = id;
        this.name = name;
        this.course = course;
        this.marks = marks;
        this.username = username;
        this.password = password;
    }

    public int getId() { return id; }
    public String getUsername() { return username; }
    public String getPassword() { return password; }

    public void setName(String name) { this.name = name; }
    public void setCourse(String course) { this.course = course; }
    public void setMarks(double marks) { this.marks = marks; }

    public String calculateGrade() {
        if (marks >= 80) return "A";
        else if (marks >= 60) return "B";
        else if (marks >= 40) return "C";
        else return "Fail";
    }

    public void display() {
        System.out.println("\n----- STUDENT DETAILS -----");
        System.out.println("ID     : " + id);
        System.out.println("Name   : " + name);
        System.out.println("Course : " + course);
        System.out.println("Marks  : " + marks);
        System.out.println("Grade  : " + calculateGrade());
    }
}