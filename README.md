# Healthcare Web Application

A full-stack role-based healthcare web application that helps doctors generate discharge summaries and helps patients analyze hospital bills, medicine prices, and follow-up instructions.

## 🎯 Features

### For Doctors
- 📝 AI-assisted discharge summary generation (powered by Groq API)
- ✏️ Edit and customize discharge summaries
- 📋 Add follow-up instructions, diet advice, and red flag symptoms
- ✅ Mark summaries as final
- 📄 Download discharge summaries as PDF

### For Patients
- 📤 Upload hospital bills (image or PDF)
- 🔍 Automated bill analysis with OCR
- 💰 Compare charges with CGHS reference rates
- 💊 Medicine price analysis (brand vs generic)
- 🤝 "Where to Negotiate" suggestions with patient-friendly wording
- 📄 Download bill analysis reports as PDF
- 📋 View discharge summaries (read-only)

### For Everyone (Public Homepage)
- 💊 **Prescription Price Comparison**: Upload prescription images to compare medicine prices across 4 major online pharmacies (Tata 1mg, PharmEasy, NetMeds, Apollo Pharmacy)
- 🔍 OCR-powered medicine name extraction
- 💰 Automatic price sorting with cheapest option highlighted

## 🛠️ Tech Stack

- **Frontend**: React + Vite
- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **AI**: Groq API (Llama models)
- **OCR**: Tesseract, pdfplumber
- **PDF Generation**: ReportLab
- **Web Scraping**: Playwright (headless browser automation)

## 📋 Prerequisites

- Python 3.8+ (with pip)
- Node.js 16+ (with npm)
- Tesseract OCR installed on your system
- Groq API key (free from https://console.groq.com/)

### Installing Tesseract OCR

**Windows:**
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your system PATH

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## 🚀 Setup Instructions

### 1. Clone/Navigate to Project Directory

```bash
cd healthcare-app
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright and browsers (for price comparison feature)
pip install playwright aiofiles
python -m playwright install chromium

# Create .env file from example
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux

# Edit .env and add your Groq API key:
# GROQ_API_KEY=your_actual_groq_api_key_here
```

### 3. Get Groq API Key

1. Go to https://console.groq.com/
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and paste it in your `.env` file

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app:app --reload
```

The backend will start at: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The frontend will start at: http://localhost:5173

### 6. Access the Application

Open your browser and go to: **http://localhost:5173**

## 👤 Demo Credentials

### Doctor Login
- Username: `doctor1`
- Password: `password123`
- Role: Doctor

### Patient Login
- Username: `patient1`
- Password: `password123`
- Role: Patient

You can also create new accounts using the "Register" tab.

## 📚 API Documentation

Once the backend is running, visit: http://localhost:8000/docs

This provides interactive Swagger documentation for all API endpoints.

## 🗂️ Project Structure

```
healthcare-app/
├── backend/
│   ├── app.py                  # Main FastAPI application
│   ├── database.py             # Database models
│   ├── auth.py                 # Authentication utilities
│   ├── requirements.txt
│   ├── routers/
│   │   ├── doctor.py           # Doctor endpoints
│   │   └── patient.py          # Patient endpoints
│   ├── services/
│   │   ├── discharge_summary.py    # Groq AI integration
│   │   ├── bill_analyzer.py        # OCR & bill analysis
│   │   ├── medicine_analyzer.py    # Medicine price checking
│   │   ├── negotiation.py          # Negotiation suggestions
│   │   └── pdf_generator.py        # PDF generation
│   └── data/
│       ├── cghs_rates.csv          # CGHS reference rates
│       └── medicine_mapping.csv    # Medicine mappings
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── DoctorDashboard.jsx
│   │   │   └── PatientDashboard.jsx
│   │   └── utils/
│   │       └── api.js              # API helper functions
│   └── package.json
└── README.md
```

## 🎨 Screenshots & Usage

### Doctor Workflow
1. Login with doctor credentials
2. Enter patient name and clinical notes
3. Click "Generate Summary" (AI will create structured summary)
4. Edit the summary as needed
5. Add follow-up instructions, diet advice, and red flag symptoms
6. Mark as final when complete
7. Download PDF

### Patient Workflow
1. Login with patient credentials
2. Upload hospital bill (image or PDF)
3. View analysis results:
   - Category-wise bill breakup
   - Overcharged items vs CGHS rates
   - Medicine price analysis (brand vs generic)
   - Negotiation suggestions with patient-friendly wording
4. Download bill analysis report as PDF
5. View discharge summary by entering summary ID
6. Download discharge summary PDF

## 🔒 Security Notes

- This is an MVP/demo application
- Passwords are hashed using bcrypt
- For production use:
  - Implement proper JWT authentication
  - Add HTTPS
  - Use environment-specific configurations
  - Add rate limiting
  - Implement proper file upload validation

## ⚠️ Disclaimer

This system provides decision support and does not replace medical or legal advice. Always consult with qualified healthcare professionals and verify all medical information.

## 📝 Sample Data

The application includes sample CGHS reference rates and medicine mappings in CSV format:
- `backend/data/cghs_rates.csv` - Reference rates for procedures, tests, room charges
- `backend/data/medicine_mapping.csv` - Brand to generic medicine mappings

You can edit these files to add more reference data.

## 🐛 Troubleshooting

### Tesseract OCR Not Found
- Ensure Tesseract is installed and added to system PATH
- Restart your terminal after installation

### Groq API Errors
- Verify your API key is correct in `.env`
- Check your API usage limits at console.groq.com
- The system will fallback to mock summaries if API fails

### Database Issues
- Delete `backend/healthcare.db` and restart the backend to recreate

### CORS Errors
- Ensure backend is running on port 8000
- Frontend API calls are configured for localhost:8000

## 📞 Support

For issues or questions, please check:
1. Tesseract is properly installed
2. Groq API key is configured
3. All dependencies are installed
4. Both frontend and backend servers are running

## 🎓 Academic Use

This project is designed for academic demonstration and evaluation purposes. It showcases:
- Full-stack web development
- REST API design
- AI integration (Groq API)
- OCR and document processing
- Healthcare data analysis
- User-friendly UI/UX design

---

**Built with ❤️ for Healthcare Innovation**
