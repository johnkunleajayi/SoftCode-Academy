from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from app.auth import signup as auth_signup, signin as auth_signin
from app.auth import authenticate_salesforce
from app.student import get_student_data, create_student, get_student_data_by_email
from app.state import student_users  # Import from app.state instead
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
        student_users[email] = {
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
        user = student_users.get(email)

        if not user:
            # Check if user exists in the database (MongoDB)
            user = users_collection.find_one({'email': email})
            if not user:
                if sf:
                    student_data = get_student_data_by_email(sf, email)
                    if not student_data:
                        return "User not found in Salesforce", 404

                    user = {
                        "name": student_data["Name"],
                        "email": student_data["Email"],
                        "phone_number": student_data["Phone"],
                        "sf_id": student_data["Id"]
                    }
                    student_users[email] = user
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
    student_data = get_student_data_by_email(sf, user_email)

    if not student_data:
        return "User not found in Salesforce", 404

    # Use the public image URL directly
    image_url = student_data.get('New_Profile_URL__c')


    return render_template(
        'dashboard.html',
        name=student_data.get('Full_Name__c'),
        email=student_data.get('Email__c'),
        phone=student_data.get('Phone_Number__c'),
        assignments_completed=student_data.get('Assignment_Completed__c', 0),
        enrolldate=student_data.get('Enrollment_Date__c'),
        grade=student_data.get('Final_Grade__c'),
        grad=student_data.get('Graduation_Date__c'),
        comment=student_data.get('Instructor_s_Comments__c'),
        image_url=image_url,
        progress=student_data.get('Progress_Percentage__c'),
        skills=student_data.get('Skills__c'),
        status=student_data.get('Status__c'),
        tplan=student_data.get('Training_Plan__c'),
        username=student_data.get('Username__c')
    )


# Signout route
@app.route('/signout', methods=['POST'])
def signout():
    session.clear()
    return redirect(url_for('signin_page'))

# Get student by ID (JSON API)
@app.route('/students/<student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    if sf:
        student_data = get_student_data(sf, student_id)
        if student_data:
            return jsonify(student_data), 200
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"error": "Salesforce Authentication failed."}), 500

# Create student (JSON API)
@app.route('/students', methods=['POST'])
@jwt_required()
def create_student_route():
    data = request.get_json()
    if sf:
        new_student = create_student(sf, data['name'], data['email'], data['phone'])
        return jsonify({"id": new_student['id']}), 201
    return jsonify({"error": "Salesforce Authentication failed."}), 500


# Show update form
@app.route('/update-profile', methods=['GET'])
def update_profile():
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    user_email = session.get('email')
    student_data = get_student_data_by_email(sf, user_email)

    if not student_data:
        return "User not found", 404
    

    return render_template(
    'update_profile.html',
    student=student_data,
    name=student_data['Full_Name__c'],
    image_url=student_data['New_Profile_URL__c'],
    username=student_data.get('Username__c', ''),
    status=student_data.get('Status__c', ''),
    phone=student_data.get('Phone_Number__c', ''),
    email=student_data.get('Email__c', ''),
    assignments_completed=student_data.get('Assignments_Completed__c'),
    url1=student_data.get('Week_1_LinkedIn_URL__c'),
    url2=student_data.get('Week_2_LinkedIn_URL__c'),
    url3=student_data.get('Week_3_LinkedIn_URL__c'),
    url4=student_data.get('Week_4_LinkedIn_URL__c'),
    url5=student_data.get('Week_5_LinkedIn_URL__c'),
    url6=student_data.get('Week_6_LinkedIn_URL__c'),
    url7=student_data.get('Week_7_LinkedIn_URL__c'),
    url8=student_data.get('Week_8_LinkedIn_URL__c'),
    url9=student_data.get('Week_9_LinkedIn_URL__c'),
    url10=student_data.get('Week_10_LinkedIn_URL__c'),
    
)





# Save profile updates
@app.route('/save-profile', methods=['POST'])
def save_profile():
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    user_email = session.get('email')
    student_data = get_student_data_by_email(sf, user_email)

    if not student_data:
        return "User not found", 404

    record_id = student_data['Id']
    #Fields to be updated
    updated_fields = {
        'Phone_Number__c': request.form.get('phone'),
        'Username__c': request.form.get('username'),
        'Week_1_LinkedIn_URL__c': request.form.get('url1'),
        'Week_2_LinkedIn_URL__c': request.form.get('url2'),
        'Week_3_LinkedIn_URL__c': request.form.get('url3'),
        'Week_4_LinkedIn_URL__c': request.form.get('url4'),
        'Week_5_LinkedIn_URL__c': request.form.get('url5'),
        'Week_6_LinkedIn_URL__c': request.form.get('url6'),
        'Week_7_LinkedIn_URL__c': request.form.get('url7'),
        'Week_8_LinkedIn_URL__c': request.form.get('url8'),
        'Week_9_LinkedIn_URL__c': request.form.get('url9'),
        'Week_10_LinkedIn_URL__c': request.form.get('url10')
    }

    sf.Student__c.update(record_id, updated_fields)
    return redirect(url_for('dashboard'))


# Submit Assignment form
@app.route('/assignment', methods=['GET'])
def assignment_profile():
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    user_email = session.get('email')
    student_data = get_student_data_by_email(sf, user_email)

    if not student_data:
        return "User not found", 404

    return render_template('assignment_submission.html',
                       student=student_data,
                       name=student_data['Full_Name__c'],
                       image_url=student_data['New_Profile_URL__c'],
                       username=student_data.get('Username__c', ''),
                       status=student_data.get('Status__c', ''),
                       phone=student_data.get('Phone_Number__c', ''),
                       email=student_data.get('Email__c', ''),
                       assignments_completed=student_data.get('Assignments_Completed__c', 0),
                       progress=student_data.get('Progress_Percentage__c', 0))


# Save assignment updates
@app.route('/assignment-profile', methods=['POST'])
def assignment_submit():
    if 'email' not in session:
        return redirect(url_for('signin_page'))

    user_email = session.get('email')
    student_data = get_student_data_by_email(sf, user_email)

    if not student_data:
        return "User not found", 404

    record_id = student_data['Id']
    #Fields to be updated
    assignment_fields = {
        'Week_1_Assignment__c': request.form.get('week1'),
        'Week_2_Assignment__c': request.form.get('week2'),
        'Week_3_Assignment__c': request.form.get('week3'),
        'Week_4_Assignment__c': request.form.get('week4'),
        'Week_5_Assignment__c': request.form.get('week5'),
        'Week_6_Assignment__c': request.form.get('week6'),
        'Week_7_Assignment__c': request.form.get('week7'),
        'Week_8_Assignment__c': request.form.get('week8'),
        'Week_9_Assignment__c': request.form.get('week9'),
        'Week_10_Assignment__c': request.form.get('week10')
        
    }

    sf.Student__c.update(record_id, assignment_fields)
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)