# Firebase Deployment Guide

This guide covers deploying the Healthcare Web Application using Firebase Hosting (frontend) and Firebase Cloud Run (backend).

## 📋 Prerequisites

1. **Firebase Account**: Sign up at [firebase.google.com](https://firebase.google.com)
2. **Firebase CLI**: Install globally
   ```bash
   npm install -g firebase-tools
   ```
3. **Google Cloud Account**: Required for Cloud Run (linked with Firebase)
4. **Groq API Key**: Keep your existing Groq API key (no changes needed)

---

## 🚀 Step-by-Step Deployment

### Step 1: Initialize Firebase

```bash
cd ant/ant/healthcare-app
firebase login
firebase init
```

When prompted:
- Select **Hosting** and **Cloud Run** (if available)
- Choose or create a Firebase project
- For hosting: Set public directory to `frontend/dist`
- For Cloud Run: We'll configure manually

---

### Step 2: Deploy Backend to Firebase Cloud Run

Firebase Cloud Run uses Docker containers. We'll use the existing Dockerfile.

#### Option A: Using Google Cloud Console

1. **Build and Push Docker Image**:
   ```bash
   cd backend
   
   # Set your project ID
   export PROJECT_ID=your-firebase-project-id
   export SERVICE_NAME=healthcare-backend
   
   # Build the image
   docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .
   
   # Push to Google Container Registry
   gcloud auth configure-docker
   docker push gcr.io/$PROJECT_ID/$SERVICE_NAME
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy $SERVICE_NAME \
     --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GROQ_API_KEY=your_groq_api_key_here \
     --set-env-vars CORS_ORIGINS=https://your-firebase-project-id.web.app
   ```

3. **Get the Backend URL**:
   After deployment, you'll get a URL like:
   `https://healthcare-backend-xxxxx-uc.a.run.app`
   Copy this URL!

#### Option B: Using Firebase CLI (if Cloud Run extension is available)

```bash
firebase deploy --only functions:healthcareBackend
```

---

### Step 3: Configure Frontend Environment

1. **Create frontend/.env file**:
   ```bash
   cd frontend
   ```

   Create `.env` file with your Cloud Run backend URL:
   ```env
   VITE_API_BASE_URL=https://healthcare-backend-xxxxx-uc.a.run.app
   ```

2. **Build the frontend**:
   ```bash
   npm install
   npm run build
   ```

   This creates the `dist/` folder with production files.

---

### Step 4: Deploy Frontend to Firebase Hosting

```bash
# From project root
firebase deploy --only hosting
```

Your app will be live at: `https://your-firebase-project-id.web.app`

---

## 🔧 Alternative: Backend on Cloud Run (Manual Setup)

If you prefer to set up Cloud Run manually:

### 1. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Build and Deploy

```bash
cd backend

# Set variables
export PROJECT_ID=your-firebase-project-id
export SERVICE_NAME=healthcare-backend
export REGION=us-central1

# Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars GROQ_API_KEY=your_groq_api_key_here \
  --set-env-vars CORS_ORIGINS=https://your-firebase-project-id.web.app,https://your-firebase-project-id.firebaseapp.com
```

### 3. Update Frontend Environment

Update `frontend/.env` with the Cloud Run URL and rebuild:
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

## 📝 Environment Variables

### Backend (Cloud Run):
- `GROQ_API_KEY` - Your Groq API key (unchanged)
- `CORS_ORIGINS` - Your Firebase Hosting URLs (comma-separated)
- `DATABASE_URL` - Optional: For PostgreSQL (defaults to SQLite)

### Frontend (.env before build):
- `VITE_API_BASE_URL` - Your Cloud Run backend URL

---

## 🔄 Update Deployment Script

Create `deploy.sh` for easy redeployment:

```bash
#!/bin/bash

# Backend deployment
cd backend
export PROJECT_ID=your-firebase-project-id
export SERVICE_NAME=healthcare-backend

gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=$GROQ_API_KEY \
  --set-env-vars CORS_ORIGINS=https://your-firebase-project-id.web.app

# Frontend deployment
cd ../frontend
npm run build
cd ..
firebase deploy --only hosting
```

Make it executable:
```bash
chmod +x deploy.sh
```

---

## 🐛 Troubleshooting

### Backend Issues:

**"Permission denied" errors:**
```bash
gcloud auth login
gcloud config set project your-firebase-project-id
```

**Playwright/Chromium not working:**
- The Dockerfile includes Playwright installation
- Ensure Cloud Run has enough memory (2Gi recommended)

**Tesseract OCR not found:**
- Already included in Dockerfile
- If issues persist, check Cloud Run logs

### Frontend Issues:

**API calls failing:**
- Check `VITE_API_BASE_URL` in `.env` before building
- Verify CORS settings in backend
- Check browser console for errors

**Build errors:**
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

### CORS Errors:

Update backend CORS_ORIGINS to include:
- `https://your-project-id.web.app`
- `https://your-project-id.firebaseapp.com`
- Your custom domain (if configured)

---

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Store in Cloud Run environment variables (not in code)
3. **CORS**: Restrict to your Firebase domains only
4. **HTTPS**: Firebase Hosting provides HTTPS automatically
5. **Database**: Consider PostgreSQL for production (Cloud SQL)

---

## 📊 Monitoring

### View Logs:

**Backend (Cloud Run)**:
```bash
gcloud run services logs read healthcare-backend --region us-central1
```

**Frontend (Firebase Hosting)**:
- Firebase Console → Hosting → View logs

### Set Up Alerts:

1. Go to Google Cloud Console
2. Navigate to Cloud Run → your service
3. Set up monitoring and alerts

---

## 💰 Cost Considerations

### Firebase Hosting:
- Free tier: 10 GB storage, 360 MB/day transfer
- Paid: $0.026/GB storage, $0.15/GB transfer

### Cloud Run:
- Free tier: 2 million requests/month
- Paid: $0.40 per million requests + compute costs
- Memory/CPU: Pay for what you use

**Estimated monthly cost for small app**: $0-10 (within free tiers)

---

## 🚀 Quick Deploy Commands

```bash
# 1. Build and deploy backend
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/healthcare-backend
gcloud run deploy healthcare-backend \
  --image gcr.io/YOUR_PROJECT_ID/healthcare-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=YOUR_KEY,CORS_ORIGINS=https://YOUR_PROJECT.web.app

# 2. Update frontend .env with backend URL
cd ../frontend
echo "VITE_API_BASE_URL=https://healthcare-backend-xxxxx-uc.a.run.app" > .env

# 3. Build and deploy frontend
npm run build
cd ..
firebase deploy --only hosting
```

---

## 📚 Additional Resources

- [Firebase Hosting Docs](https://firebase.google.com/docs/hosting)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Firebase CLI Reference](https://firebase.google.com/docs/cli)

---

**Note**: Groq API usage remains unchanged. All existing Groq integrations will work as-is in the deployed environment.

