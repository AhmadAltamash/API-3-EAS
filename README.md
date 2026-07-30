# 🚀 Export Automation System (EAS)

An AI-powered web application built with **Flask** to help businesses discover international buyers, classify them using Google Gemini AI, enrich contact information, and launch targeted email campaigns.

---

## 📖 Overview

Export Automation System (EAS) automates the workflow of export lead generation by combining web search, AI classification, contact management, and email automation into a single platform.

Instead of manually searching for buyers and maintaining spreadsheets, EAS allows users to:

- Search buyers from multiple online sources
- Store buyers in a centralized database
- Automatically classify companies using AI
- Enrich buyer information
- Launch email campaigns with attachments
- Track campaign statistics and reports

---

# ✨ Features

### 🔍 Buyer Search

- Search buyers using business keywords
- Supports multiple search sources
- Automatically stores search results
- Removes duplicate entries

---

### 🗂 Buyer Database

- View all discovered buyers
- Company information
- Website
- Email
- Country
- Business category
- Source

---

### 🤖 AI Classification

Powered by **Google Gemini AI**

Automatically classifies buyers into categories such as:

- Importer
- Exporter
- Manufacturer
- Distributor
- Wholesaler
- Retailer
- Unknown

Supports:

- Individual classification
- Bulk classification

---

### 📧 Email Campaign

- Send personalized email campaigns
- SMTP integration
- Support file attachments
- Email templates
- Campaign tracking

---

### 📊 Dashboard

Displays:

- Total Buyers
- Email Ready Buyers
- AI Classified Buyers
- Total Campaigns
- Emails Sent
- Failed Emails
- Success Rate
- Recent Buyers
- Recent Campaigns

---

### 📈 Reports

Provides campaign insights including:

- Campaign history
- Email statistics
- Delivery performance
- Success metrics

---

### ⚙ Settings

Centralized application configuration:

- SMTP Configuration
- Gemini AI Configuration
- Application Status
- Environment Information

---

# 🛠 Tech Stack

## Backend

- Python
- Flask
- SQLAlchemy
- Flask-Migrate
- SQLite

## Frontend

- HTML5
- CSS3
- Bootstrap 5
- Font Awesome
- Jinja2

## AI

- Google Gemini API

## Database

- SQLite

## Deployment

- Gunicorn
- Render (Recommended)

---

# 📂 Project Structure

```text
Export-Automation-System/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   ├── static/
│   └── extensions.py
│
├── migrations/
├── instance/
├── run.py
├── config.py
├── requirements.txt
├── Procfile
└── README.md
```

---

# ⚡ Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Export-Automation-System.git

cd Export-Automation-System
```

Create virtual environment

```bash
python -m venv venv
```

Activate it

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file.

Example:

```env
SECRET_KEY=your_secret_key

GOOGLE_API_KEY=your_gemini_api_key

EMAIL_ADDRESS=your_email@gmail.com

EMAIL_PASSWORD=your_gmail_app_password

DATABASE_URL=sqlite:///instance/export.db
```

---

# ▶ Running the Application

```bash
flask db upgrade
```

Start the server

```bash
python run.py
```

Application will be available at

```
http://127.0.0.1:5000
```

---

# 🚀 Deployment

This project is ready for deployment on platforms such as:

- Render
- Railway
- PythonAnywhere
- AWS EC2
- DigitalOcean

For Render:

Build Command

```bash
pip install -r requirements.txt
```

Start Command

```bash
gunicorn run:app
```

---

# 📸 Application Modules

- Dashboard
- Buyer Search
- Buyer Database
- AI Classification
- Email Campaign
- Campaign History
- Reports
- Settings

---

# 🔄 Workflow

```
Search Buyers
        │
        ▼
Store in Database
        │
        ▼
AI Classification
        │
        ▼
Contact Enrichment
        │
        ▼
Email Campaign
        │
        ▼
Reports & Analytics
```

---

# 📌 Future Improvements

- PostgreSQL support
- User authentication
- Campaign scheduling
- Cloud file storage
- Email open & click tracking
- Buyer analytics dashboard
- Multi-user support

---

# 👨‍💻 Author

**Ahmad Altamash**

Computer Science Student

Built as an internship assessment project demonstrating:

- Flask Development
- Database Design
- RESTful Architecture
- AI Integration
- Email Automation
- Web Scraping
- Responsive UI Design

---

# 📄 License

This project is developed for educational and internship demonstration purposes.
