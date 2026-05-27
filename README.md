# Cinema Plus - Movie Ticket Booking Platform

A modern, full-stack movie ticket booking web application built purely with Python.

## Tech Stack
- **Frontend**: NiceGUI
- **Backend**: FastAPI
- **Database**: MySQL (via SQLAlchemy ORM)
- **Authentication**: JWT & Passlib (Bcrypt)

## Project Structure
```
movie-booking-app/
│
├── backend/            # FastAPI Backend
│   ├── main.py         # Entry point for backend
│   ├── database.py     # SQLAlchemy config
│   ├── models/         # DB Models
│   ├── schemas/        # Pydantic Schemas
│   ├── routes/         # API endpoints
│   ├── auth/           # JWT security
│   └── utils/          # PDF & QR generators
│
├── frontend/           # NiceGUI Frontend
│   ├── main.py         # Entry point for frontend
│   ├── pages/          # UI Views
│   ├── components/     # Reusable UI parts
│   └── services/       # API client
│
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── seed_db.py          # Database seeder
```

## Setup Instructions

### 1. Database Setup
Ensure you have MySQL running locally.
Create a database named `MovieTicketBooking`.
```sql
CREATE DATABASE MovieTicketBooking;
```

### 2. Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`):
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=admin
DB_NAME=MovieTicketBooking
SECRET_KEY=yoursecretkey
```

### 3. Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Seed the Database
Run the seed script to create tables and insert dummy data and an admin user.
```bash
python seed_db.py
```
Default accounts:
- Admin: `admin` / `admin123`
- User: `testuser` / `password123`

### 5. Start the Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
*API documentation available at http://localhost:8000/docs*

### 6. Start the Frontend
In a new terminal window:
```bash
# activate venv again
python frontend/main.py
```
*Web app available at http://localhost:8080*

## Features
- Dynamic visual seat selection
- PDF E-ticket generation with QR codes
- Admin dashboard with stats and movie management
- Secure JWT authentication
- Modern Dark "Cinema" UI aesthetic
