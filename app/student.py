import logging
from simple_salesforce import SalesforceResourceNotFound

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_student_data(sf, student_id):
    """
    Fetch student data from Salesforce by Student ID.
    """

    from app.auth import authenticate_salesforce

    try:
        student = sf.Student__c.get(student_id)  # Students are stored as 'Student__c' records
        return student
    except SalesforceResourceNotFound:
        logger.error(f"Student with ID {student_id} not found.")
        return None
    except Exception as e:
        logger.error(f"Error fetching student data: {e}")
        return None

def create_student(sf, name, email, phone_number, password):
    """
    Create a new student record in Salesforce, including the password field.
    """
    try:
        # Create the student record in Salesforce, storing password as part of the custom object
        student = sf.Student__c.create({
            'Full_Name__c': name,
            'Email__c': email,
            'Phone_Number__c': phone_number,
            'Password__c': password  # Store password as a custom field (ensure it's hashed)
        })
        logger.info(f"Student created with ID: {student['id']}")
        return student
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        return None

def get_student_data_by_email(sf, email):
    try:
        query = f"SELECT Id, Assignment_Completed__c, Email__c, Enrollment_Date__c, Final_Grade__c, Full_Name__c, Graduation_Date__c, Instructor_s_Comments__c, Phone_Number__c, Profile_Image__c, New_Profile_URL__c, Progress_Percentage__c, Skills__c, Status__c, Student_s_Comments__c, Training_Plan__c, Username__c, Week_1_Assignment__c,  Week_2_Assignment__c, Week_3_Assignment__c, Week_4_Assignment__c, Week_5_Assignment__c, Week_6_Assignment__c, Week_7_Assignment__c, Week_8_Assignment__c, Week_9_Assignment__c, Week_10_Assignment__c, Week_1_LinkedIn_URL__c, Week_2_LinkedIn_URL__c, Week_3_LinkedIn_URL__c, Week_4_LinkedIn_URL__c, Week_5_LinkedIn_URL__c, Week_6_LinkedIn_URL__c, Week_7_LinkedIn_URL__c, Week_8_LinkedIn_URL__c, Week_9_LinkedIn_URL__c, Week_10_LinkedIn_URL__c  FROM Student__c WHERE Email__c = '{email}' LIMIT 1"
        result = sf.query(query)
        records = result.get('records', [])
        if records:
            return records[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching student by email: {e}")
        return None