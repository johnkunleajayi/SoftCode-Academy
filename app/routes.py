from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from app.auth import signup as auth_signup, signin as auth_signin
from app.auth import authenticate_salesforce
from app.employee import get_employee_data, create_employee, update_employee, get_employee_data_by_email
from app.state import employee_users  # Import from app.state instead
from app.auth import users_collection  # Import users collection from auth.py
from bs4 import BeautifulSoup


sf = None  # Global inside routes.py

def set_salesforce_client(salesforce_client):
    global sf
    sf = salesforce_client



# Salesforce instance
sf = authenticate_salesforce()

# Initialize Flask app and JWT
app = Flask(__name__)
app.secret_key = "your_secret_session_key"  # Required for session tracking
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"  # Use a strong secret in production
jwt = JWTManager(app)

# Home route
@app.route('/')
def index():
    return redirect(url_for('signup_route'))

# Signup page (GET + POST)
@app.route('/signup', methods=['GET', 'POST'])
def signup_route():
    if request.method == 'GET':
        return render_template('signup.html')

    data = request.form
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone_number')
    password = data.get('password')

    try:
        result = auth_signup(email, password, name, phone)

        # Store in-memory data (temporary)
        employee_users[email] = {
            "name": name,
            "email": email,
            "phone_number": phone,
            "sf_id": result.get('id')
        }

        return redirect(url_for('signin_page'))
    except Exception as e:
        return f"Signup failed: {str(e)}", 400

# Signin page (GET)
@app.route('/signin', methods=['GET'])
def signin_page():
    return render_template('signin.html')

# HTML Signin Form (POST)
@app.route('/signin-form', methods=['POST'])
def signin_form():
    data = request.form
    email = data.get('email')
    password = data.get('password')

    try:
        result = auth_signin(email, password)
        user = employee_users.get(email)

        if not user:
            # Check if user exists in the database (MongoDB)
            user = users_collection.find_one({'email': email})
            if not user:
                if sf:
                    employee_data = get_employee_data_by_email(sf, email)
                    if not employee_data:
                        return "User not found in Salesforce", 404

                    user = {
                        "name": employee_data["Name"],
                        "email": employee_data["Email"],
                        "phone_number": employee_data["Phone"],
                        "sf_id": employee_data["Id"]
                    }
                    employee_users[email] = user
                else:
                    return "Salesforce not authenticated", 500

        # ✅ Set session values, including sf_id
        session['email'] = user['email']
        session['name'] = user['name']
        session['phone'] = user['phone_number']
        session['sf_id'] = user['sf_id']  # ✅ Add this line

        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"<h3>Login failed: {str(e)}</h3>", 400


# JSON Signin API
@app.route('/signin', methods=['POST'])
def signin_token():
    data = request.get_json()
    try:
        result = auth_signin(data['email'], data['password'])
        return jsonify({"token": result['token']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

from flask import render_template, redirect, url_for, session
from bs4 import BeautifulSoup


@app.route('/dashboard')
def dashboard():
    print("🔥 DEBUG: Entered /dashboard route")
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    user_email = session.get('email')
    employee_data = get_employee_data_by_email(sf, user_email)

    if not employee_data:
        return "User not found in Salesforce", 404

    # Use the public image URL directly
    image_url = employee_data.get('New_Profile_URL__c')


    return render_template(
        'dashboard.html',
        name=employee_data.get('Full_Name__c'),
        email=employee_data.get('Email__c'),
        phone=employee_data.get('Phone_Number__c'),
        assignments_completed=employee_data.get('Assignment_Completed__c', 0),
        enrolldate=employee_data.get('Enrollment_Date__c'),
        grade=employee_data.get('Final_Grade__c'),
        grad=employee_data.get('Graduation_Date__c'),
        comment=employee_data.get('Instructor_s_Comments__c'),
        image_url=image_url,
        progress=employee_data.get('Progress_Percentage__c'),
        skills=employee_data.get('Skills__c'),
        status=employee_data.get('Status__c'),
        tplan=employee_data.get('Training_Plan__c'),
        username=employee_data.get('Username__c')
    )


# Signout route
@app.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return redirect(url_for('signin_page'))

# Get employee by ID (JSON API)
@app.route('/employees/<employee_id>', methods=['GET'])
@jwt_required()
def get_employee(employee_id):
    if sf:
        employee_data = get_employee_data(sf, employee_id)
        if employee_data:
            return jsonify(employee_data), 200
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"error": "Salesforce Authentication failed."}), 500

# Create employee (JSON API)
@app.route('/employees', methods=['POST'])
@jwt_required()
def create_employee_route():
    data = request.get_json()
    if sf:
        new_employee = create_employee(sf, data['name'], data['email'], data['phone'])
        return jsonify({"id": new_employee['id']}), 201
    return jsonify({"error": "Salesforce Authentication failed."}), 500

# Update employee (JSON API)
@app.route('/employees/<employee_id>', methods=['PUT'])
@jwt_required()
def update_employee_route(employee_id):
    data = request.get_json()
    if sf:
        updated = update_employee(
            sf,
            employee_id,
            name=data.get('name'),
            email=data.get('email'),
            phone_number=data.get('phone')
        )
        if updated:
            return jsonify({"message": "Employee updated successfully"}), 200
        return jsonify({"error": "Employee not found or failed to update."}), 400
    return jsonify({"error": "Salesforce Authentication failed."}), 500

# Profile Update Form Page
@app.route('/update-profile', methods=['GET'])
def update_profile_form():
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    # Get the user's data from Salesforce (or session if needed)
    print("SF is available:", bool(sf))
    print("Salesforce is", "connected" if sf else "not connected")


    user_email = session.get('email')
    user_sf_id = employee_users.get(user_email, {}).get('sf_id')

    if sf and user_sf_id:
        employee_data = get_employee_data(sf, user_sf_id)
        if employee_data:
            return render_template(
    'update_profile.html',
    name=employee_data.get('Name'),
    email=employee_data.get('Email'),
    phone=employee_data.get('Phone')
)
        return "Employee data not found", 404
    return "Salesforce not authenticated or user ID missing", 500

# Handle Profile Update Submission
@app.route('/update-profile', methods=['POST'])
def update_profile_submit():
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    data = request.form
    user_email = session.get('email')
    user_sf_id = employee_users.get(user_email, {}).get('sf_id')

    if sf and user_sf_id:
        updated = update_employee(
            sf,
            user_sf_id,
            name=data.get('name'),
            email=data.get('email'),
            phone_number=data.get('phone')
        )
        if updated:
            # Update session info
            session['name'] = data.get('name')
            session['email'] = data.get('email')
            session['phone'] = data.get('phone')

            # ✅ Add this to keep the in-memory store consistent
            employee_users[user_email].update({
                "name": data.get('name'),
                "phone_number": data.get('phone')
            })
            return redirect(url_for('dashboard'))  # ✅ redirect after successful update
        return "Update failed", 400
    return "Salesforce not authenticated or user ID missing", 500

if __name__ == "__main__":
    app.run(debug=True)