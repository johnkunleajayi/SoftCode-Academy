from app.auth import signup, signin, authenticate_salesforce
from app.student import get_student_data, create_student
from app.routes import app, set_salesforce_client  # ✅ this brings in your Flask app + setter

def run_tests():
    try:
        signup_result = signup("peter.doe@example.com", "password123", "peter Doe", "123-456-7890")
        print(signup_result)
    except Exception as e:
        print(f"Signup Error: {e}")

    try:
        signin_result = signin("peter.doe@example.com", "password123")
        print(f"Signin successful, JWT Token: {signin_result['token']}")
    except Exception as e:
        print(f"Signin Error: {e}")

    # You can skip this part if you're already authenticating above
    sf = authenticate_salesforce()
    if sf:
        print("Salesforce authenticated successfully.")
        new_student = create_student(sf, "peter Doe", "peter.doe@example.com", "123-456-7890", "password123")
        if new_student:
            student_data = get_student_data(sf, new_student['id'])
            print("Student Data:", student_data)
    else:
        print("Salesforce Authentication failed.")

if __name__ == "__main__":
    # ✅ Authenticate once and inject into routes
    sf = authenticate_salesforce()
    if sf:
        print("✅ Salesforce authenticated successfully.")
        set_salesforce_client(sf)  # 👈 injects it globally
    else:
        print("❌ Salesforce authentication failed.")

# Do not use app.run(debug=True) in production
    app.run(debug=False, host='0.0.0.0', port=5000)