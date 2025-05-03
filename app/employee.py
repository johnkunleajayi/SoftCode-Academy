from simple_salesforce import SalesforceResourceNotFound
from app.auth import authenticate_salesforce

def get_employee_data(sf, employee_id):
    """
    Fetch employee data from Salesforce by Employee ID.
    """
    try:
        employee = sf.Student__c.get(employee_id)  # Students are stored as 'Student__c' records
        return employee
    except SalesforceResourceNotFound:
        print(f"Employee with ID {employee_id} not found.")
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
            'Password__c': password  # Store password as a custom field
        })
        print(f"Student created created with ID: {employee['id']}")
        return employee
    except Exception as e:
        print(f"Error creating employee: {e}")
        return None
    
    
def get_employee_data_by_email(sf, email):
    try:
        query = f"SELECT Id, Name, Email__c, Phone_Number__c FROM Student__c WHERE Email__c = '{email}' LIMIT 1"
        result = sf.query(query)
        records = result.get('records', [])
        if records:
            return records[0]
        return None
    except Exception as e:
        print(f"Error fetching employee by email: {e}")
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
            print(f"Employee with ID {employee_id} updated.")
        else:
            print("No updates provided.")
        return True

    except SalesforceResourceNotFound:
        print(f"Employee with ID {employee_id} not found.")
        return False
    except Exception as e:
        print(f"Error updating employee: {e}")
        return False