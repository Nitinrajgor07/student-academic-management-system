import hashlib
import mysql.connector

# The 10 demo recruiter/company accounts
demo_companies = [
    {"email": "hr@novatechsolutions.in", "password": "Nova@123", "name": "NovaTech Solutions Pvt Ltd"},
    {"email": "careers@brightsofttech.com", "password": "Bright@123", "name": "BrightSoft Technologies"},
    {"email": "hr@nextgeninfotech.in", "password": "Next@123", "name": "NextGen Infotech"},
    {"email": "recruitment@skylinksystems.com", "password": "Sky@123", "name": "SkyLink Systems"},
    {"email": "jobs@vertexdigital.in", "password": "Vertex@123", "name": "Vertex Digital Pvt Ltd"},
    {"email": "hr@alphacoretech.com", "password": "Alpha@123", "name": "AlphaCore Technologies"},
    {"email": "hiring@codesphere.in", "password": "Code@123", "name": "CodeSphere Solutions"},
    {"email": "careers@futurebridge.io", "password": "Future@123", "name": "FutureBridge Software"},
    {"email": "hr@innovixlabs.com", "password": "Innovix@123", "name": "Innovix Labs"},
    {"email": "recruitment@quantumedge.in", "password": "Quantum@123", "name": "QuantumEdge Technologies"}
]

def verify():
    conn = mysql.connector.connect(
        host="localhost",
        user="studentuser",
        password="1234",
        database="studentdb"
    )
    cursor = conn.cursor()
    
    success = True
    print("Verifying 10 demo recruiter/company accounts:")
    for comp in demo_companies:
        cursor.execute("SELECT password, name FROM companies WHERE email = %s", (comp["email"],))
        res = cursor.fetchone()
        if not res:
            print(f"[FAIL] {comp['name']} ({comp['email']}) is not registered in the database.")
            success = False
            continue
        
        db_pwd, db_name = res
        expected_hash = hashlib.sha256(comp["password"].encode('utf-8')).hexdigest()
        if db_pwd == expected_hash:
            print(f"[PASS] {db_name} verified. Email: {comp['email']}, Hashed Password matches.")
        else:
            print(f"[FAIL] {db_name} password hash mismatch. DB: {db_pwd}, Expected: {expected_hash}")
            success = False
            
    cursor.close()
    conn.close()
    
    if success:
        print("\nAll 10 demo recruiter/company accounts are successfully verified!")
        exit(0)
    else:
        print("\nVerification failed!")
        exit(1)

if __name__ == "__main__":
    verify()
