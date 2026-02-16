# Firebase Deployment - Quick Start

## 🚀 Fastest Way to Deploy (5 minutes)

### Prerequisites:
1. Install Firebase CLI: `npm install -g firebase-tools`
2. Install Google Cloud SDK: [Download here](https://cloud.google.com/sdk/docs/install)
3. Login to both:
   ```bash
   firebase login
   gcloud auth login
   ```

### Step 1: Initialize Firebase
```bash
cd ant/ant/healthcare-app
firebase init
```
- Select **Hosting**
- Choose/create your Firebase project
- Set public directory: `frontend/dist`
- Configure as single-page app: **Yes**

### Step 2: Update .firebaserc
Edit `.firebaserc` and replace `your-firebase-project-id` with your actual project ID.

### Step 3: Deploy (Choose one method)

#### Option A: Automated Script (Recommended)
**Windows:**
```powershell
.\deploy-firebase.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy-firebase.sh
./deploy-firebase.sh
```

#### Option B: Manual Steps

**1. Deploy Backend:**
```bash
cd backend

# Set your project ID
export PROJECT_ID=your-firebase-project-id
export GROQ_API_KEY=your_groq_key_here

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/healthcare-backend
gcloud run deploy healthcare-backend \
  --image gcr.io/$PROJECT_ID/healthcare-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=$GROQ_API_KEY \
  --set-env-vars CORS_ORIGINS=https://$PROJECT_ID.web.app

# Copy the backend URL that's displayed
```

**2. Update Frontend:**
```bash
cd ../frontend
echo "VITE_API_BASE_URL=https://your-backend-url-here" > .env
npm run build
```

**3. Deploy Frontend:**
```bash
cd ..
firebase deploy --only hosting
```

### Done! 🎉
Your app is live at: `https://your-project-id.web.app`

---

## 📝 Important Notes

1. **Groq API Key**: Your existing Groq usage is unchanged - just set it as an environment variable in Cloud Run
2. **CORS**: Backend automatically allows your Firebase Hosting URLs
3. **Database**: Uses SQLite by default (data persists in Cloud Run container)

---

## 🔄 Updating Deployment

After making changes:

**Backend changes:**
```bash
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/healthcare-backend
gcloud run deploy healthcare-backend --image gcr.io/YOUR_PROJECT_ID/healthcare-backend
```

**Frontend changes:**
```bash
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

---

## 🐛 Troubleshooting

**"Permission denied" errors:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**Build fails:**
- Check that Dockerfile is in `backend/` directory
- Ensure all dependencies are in `requirements.txt`

**Frontend can't connect to backend:**
- Verify `VITE_API_BASE_URL` in `frontend/.env` matches your Cloud Run URL
- Check CORS settings in backend environment variables

---

For detailed instructions, see [FIREBASE_DEPLOYMENT.md](./FIREBASE_DEPLOYMENT.md)

