import mysql.connector
import config


def connection():
    try:
        db = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        print("Database connected successfully.")
        return db
    except mysql.connector.Error as err:
        print("Error connecting to database:", err)
        return None

def create_tables(data):
    cursor = data.cursor()
    cursor.execute("""Create Table If Not Exists user_registeration_details(
            user_first_name varchar(50) NOT NULL ,
            user_last_name varchar (50),
            user_email_id varchar(50) UNIQUE ,
            user_phone_no char(10) PRIMARY KEY,
            check (user_phone_no REGEXP '^[1-9][0-9]{9}$'),
            user_gender ENUM('M','F','O'),
            user_password varchar(255) NOT NULL
            );""")
    
    cursor.execute("""Create Table If Not Exists user_address_details (
            user_phone_no char(10) PRIMARY KEY,
            check (user_phone_no REGEXP '^[1-9][0-9]{9}$'),
            user_house_no int NOT NULL ,
            user_tower_no VARCHAR(50),
            user_floor_no int ,
            user_locality varchar(255),
            user_area varchar(255),
            user_city varchar(255),
            user_state varchar(255) NOT NULL,
            user_pincode int 
            );""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS user_complaints_details (
                    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_phone_no CHAR(10),
                    complaint_type VARCHAR(100),
                    complaint_desc TEXT,
                    complaint_priority ENUM('Urgent', 'Normal'),
                    complaint_datetime DATETIME,
                    status ENUM('Pending', 'In Progress', 'Resolved'),
                    complaint_scope ENUM('Personal', 'Community'),
                    location VARCHAR(255),
                    assigned_to VARCHAR(100) DEFAULT 'Not Assigned',
                    FOREIGN KEY (user_phone_no) REFERENCES user_registeration_details(user_phone_no)
                );""")
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS admin_details (
                        admin_id INT AUTO_INCREMENT PRIMARY KEY,
                        admin_username VARCHAR(50) NOT NULL,
                        admin_password VARCHAR(255) NOT NULL
                                    );""")
    cursor.execute("SELECT * FROM admin_details WHERE admin_username = %s", (config.Admin1_username,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admin_details (admin_username, admin_password) VALUES (%s, %s);",
            (config.Admin1_username, config.Admin1_password)
        )
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers_details (
        worker_id INT AUTO_INCREMENT PRIMARY KEY,
        worker_name VARCHAR(50) NOT NULL,
        worker_phone_no CHAR(10) UNIQUE,
        worker_password VARCHAR(255) NOT NULL,
        specialization VARCHAR(100)
         );""")
     
    data.commit()
    cursor.close()

