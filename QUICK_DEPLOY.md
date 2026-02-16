# Quick Deployment Guide

## 🚀 Fastest Way: Railway (5 minutes)

### Backend:
```bash
cd backend
railway login
railway init
railway variables set GROQ_API_KEY=your_key_here
railway up
```
Copy the backend URL (e.g., `https://your-app.railway.app`)

### Frontend:
```bash
cd frontend
# Create .env file with:
# VITE_API_BASE_URL=https://your-backend.railway.app
railway init
railway up
```

Done! 🎉

---

## Alternative: Vercel (Frontend) + Railway (Backend)

### Backend (Railway):
Same as above.

### Frontend (Vercel):
```bash
cd frontend
# Create .env file:
# VITE_API_BASE_URL=https://your-backend.railway.app
vercel
```

---

## Docker (Local/Server)

```bash
# Set environment variables in backend/.env
docker-compose up -d
```

Access at: `http://localhost` (frontend) and `http://localhost:8000` (backend)

---

## Environment Variables Needed

### Backend (.env):
```
GROQ_API_KEY=your_key
CORS_ORIGINS=https://your-frontend-url.com
```

### Frontend (.env):
```
VITE_API_BASE_URL=https://your-backend-url.com
```

---

For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

