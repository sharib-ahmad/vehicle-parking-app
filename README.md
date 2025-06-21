
# 🚗 Vehicle Parking Management System (VPMS)

A full-stack web application that enables efficient and secure management of parking lots, vehicles, and users. The system supports session-based authentication, dynamic role-based dashboards, and an integrated RESTful API documented with Swagger.

---

## 🔧 Project Overview

The Vehicle Parking Management System (VPMS) is designed to streamline parking operations. It allows administrators to manage parking lots and spots, while end users can register their vehicles and monitor parking activity. The system is equipped with real-time interaction, user profile management, and visual summaries of operations.

---

## 📦 Technology Stack

- **Backend**: Python, Flask, Flask-Login, Flask-RESTful, SQLAlchemy
- **Frontend**: Jinja2 Templating, Bootstrap 5, Font Awesome
- **Database**: SQLite
- **API Documentation**: Swagger (YAML)
- **Others**: WTForms, Chart.js (for summary visualization), Car-loading animation, Markdown & ERD documentation

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)
- Virtual Environment (recommended)

### Setup Instructions

1. **Clone or download** the project folder.
2. Navigate to the project directory and set up the virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Start the Flask server**:

```bash
python app.py
```

5. Visit `http://127.0.0.1:5000` to use the application.

---

## 🧪 API Access

- API is available at: `http://127.0.0.1:5000/api/`
- Swagger UI: `http://127.0.0.1:5000/swagger`

**Note**: APIs are secured via Flask-Login session-based authentication. Login to the web app first before using Swagger UI.

---


## 🎥 Demo Video

Link: [https://drive.google.com/file/d/your-video-link](https://drive.google.com/file/d/1K6dNET8AUnN19ZU2LPB1lYmA8QSx-yPp/view?usp=sharing)

---

## 👨‍💻 Author

**Sharib Ahmad**  
Roll Number: `24f2001786`  
Email: `24f2001786@ds.study.iitm.ac.in`

---