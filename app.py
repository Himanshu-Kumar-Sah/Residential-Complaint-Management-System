from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

import hashlib
import random
import os
from datetime import datetime

from db_setup import connection, create_tables
import mysql.connector

from config import MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  

UPLOAD_FOLDER = os.path.join('static', 'complaint_images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_USERNAME

mail = Mail(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Connect to DB once when Flask starts
db = connection()
if not db:
    print("DB connection failed.")

@app.route('/')
def home():
    return render_template('home.html')
# -------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        password = request.form.get('password')

        if not all([first_name, email, phone, password]):
            flash("First name, phone number, email, and password are required.", "user_error")
            return redirect(url_for('registration'))

        if not phone.isdigit():
            flash("Phone number should contain digits only.", "user_error")
            return redirect(url_for("registration"))

        if len(phone) != 10:
            flash("Phone number must be exactly 10 digits.", "user_error")
            return redirect(url_for("registration"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "user_error")
            return redirect(url_for("registration"))

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            cursor = db.cursor()   
            cursor.execute("SELECT user_phone_no FROM user_registeration_details WHERE user_phone_no = %s", (phone,))
            result = cursor.fetchone()

            if result:
                flash("You have already registered before. Please login.", "user_error")
                return redirect(url_for('user_login'))

            cursor.execute("SELECT user_email_id FROM user_registeration_details WHERE user_email_id = %s", (email,))
            email_exists = cursor.fetchone()

            if email_exists:         
                flash("This email is already registered. Please login.", "user_error")
                return redirect(url_for('user_login'))

            cursor.execute(
                "INSERT INTO user_registeration_details (user_first_name, user_last_name, user_email_id, user_phone_no, user_gender, user_password) VALUES (%s, %s, %s, %s, %s, %s)",
                (first_name, last_name, email, phone, gender, hashed_password)
            )
            db.commit()
            cursor.close()

            flash("Registration successful! Now login.")
            return redirect(url_for('user_login'))

        except Exception as e:
            flash(f"Database error: {str(e)}", "user_error")
            return redirect(url_for('registration'))

    return render_template('registration.html')



@app.route('/user_login', methods=['GET', 'POST']) 
def user_login():
    if request.method == 'POST':
        user_phone_no = request.form.get('user_phone_no')
        user_password = request.form.get('user_password')

        if not all([user_phone_no, user_password]):
            flash("Phone number and password are required.", "user_error")
            return redirect(url_for('user_login'))

        hashed_password = hashlib.sha256(user_password.encode()).hexdigest()

        try:
            my_cursor = db.cursor()
            query = """
                SELECT user_phone_no
                FROM user_registeration_details
                WHERE user_phone_no = %s AND user_password = %s;
            """
            my_cursor.execute(query, (user_phone_no, hashed_password)) 
            result = my_cursor.fetchone()
            my_cursor.close()
            
            if result:
                session['user_phone_no'] = user_phone_no
                flash("Login successful.", "user_success")  
                return redirect(url_for('user_dashboard'))
            else:
                flash("Incorrect phone number or password.", "user_error")
                return redirect(url_for('user_login'))

        except Exception as e:
            flash(f"Login failed: {e}", "user_error")  
            return redirect(url_for('user_login'))

    return render_template('user_login.html')



@app.route('/add_your_address', methods=['GET', 'POST'])
def add_your_address():
    if not db:
        flash("No database connection available.")
        return redirect(url_for('user_dashboard'))
    
    user_phone_no = session['user_phone_no']
    if 'user_phone_no' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('user_login'))

    my_cursor = db.cursor()
    query = "SELECT * FROM user_address_details WHERE user_phone_no = %s"
    my_cursor.execute(query, (user_phone_no,))
    address = my_cursor.fetchone()
    my_cursor.close()

    if address:
        flash("Address already added.", "info")
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        house_no = request.form.get('house_no')
        tower = request.form.get('tower')
        floor = request.form.get('floor')
        locality = request.form.get('locality')
        area = request.form.get('area')
        city = request.form.get('city')
        state = request.form.get('state')
        pincode = request.form.get('pincode')

        try:
            my_cursor = db.cursor()
            if not all([house_no, tower, floor, locality, area, city, state, pincode]):
                flash("All address fields are required.")
                return redirect(url_for('add_your_address'))

            if not house_no.isdigit() or not floor.isdigit() or not pincode.isdigit():
                flash("House No., Floor, and Pincode must be numeric.")
                return redirect(url_for('add_your_address'))

            house_no = int(house_no)
            floor = int(floor)
            pincode = int(pincode)

            
            insert_query = """
                INSERT INTO user_address_details 
                (user_phone_no, user_house_no, user_tower_no, user_floor_no, user_locality, user_area, user_city, user_state, user_pincode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            my_cursor.execute(insert_query, (user_phone_no, house_no, tower, floor, locality, area, city, state, pincode))
            db.commit()
            my_cursor.close()

            flash("Address added successfully.", "success")
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            flash(f"Error adding address: {e}", "error")
            return redirect(url_for('add_your_address'))

    return render_template('add_your_address.html')




@app.route('/add_complain', methods=['GET', 'POST'])
def add_complain():
    if not db:
        flash("No database connection available.")
        return redirect(url_for('user_dashboard'))

    user_phone_no = session.get('user_phone_no')
    if not user_phone_no:
        flash("Session expired. Please log in again.")
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        complaint_scope = request.form.get('complain')  # P or C
        if complaint_scope not in ["P", "C"]:
            flash("Invalid scope. Use 'P' for Personal or 'C' for Community.")
            return redirect(url_for('add_complain'))

        try:
            if complaint_scope == "P":
                cursor = db.cursor()
                cursor.execute("SELECT * FROM user_address_details WHERE user_phone_no = %s", (user_phone_no,))
                address_result = cursor.fetchone()
                cursor.close()

                if not address_result:
                    flash("You must add your address before submitting a personal complaint.")
                    return redirect(url_for('add_your_address'))

            complaint_type = request.form.get('complain_type')
            complaint_description = request.form.get('complain_description')
            complaint_priority = request.form.get('complain_priority', '').capitalize()
            location = request.form.get('location') if complaint_scope == "C" else None
            image_file = request.files.get('complaint_image')
            filename = None
            verification_code = str(random.randint(100000, 999999))

            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"complaint_{user_phone_no}_{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                image_file.save(filepath)
            else:
                new_filename = None 

            if complaint_priority not in ["Urgent", "Normal"]:
                flash("Invalid priority. Choose 'Urgent' or 'Normal'.")
                return redirect(url_for('add_complain'))

            complaint_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor = db.cursor()
            insert_query = """
                INSERT INTO user_complaints_details (
                    user_phone_no, complaint_type, complaint_desc, complaint_priority, 
                    complaint_datetime, status, complaint_scope, location, assigned_to, image_path,verification_code
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            """
            cursor.execute(insert_query, (
                user_phone_no, complaint_type, complaint_description, complaint_priority,
                complaint_datetime, 'Pending', 'Personal' if complaint_scope == 'P' else 'Community',
                location, 'Not Assigned',new_filename,verification_code
            ))
            db.commit()

            cursor = db.cursor()
            cursor.execute("""
                SELECT complaint_id, complaint_type, complaint_desc, complaint_priority
                FROM user_complaints_details
                WHERE user_phone_no = %s
                ORDER BY complaint_datetime DESC
                LIMIT 1
            """, (user_phone_no,))
            complaint = cursor.fetchone()
            cursor.close()

            if complaint:
                complaint_id, complaint_type, complaint_description, complaint_priority = complaint

                # Get email
                cursor = db.cursor()
                cursor.execute("SELECT user_email_id FROM user_registeration_details WHERE user_phone_no = %s", (user_phone_no,))
                result = cursor.fetchone()
                cursor.close()

                if result:
                    user_email = result[0]
                    subject = "Complaint Registered - Verification Code"
                    body = f"""
                    Dear User,

                    Your complaint has been registered successfully.
                    📄 Complaint ID: {complaint_id}
                    📝 Type: {complaint_type}
                    ✏️ Description: {complaint_description}
                    🎯 Priority: {complaint_priority}
                    🔐 Verification Code: {verification_code}

                    Please share this code only with the assigned worker once the issue is resolved.

                    Thank you.
                    """

                    msg = Message(subject, recipients=[user_email])
                    msg.body = body
                    mail.send(msg)

            cursor.close()
            flash("Complaint submitted successfully.")
            return redirect(url_for('user_dashboard'))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return redirect(url_for('add_complain'))

    return render_template('add_complaint.html')


@app.route('/view_complaints', methods=['GET', 'POST'])
def view_complain():
    if not db:
        flash("No database connection available.")
        return redirect(url_for('user_dashboard'))

    user_phone_no = session.get('user_phone_no')
    if not user_phone_no:
        flash("Session expired. Please log in again.")
        return redirect(url_for('user_login'))

    complaints = []
    try:
        my_cursor = db.cursor()
        query = """
            SELECT complaint_id, user_phone_no, complaint_type, complaint_desc, 
                   complaint_priority, complaint_datetime, status, complaint_scope, 
                   location, assigned_to, worker_phone_no, image_path
            FROM user_complaints_details
            WHERE user_phone_no = %s ORDER BY complaint_datetime DESC
        """
        my_cursor.execute(query, (user_phone_no,))
        complaints = my_cursor.fetchall()
        my_cursor.close()

        if not complaints:
            flash("No complaints found.")

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('user_dashboard'))

    return render_template('view_complaints.html', complaints=complaints)


@app.route('/delete_complaint', methods=['GET', 'POST'])
def delete_complaint():
    if not db:
        flash("No database connection available.")
        return redirect(url_for('user_dashboard'))

    user_phone_no = session.get('user_phone_no')
    if not user_phone_no:
        flash("Session expired. Please log in again.")
        return redirect(url_for('user_login'))

    complaints = []
    
    try:
        my_cursor = db.cursor()
        # Fetch complaints of user
        query = """SELECT complaint_id, complaint_type, complaint_desc, complaint_priority, 
                          complaint_datetime, status, complaint_scope 
                   FROM user_complaints_details 
                   WHERE user_phone_no = %s 
                   ORDER BY complaint_datetime DESC"""
        my_cursor.execute(query, (user_phone_no,))
        complaints = my_cursor.fetchall()
        my_cursor.close()
    except Exception as e:
        flash(f"Error fetching complaints: {e}")
        return redirect(url_for('user_dashboard'))

    # Handle POST (form submitted)
    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id')

        if not complaint_id or not complaint_id.isdigit():
            flash("Invalid Complaint ID.")
            return render_template('delete_complaint.html', complaints=complaints)

        try:
            my_cursor = db.cursor()
            delete_query = """DELETE FROM user_complaints_details 
                              WHERE complaint_id = %s AND user_phone_no = %s AND status = 'Pending'"""
            my_cursor.execute(delete_query, (int(complaint_id), user_phone_no))

            if my_cursor.rowcount == 0:
                flash("Complaint not found or already processed.")
            else:
                db.commit()
                flash("Complaint deleted successfully.")
            
            my_cursor.close()
        except Exception as e:
            flash(f"Error deleting complaint: {e}")

    # Finally show complaints + form
    return render_template('delete_complaint.html', complaints=complaints)



@app.route('/give_feedback', methods=['GET', 'POST'])
def give_feedback():
    if not db:
        flash("No database connection available.")
        return redirect(url_for('user_dashboard'))

    user_phone_no = session.get('user_phone_no')
    if not user_phone_no:
        flash("Session expired. Please log in again.")
        return redirect(url_for('user_login'))

    complaints = []
    try:
        my_cursor = db.cursor()
        # Fetch unresolved complaints for feedback
        query = """ 
            SELECT complaint_id, complaint_desc, complaint_datetime, complaint_priority
            FROM user_complaints_details
            WHERE user_phone_no = %s AND status = 'Resolved' AND feedback_rating IS NULL
        """
        my_cursor.execute(query, (user_phone_no,))
        complaints = my_cursor.fetchall()
        my_cursor.close()

        if not complaints:
            flash("No resolved complaints available for feedback.")
            return render_template('give_feedback.html', complaints=[])

    except mysql.connector.Error as err:
        flash(f"Database error while fetching complaints: {err}")
        return redirect(url_for('user_dashboard'))

    # If feedback form submitted
    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id')
        feedback_rating = request.form.get('feedback_rating')
        feedback_text = request.form.get('feedback_text', '').strip()

        if not complaint_id or not complaint_id.isdigit():
            flash("Invalid Complaint ID.")
            return render_template('give_feedback.html', complaints=complaints)

        if not feedback_rating or not feedback_rating.isdigit() or int(feedback_rating) not in [1, 2, 3, 4, 5]:
            flash("Invalid rating. Please enter a number between 1 and 5.")
            return render_template('give_feedback.html', complaints=complaints)

        try:
            my_cursor = db.cursor()
            update_query = """
                UPDATE user_complaints_details
                SET feedback_rating = %s, feedback_text = %s
                WHERE complaint_id = %s AND user_phone_no = %s
            """
            my_cursor.execute(update_query, (int(feedback_rating), feedback_text, int(complaint_id), user_phone_no))
            db.commit()
            my_cursor.close()
            flash("Thank you for your feedback.")
            return redirect(url_for('user_dashboard'))

        except mysql.connector.Error as err:
            flash(f"Database error while saving feedback: {err}")

    return render_template('give_feedback.html', complaints=complaints)

@app.route('/user_dashboard')
def user_dashboard():
    user_phone_no = session.get('user_phone_no')
    if not user_phone_no:
        flash("Session expired. Please log in again.")
        return redirect(url_for('user_login'))
    return render_template('user_dashboard.html', user_phone_no=user_phone_no)

@app.route('/logout')
def logout():
    session.pop('user_phone_no', None)
    flash("You have been logged out.")
    return redirect(url_for('user_login'))


# ADMIN -----------------------------------------------------------------------------------------------------------------------------------

@app.route('/admin_login', methods=['GET', 'POST']) 
def admin_login():
    if request.method == 'POST':
        admin_username = request.form.get('admin_username')
        admin_password = request.form.get('admin_password')

        if not all([admin_username, admin_password]):
            flash("All fields are required.")
            return redirect(url_for('admin_login'))

        hashed_password = hashlib.sha256(admin_password.encode()).hexdigest()

        try:
            cursor = db.cursor()
            cursor.execute(
                "SELECT admin_username FROM admin_details WHERE admin_username = %s AND admin_password = %s",
                (admin_username, hashed_password)
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                session['admin_username'] = admin_username
                session['admin_username'] = result[0]
                flash("Admin login successful.")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid credentials.")
        except Exception as e:
            flash(f"Login failed: {e}")

    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_username' not in session:
        flash("Please log in as admin.")
        return redirect(url_for('admin_login'))

    return render_template('admin_dashboard.html', admin_username=session.get('admin_username'))


@app.route('/view_all_complaints', methods=['GET', 'POST'])
def view_all_complaints():
    if 'admin_username' not in session:
        flash("Please log in as admin.")
        return redirect(url_for('admin_login'))

    filters = []
    values = []

    if request.method == 'POST':
        priority = request.form.get('priority')
        status = request.form.get('status')
        scope = request.form.get('scope')
        assigned_to = request.form.get('assigned_to')

        if priority and priority in ['Urgent', 'Normal']:
            filters.append("complaint_priority = %s")
            values.append(priority)

        if status and status in ['Pending', 'In progress', 'Resolved']:
            filters.append("status = %s")
            values.append(status)

        if scope and scope in ['Personal', 'Community']:
            filters.append("complaint_scope = %s")
            values.append(scope)

        if assigned_to:
            filters.append("assigned_to = %s")
            values.append(assigned_to)

    query = """
        SELECT complaint_id, user_phone_no, complaint_type, complaint_desc, 
               complaint_priority, complaint_datetime, status, complaint_scope, 
               location, assigned_to, image_path
        FROM user_complaints_details
    """
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY complaint_datetime DESC"

    try:
        cursor = db.cursor()
        cursor.execute(query, tuple(values))
        complaints = cursor.fetchall()
        cursor.close()
    except Exception as e:
        flash(f"Database error: {e}")
        complaints = []

    return render_template('view_all_complaints.html', complaints=complaints)


@app.route('/add_worker', methods=['GET', 'POST'])
def add_worker():
    if 'admin_username' not in session:
        flash("Please log in as admin.")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        worker_name = request.form.get('worker_name').strip()
        worker_phone_no = request.form.get('worker_phone_no').strip()
        worker_password = request.form.get('worker_password').strip()
        specialization = request.form.get('specialization').strip()

        if not all([worker_name, worker_phone_no, worker_password, specialization]):
            flash("All fields are required.")
            return render_template('add_worker.html')

        if not worker_phone_no.isdigit() or len(worker_phone_no) != 10:
            flash("Invalid phone number. Must be 10 digits.")
            return render_template('add_worker.html')

        if len(worker_password) < 6:
            flash("Password must be at least 6 characters.")
            return render_template('add_worker.html')

        hashed_password = hashlib.sha256(worker_password.encode()).hexdigest()

        try:
            my_cursor = db.cursor()
            my_cursor.execute("SELECT * FROM workers_details WHERE worker_phone_no = %s", (worker_phone_no,))
            if my_cursor.fetchone():
                flash("Worker with this phone number already exists.")
                my_cursor.close()
                return render_template('add_worker.html')

            insert_query = """
                INSERT INTO workers_details (worker_name, worker_phone_no, worker_password, specialization)
                VALUES (%s, %s, %s, %s)
            """
            my_cursor.execute(insert_query, (worker_name, worker_phone_no, hashed_password, specialization))
            db.commit()
            my_cursor.close()

            flash("Worker added successfully.")
            return redirect(url_for('admin_dashboard'))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return render_template('add_worker.html')

    return render_template('add_worker.html')


@app.route('/assign_complaint', methods=['GET', 'POST'])
def assign_complaint():
    if not db:
        flash("Database connection unavailable.")
        return redirect(url_for('admin_dashboard'))

    try:
        cursor = db.cursor()

        # Fetch unassigned complaints
        cursor.execute("""
            SELECT complaint_id, complaint_type, complaint_scope, location 
            FROM user_complaints_details 
            WHERE assigned_to = 'Not Assigned'
        """)
        complaints = cursor.fetchall()

        # Fetch all available workers
        cursor.execute("""
            SELECT worker_id, worker_name, specialization 
            FROM workers_details
        """)
        workers = cursor.fetchall()
        cursor.close()

        if request.method == 'POST':
            complaint_id = request.form.get('complaint_id')
            worker_id = request.form.get('worker_id')

            if not complaint_id or not complaint_id.isdigit() or not worker_id or not worker_id.isdigit():
                flash("Invalid Complaint ID or Worker ID.")
                return redirect(url_for('assign_complaint'))

            cursor = db.cursor()
            # Check if complaint exists and is still unassigned
            cursor.execute("""
                SELECT complaint_id FROM user_complaints_details 
                WHERE complaint_id = %s AND assigned_to = 'Not Assigned'
            """, (int(complaint_id),))
            if not cursor.fetchone():
                flash("Complaint is either invalid or already assigned.")
                cursor.close()
                return redirect(url_for('assign_complaint'))

            # Get selected worker details
            cursor.execute("""
                SELECT worker_name, worker_phone_no FROM workers_details 
                WHERE worker_id = %s
            """, (int(worker_id),))
            worker = cursor.fetchone()
            if not worker:
                flash("Invalid Worker ID.")
                cursor.close()
                return redirect(url_for('assign_complaint'))

            worker_name, worker_phone_no = worker

            # Update complaint
            cursor.execute("""
                UPDATE user_complaints_details 
                SET assigned_to = %s, worker_phone_no = %s, status = 'In Progress'
                WHERE complaint_id = %s
            """, (worker_name, worker_phone_no, int(complaint_id)))
            db.commit()
            cursor.close()

            flash(f"Complaint ID {complaint_id} assigned to {worker_name}.")
            return redirect(url_for('assign_complaint'))

        return render_template('assign_complaint.html', complaints=complaints, workers=workers)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('admin_dashboard'))


@app.route('/update_complaint_status', methods=['GET', 'POST'])
def update_complaint_status():
    if not db:
        flash("Database connection unavailable.")
        return redirect(url_for('admin_dashboard'))

    try:
        cursor = db.cursor()

        # Fetch all complaints
        cursor.execute("""
            SELECT complaint_id, complaint_desc, status 
            FROM user_complaints_details
            ORDER BY complaint_datetime DESC
        """)
        complaints = cursor.fetchall()
        cursor.close()

        if request.method == 'POST':
            complaint_id = request.form.get('complaint_id')
            new_status = request.form.get('new_status')

            if not complaint_id or not complaint_id.isdigit():
                flash("Invalid Complaint ID.")
                return redirect(url_for('update_complaint_status'))

            valid_statuses = ['Pending', 'In Progress', 'Resolved']
            if new_status not in valid_statuses:
                flash("Invalid status selected.")
                return redirect(url_for('update_complaint_status'))

            cursor = db.cursor()
            cursor.execute("SELECT status FROM user_complaints_details WHERE complaint_id = %s", (int(complaint_id),))
            result = cursor.fetchone()
            if not result:
                flash("Complaint ID not found.")
                cursor.close()
                return redirect(url_for('update_complaint_status'))

            current_status = result[0]
            if current_status == 'Resolved' and new_status != 'Resolved':
                flash("Cannot downgrade from Resolved. No changes made.")
                cursor.close()
                return redirect(url_for('update_complaint_status'))

            cursor.execute(
                "UPDATE user_complaints_details SET status = %s WHERE complaint_id = %s",
                (new_status, int(complaint_id))
            )
            db.commit()
            cursor.close()
            flash(f"Complaint ID {complaint_id} status updated to {new_status}.")
            return redirect(url_for('update_complaint_status'))

        return render_template('update_complaint_status.html', complaints=complaints)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('admin_dashboard'))


@app.route('/delete_worker', methods=['GET', 'POST'])
def delete_worker():
    if not db:
        flash("Database not connected.")
        return redirect(url_for('admin_dashboard'))

    try:
        cursor = db.cursor()
        cursor.execute("SELECT worker_id, worker_name, specialization FROM workers_details")
        workers = cursor.fetchall()
        cursor.close()

        if not workers:
            flash("No workers found in the system.")
            return render_template('delete_worker.html', workers=[])

        # POST = Delete selected worker
        if request.method == 'POST':
            worker_id = request.form.get('worker_id')
            if not worker_id or not worker_id.isdigit():
                flash("Invalid Worker ID.")
                return redirect(url_for('delete_worker'))

            worker_id = int(worker_id)

            cursor = db.cursor()
            cursor.execute("SELECT worker_name FROM workers_details WHERE worker_id = %s", (worker_id,))
            result = cursor.fetchone()
            if not result:
                flash("Worker not found.")
                return redirect(url_for('delete_worker'))

            worker_name = result[0]
            cursor.execute("DELETE FROM workers_details WHERE worker_id = %s", (worker_id,))
            db.commit()
            cursor.close()
            flash(f"Worker '{worker_name}' deleted successfully.")
            return redirect(url_for('delete_worker'))

        return render_template('delete_worker.html', workers=workers)

    except Exception as e:
        flash(f"Error during deletion: {e}")
        return redirect(url_for('admin_dashboard'))


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_username', None)
    session.pop('admin_username', None)
    flash("Admin logged out.")
    return redirect(url_for('admin_login'))

#WORKER ----------------------------------------------------------------------------------------------------------------------------------

@app.route('/worker_login', methods=['GET', 'POST'])
def worker_login():
    if not db:
        flash("No database connection available.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        worker_phone_no = request.form.get('worker_phone_no').strip()
        worker_password = request.form.get('worker_password').strip()

        if not worker_phone_no or not worker_password:
            flash("Both phone number and password are required.")
            return render_template('worker_login.html')

        hashed_password = hashlib.sha256(worker_password.encode()).hexdigest()

        try:
            cursor = db.cursor()
            cursor.execute("""
                SELECT worker_phone_no 
                FROM workers_details 
                WHERE worker_phone_no = %s AND worker_password = %s
            """, (worker_phone_no, hashed_password))
            result = cursor.fetchone()
            cursor.close()

            if result:
                session['worker_phone_no'] = result[0]
                flash(f"Welcome, Worker {worker_phone_no}!")
                return redirect(url_for('worker_dashboard'))
            else:
                flash("Incorrect phone number or password.")
                return render_template('worker_login.html')

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return render_template('worker_login.html')

    return render_template('worker_login.html')


@app.route('/view_assigned_complaints')
def view_assigned_complaints():
    if 'worker_phone_no' not in session:
        flash("Please log in as worker.")
        return redirect(url_for('worker_login'))

    worker_phone_no = session['worker_phone_no']
    complaints = []

    try:
        cursor = db.cursor()
        # Fetch complaints assigned to this worker
        cursor.execute("""
            SELECT complaint_id, user_phone_no, complaint_type, complaint_desc, 
                   complaint_priority, complaint_scope, location 
            FROM user_complaints_details 
            WHERE worker_phone_no = %s
        """, (worker_phone_no,))
        complaints_data = cursor.fetchall()

        for complaint in complaints_data:
            complaint_id, user_phone_no, c_type, desc, priority, scope, location = complaint
            address = None

            if scope == 'Personal':
                # Fetch personal address if complaint is personal
                cursor.execute("""
                    SELECT user_house_no, user_tower_no, user_floor_no, 
                           user_locality, user_area, user_city, user_state, user_pincode
                    FROM user_address_details
                    WHERE user_phone_no = %s
                """, (user_phone_no,))
                addr = cursor.fetchone()
                if addr:
                    address = {
                        'house_no': addr[0],
                        'tower': addr[1],
                        'floor': addr[2],
                        'locality': addr[3],
                        'area': addr[4],
                        'city': addr[5],
                        'state': addr[6],
                        'pincode': addr[7]
                    }

            complaints.append({
                'complaint_id': complaint_id,
                'user_phone_no': user_phone_no,
                'type': c_type,
                'desc': desc,
                'priority': priority,
                'scope': scope,
                'location': location,
                'address': address
            })

        cursor.close()

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('worker_dashboard'))

    return render_template('view_assigned_complaints.html', complaints=complaints)


@app.route('/update_assigned_complaint_status', methods=['GET', 'POST'])
def update_assigned_complaint_status():
    if 'worker_phone_no' not in session:
        flash("Please log in as worker.")
        return redirect(url_for('worker_login'))

    worker_phone_no = session['worker_phone_no']
    complaints = []

    try:
        cursor = db.cursor()

        # Fetch complaints assigned to this worker and not already resolved
        cursor.execute("""
            SELECT complaint_id, complaint_type, complaint_scope, status 
            FROM user_complaints_details 
            WHERE worker_phone_no = %s AND status != 'Resolved'
        """, (worker_phone_no,))
        complaints = cursor.fetchall()

        if request.method == 'POST':
            complaint_id = request.form.get('complaint_id')
            entered_code = request.form.get('verification_code')

            if not complaint_id or not complaint_id.isdigit() or not entered_code:
                flash("Complaint ID or code is missing or invalid.")
                return redirect(url_for('update_assigned_complaint_status'))

            # Fetch the actual verification code for this complaint
            cursor.execute("""
                SELECT verification_code FROM user_complaints_details 
                WHERE complaint_id = %s AND worker_phone_no = %s
            """, (int(complaint_id), worker_phone_no))
            result = cursor.fetchone()

            if not result:
                flash("Complaint not found or not assigned to you.")
                return redirect(url_for('update_assigned_complaint_status'))

            actual_code = result[0]

            if entered_code == actual_code:
                # Mark as resolved
                cursor.execute("""
                    UPDATE user_complaints_details 
                    SET status = 'Resolved' 
                    WHERE complaint_id = %s AND worker_phone_no = %s
                """, (int(complaint_id), worker_phone_no))
                db.commit()
                flash(f"Complaint ID {complaint_id} marked as Resolved.")
            else:
                flash("Incorrect verification code.")

            return redirect(url_for('update_assigned_complaint_status'))

        cursor.close()

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('worker_dashboard'))

    return render_template('update_assigned_complaint_status.html', complaints=complaints)




@app.route('/worker_dashboard')
def worker_dashboard():
    if 'worker_phone_no' not in session:
        flash("Please log in as worker.")
        return redirect(url_for('worker_login'))

    worker_phone_no = session['worker_phone_no']
    return render_template('worker_dashboard.html', worker_phone_no=worker_phone_no)

@app.route('/worker_logout')
def worker_logout():
    session.pop('worker_phone_no', None)
    flash("Worker logged out.")
    return redirect(url_for('worker_login'))





@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':  
        email = request.form.get("email")

        if not email:
            flash("Email is required.")
            return redirect(url_for('forgot_password'))

        cursor = db.cursor()
        cursor.execute("SELECT user_phone_no FROM user_registeration_details WHERE user_email_id = %s", (email,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            flash("No user found with this email.")
            return redirect(url_for('forgot_password'))
        
        user_phone_no = result[0]
        verification_code = str(random.randint(100000, 999999))
        session['reset_code'] = verification_code
        session['reset_phone'] = user_phone_no

        try:
            msg = Message("Password Reset Verification Code", recipients=[email])
            msg.body = f"Your verification code is: {verification_code}"
            mail.send(msg)
            flash("Verification code sent to your email.")
            return redirect(url_for('verify_reset_code'))
        except Exception as e:
            flash(f"Error sending email: {e}")
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/verify_reset_code', methods=['GET', 'POST'])
def verify_reset_code():
    if 'reset_code' not in session or 'reset_phone' not in session:
        flash("Session expired or invalid access.")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        entered_code = request.form.get("verification_code")

        if entered_code == session['reset_code']:
            flash("Code verified. Please set a new password.")
            return redirect(url_for('reset_password'))
        else:
            flash("Incorrect verification code.")
            return redirect(url_for('verify_reset_code'))

    return render_template('verify_reset_code.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_phone' not in session:
        flash("Unauthorized access. Please start the reset process again.")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            flash("Both password fields are required.")
            return redirect(url_for('reset_password'))

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('reset_password'))

        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.")
            return redirect(url_for('reset_password'))

        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

        try:
            cursor = db.cursor()
            cursor.execute(
                "UPDATE user_registeration_details SET user_password = %s WHERE user_phone_no = %s",
                (hashed_password, session['reset_phone'])
            )
            db.commit()
            cursor.close()

            # Clear session values
            session.pop('reset_phone', None)
            session.pop('reset_code', None)

            flash("Password reset successful. Please log in.")
            return redirect(url_for('user_login'))

        except Exception as e:
            flash(f"Error updating password: {e}")
            return redirect(url_for('reset_password'))

    return render_template('reset_password.html')



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)