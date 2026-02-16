# Deploy to Firebase - Ready to Go! 🚀

Your Firebase project is configured: **medirelease**

## Quick Deploy Steps:

### 1. Install Required Tools (if not already installed)

```bash
npm install -g firebase-tools
```

Download and install Google Cloud SDK: https://cloud.google.com/sdk/docs/install

### 2. Login to Firebase and Google Cloud

```bash
firebase login
gcloud auth login
gcloud config set project medirelease
```

### 3. Set Your Groq API Key

**Option A: Environment Variable (Recommended)**
```bash
# Windows PowerShell
$env:GROQ_API_KEY = "your_groq_api_key_here"

# Linux/Mac
export GROQ_API_KEY=your_groq_api_key_here
```

**Option B: In backend/.env file**
```
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Deploy!

**Windows:**
```powershell
cd ant\ant\healthcare-app
.\deploy-firebase.ps1
```

**Linux/Mac:**
```bash
cd ant/ant/healthcare-app
chmod +x deploy-firebase.sh
./deploy-firebase.sh
```

### 5. Access Your App

After deployment completes, your app will be live at:
- **Frontend**: https://medirelease.web.app
- **Backend**: URL will be shown after Cloud Run deployment

---

## Manual Deployment (Alternative)

If the script doesn't work, follow these steps:

### Backend Deployment:

```bash
cd backend

# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/medirelease/healthcare-backend
gcloud run deploy healthcare-backend \
  --image gcr.io/medirelease/healthcare-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars GROQ_API_KEY=your_groq_api_key_here \
  --set-env-vars CORS_ORIGINS=https://medirelease.web.app,https://medirelease.firebaseapp.com

# Copy the backend URL that appears
```

### Frontend Deployment:

```bash
cd frontend

# Create .env with your backend URL (from above)
echo "VITE_API_BASE_URL=https://healthcare-backend-xxxxx-uc.a.run.app" > .env

# Build
npm install
npm run build

# Deploy
cd ..
firebase deploy --only hosting
```

---

## Important Notes:

1. ✅ Your Firebase project ID is already set: **medirelease**
2. ✅ Groq API usage is unchanged - just set the key as environment variable
3. ✅ CORS is automatically configured for your Firebase domains
4. ✅ Frontend will be at: https://medirelease.web.app

---

## Troubleshooting:

**"Permission denied" errors:**
```bash
gcloud auth login
gcloud config set project medirelease
```

**"Project not found":**
- Make sure you're logged into the correct Google account
- Verify project ID in Firebase Console

**Build fails:**
- Check that Dockerfile exists in `backend/` directory
- Ensure all dependencies are in `requirements.txt`

---

Your app is ready to deploy! 🎉

