from app.auth import signup, signin, authenticate_salesforce
from app.employee import get_employee_data, create_employee
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
        new_employee = create_employee(sf, "peter Doe", "peter.doe@example.com", "123-456-7890", "password123")
        if new_employee:
            employee_data = get_employee_data(sf, new_employee['id'])
            print("Employee Data:", employee_data)
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
