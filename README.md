# Residential Complaint Management System 🏠

A **Flask-based web application** designed to streamline complaint management for residential societies. The system enables residents to register personal or community complaints, upload supporting images, and track their complaint status in real-time. Admins can securely log in, view and filter complaints, assign them to workers based on specialization, and monitor resolution progress. Workers receive their assigned complaints and must verify resolution using a unique code provided to the resident. The system also includes password reset via email OTP, post-resolution feedback collection, image uploads, and role-based dashboards for Users, Admins, and Workers.
---

## 🔧 Features

- 🔐 User registration and secure login system
- 📍 Add user address (used for personal complaints)
- 📝 Lodge personal or community complaints
- 🖼️ Upload images with complaints
- 🧑‍💼 Admin login, dashboard, and complaint filtering
- 👷 Admin assigns complaints to workers
- 🔄 Complaint status: `Pending → In Progress → Resolved`
- ✉️ Email-based verification codes sent at complaint registration
- 🔐 Password reset via email OTP
- ✅ Workers enter the correct code to mark complaint as resolved
- 💬 User feedback system after resolution
- 🔎 Filtered views and flash messages for each role

---

## 🛠️ Tech Stack

| Layer        | Technology                              |
|--------------|-----------------------------------------|
| **Frontend** | HTML, CSS (Bootstrap), Jinja2 Templates |
| **Backend**  | Python (Flask), MySQL                   |
| **Email**    | Flask-Mail (SMTP: Gmail)                |
| **Security** | Hashed passwords (SHA256),Flask Session |
| **Uploads**  | Image handling via  `Werkzeug`          |

---

## 📁 Project Structure

residential-complaint-management-system/
├── app.py
├── db_setup.py
├── requirements.txt
├── config_sample.py # Copy & rename this to config.py with your credentials
├── .gitignore
├── templates/ # All HTML files
├── static/
│ └── complaint_images/ # Uploaded images
└── README.md

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
 git clone https://github.com/Himanshu-Kumar-Sah/Residential-Complaint-Management-System.git
 cd residential-complaint-management-system

2. Create Virtual Environment (optional)

    python -m venv venv
    venv\Scripts\activate   # On Windows

    source venv/bin/activate  # On macOS/Linux

3. Install Requirements

    pip install -r requirements.txt

4. Configure Database

    Create a MySQL database (e.g. user_database)

    Copy config_sample.py → rename it to config.py

    Fill in your DB credentials and email SMTP config

    CREATE DATABASE user_database;

5. Run the App

    python app.py
    Then open your browser at http://127.0.0.1:5000

🔒 Configuration Notes
    ⚠️ config.py contains sensitive credentials.
    It is excluded via .gitignore.
    You must create your own copy using config_sample.py.

💡 Future Enhancements
    📊 Admin dashboard with complaint statistics
    📱 SMS notifications for complaint updates
    🌟 Worker performance rating and tracking
    🧠 AI/ML-based complaint categorization
    🔐 Multi-admin support and roles

👨‍💻 Author
    Himanshu Kumar Sah
    Software Engineering Student @ Delhi Technological University (DTU)
    [GitHub Profile] : https://github.com/Himanshu-Kumar-Sah


