import logging
from simple_salesforce import SalesforceResourceNotFound

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_employee_data(sf, employee_id):
    """
    Fetch employee data from Salesforce by Employee ID.
    """

    from app.auth import authenticate_salesforce

    try:
        employee = sf.Student__c.get(employee_id)  # Students are stored as 'Student__c' records
        return employee
    except SalesforceResourceNotFound:
        logger.error(f"Employee with ID {employee_id} not found.")
        return None
    except Exception as e:
        logger.error(f"Error fetching employee data: {e}")
        return None

def create_employee(sf, name, email, phone_number, password):
    """
    Create a new employee record in Salesforce, including the password field.
    """
    try:
        # Create the employee record in Salesforce, storing password as part of the custom object
        employee = sf.Student__c.create({
            'Full_Name__c': name,
            'Email__c': email,
            'Phone_Number__c': phone_number,
            'Password__c': password  # Store password as a custom field (ensure it's hashed)
        })
        logger.info(f"Employee created with ID: {employee['id']}")
        return employee
    except Exception as e:
        logger.error(f"Error creating employee: {e}")
        return None

def get_employee_data_by_email(sf, email):
    try:
        query = f"SELECT Id, Assignment_Completed__c, Email__c, Enrollment_Date__c, Final_Grade__c, Full_Name__c, Graduation_Date__c, Instructor_s_Comments__c, Phone_Number__c, Profile_Image__c, New_Profile_URL__c, Progress_Percentage__c, Skills__c, Status__c, Student_s_Comments__c, Training_Plan__c, Username__c FROM Student__c WHERE Email__c = '{email}' LIMIT 1"
        result = sf.query(query)
        records = result.get('records', [])
        if records:
            return records[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching employee by email: {e}")
        return None

def update_employee(sf, employee_id, name=None, email=None, phone_number=None, password=None):
    """
    Update an existing employee record in Salesforce, including the password field if provided.
    """
    try:
        employee = sf.Student__c.get(employee_id)  # Fetch the existing employee record
        updates = {}

        if name:
            updates['Full_Name__c'] = name
        if email:
            updates['Email__c'] = email
        if phone_number:
            updates['Phone_Number__c'] = phone_number
        if password:
            updates['Password__c'] = password  # Update the password field if provided
        
        if updates:
            sf.Student__c.update(employee_id, updates)
            logger.info(f"Employee with ID {employee_id} updated.")
        else:
            logger.warning("No updates provided.")
        return True
    except SalesforceResourceNotFound:
        logger.error(f"Employee with ID {employee_id} not found.")
        return False
    except Exception as e:
        logger.error(f"Error updating employee: {e}")
        return False