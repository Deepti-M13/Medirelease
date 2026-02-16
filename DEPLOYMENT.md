# Deployment Guide

This guide covers deploying the Healthcare Web Application to various platforms.

## 📋 Prerequisites

- **Backend**: Python 3.8+, Groq API key, Tesseract OCR
- **Frontend**: Node.js 16+, npm/yarn
- **Database**: SQLite (included) or PostgreSQL (for production)

## 🔧 Pre-Deployment Setup

### 1. Environment Variables

#### Backend (.env file)
Create `backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./healthcare.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/dbname
```

#### Frontend (.env file)
Create `frontend/.env`:
```env
VITE_API_BASE_URL=https://your-backend-url.com
```

### 2. Update CORS Settings

In `backend/app.py`, update CORS origins:
```python
allow_origins=["https://your-frontend-url.com"]  # Replace "*" in production
```

---

## 🚀 Deployment Options

### Option 1: Railway (Recommended - Easiest)

Railway supports both backend and frontend deployment.

#### Backend Deployment:

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Initialize Project**:
   ```bash
   cd backend
   railway init
   ```

3. **Create `railway.json`** (already created):
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "uvicorn app:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

4. **Set Environment Variables**:
   - Go to Railway dashboard → Variables
   - Add: `GROQ_API_KEY=your_key`
   - Add: `PORT=8000` (Railway auto-assigns, but set for clarity)

5. **Deploy**:
   ```bash
   railway up
   ```

#### Frontend Deployment:

1. **Build the frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Railway**:
   - Create new service in Railway
   - Connect to your frontend repo/folder
   - Set build command: `npm install && npm run build`
   - Set start command: `npx serve -s dist -l $PORT`
   - Add environment variable: `VITE_API_BASE_URL=https://your-backend.railway.app`

3. **Alternative: Deploy to Vercel** (see Option 2)

---

### Option 2: Vercel (Frontend) + Railway/Render (Backend)

#### Frontend on Vercel:

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   cd frontend
   vercel
   ```

3. **Set Environment Variables**:
   - In Vercel dashboard → Settings → Environment Variables
   - Add: `VITE_API_BASE_URL=https://your-backend-url.com`

4. **Configure `vercel.json`** (already created):
   ```json
   {
     "rewrites": [
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```

#### Backend on Railway/Render:
Follow Option 1 backend steps, or see Option 3 for Render.

---

### Option 3: Render

#### Backend Deployment:

1. **Create `render.yaml`** (already created):
   ```yaml
   services:
     - type: web
       name: healthcare-backend
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: GROQ_API_KEY
           sync: false
         - key: DATABASE_URL
           value: sqlite:///./healthcare.db
   ```

2. **Deploy**:
   - Connect your GitHub repo to Render
   - Select the backend directory
   - Set environment variables in dashboard
   - Deploy

#### Frontend Deployment:

1. **Create Static Site**:
   - In Render dashboard, create new "Static Site"
   - Connect frontend directory
   - Build command: `npm install && npm run build`
   - Publish directory: `dist`
   - Add environment variable: `VITE_API_BASE_URL`

---

### Option 4: Docker Deployment

#### Backend Dockerfile:

1. **Create `backend/Dockerfile`** (already created):
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       tesseract-ocr \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Install Playwright browsers
   RUN playwright install chromium
   RUN playwright install-deps chromium
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build and Run**:
   ```bash
   cd backend
   docker build -t healthcare-backend .
   docker run -p 8000:8000 --env-file .env healthcare-backend
   ```

#### Frontend Dockerfile:

1. **Create `frontend/Dockerfile`** (already created):
   ```dockerfile
   FROM node:18-alpine as build
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   ARG VITE_API_BASE_URL
   ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
   RUN npm run build
   
   FROM nginx:alpine
   COPY --from=build /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

2. **Docker Compose** (already created):
   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       env_file:
         - ./backend/.env
       volumes:
         - ./backend/uploads:/app/uploads
         - ./backend/healthcare.db:/app/healthcare.db
     
     frontend:
       build:
         context: ./frontend
         args:
           VITE_API_BASE_URL: http://localhost:8000
       ports:
         - "80:80"
       depends_on:
         - backend
   ```

---

### Option 5: AWS/GCP/Azure

#### AWS Elastic Beanstalk (Backend):

1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init`
3. Create environment: `eb create`
4. Deploy: `eb deploy`

#### AWS S3 + CloudFront (Frontend):

1. Build: `npm run build`
2. Upload `dist/` to S3 bucket
3. Configure CloudFront distribution
4. Set environment variables in build process

---

## 🔐 Security Considerations

### Production Checklist:

- [ ] Change CORS origins from `["*"]` to specific domain
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (most platforms do this automatically)
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Set up proper authentication (JWT tokens)
- [ ] Add rate limiting
- [ ] Enable file upload size limits
- [ ] Set up proper logging and monitoring

### Database Migration (SQLite → PostgreSQL):

1. **Update `database.py`**:
   ```python
   # Use environment variable
   DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")
   
   if DATABASE_URL.startswith("postgresql"):
       engine = create_engine(DATABASE_URL)
   else:
       engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
   ```

2. **Migrate data**:
   ```bash
   # Export from SQLite
   sqlite3 healthcare.db .dump > backup.sql
   
   # Import to PostgreSQL (adjust as needed)
   psql -d healthcare_db -f backup.sql
   ```

---

## 📝 Post-Deployment

### 1. Verify Deployment:

- Backend health check: `https://your-backend.com/api/health`
- Frontend: `https://your-frontend.com`
- Test login with demo credentials

### 2. Monitor Logs:

- Railway: Dashboard → Logs
- Render: Dashboard → Logs
- Vercel: Dashboard → Logs

### 3. Set Up Custom Domain (Optional):

- Railway: Settings → Domains
- Vercel: Settings → Domains
- Update CORS and environment variables accordingly

---

## 🐛 Troubleshooting

### Backend Issues:

**Playwright not working:**
- Ensure Chromium is installed: `playwright install chromium`
- For Docker, use the provided Dockerfile

**Tesseract OCR not found:**
- Install system package: `apt-get install tesseract-ocr` (Linux)
- For Docker, it's included in Dockerfile

**Database errors:**
- Ensure write permissions for SQLite file
- For PostgreSQL, check connection string

### Frontend Issues:

**API calls failing:**
- Check `VITE_API_BASE_URL` environment variable
- Verify CORS settings on backend
- Check browser console for errors

**Build errors:**
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version (16+)

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [Render Docs](https://render.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)

---

## 🎯 Quick Start (Railway - Recommended)

1. **Backend**:
   ```bash
   cd backend
   railway login
   railway init
   railway add --plugin postgresql  # Optional: for production DB
   railway variables set GROQ_API_KEY=your_key
   railway up
   ```

2. **Frontend**:
   ```bash
   cd frontend
   # Set VITE_API_BASE_URL to your Railway backend URL
   railway init
   railway up
   ```

That's it! Your app should be live. 🚀

