# Firebase Deployment Script for Windows PowerShell
# This script deploys backend to Cloud Run and frontend to Firebase Hosting

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Firebase Deployment...`n" -ForegroundColor Blue

# Check if required tools are installed
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Host "Firebase CLI not found. Installing...`n" -ForegroundColor Yellow
    npm install -g firebase-tools
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Google Cloud SDK not found. Please install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Get project ID
if (Test-Path .firebaserc) {
    $content = Get-Content .firebaserc | ConvertFrom-Json
    $PROJECT_ID = $content.projects.default
} else {
    $PROJECT_ID = Read-Host "Enter your Firebase Project ID"
    @{
        projects = @{
            default = $PROJECT_ID
        }
    } | ConvertTo-Json | Set-Content .firebaserc
}

if (-not $PROJECT_ID -or $PROJECT_ID -eq "your-firebase-project-id") {
    Write-Host "Please set your Firebase Project ID in .firebaserc" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Firebase Project: $PROJECT_ID`n" -ForegroundColor Green

# Check for Groq API key
if (-not $env:GROQ_API_KEY) {
    if (Test-Path backend\.env) {
        $envContent = Get-Content backend\.env
        $groqLine = $envContent | Where-Object { $_ -match "GROQ_API_KEY" }
        if ($groqLine) {
            $env:GROQ_API_KEY = ($groqLine -split '=')[1].Trim().Trim('"')
        }
    }
}

if (-not $env:GROQ_API_KEY -or $env:GROQ_API_KEY -eq "your_groq_api_key_here") {
    Write-Host "⚠️  GROQ_API_KEY not set. Please set it as an environment variable or in backend/.env" -ForegroundColor Yellow
    $env:GROQ_API_KEY = Read-Host "Enter your Groq API Key"
}

# Set Google Cloud project
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "Enabling required Google Cloud APIs...`n" -ForegroundColor Blue
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy Backend to Cloud Run
Write-Host "`n📦 Building and deploying backend to Cloud Run...`n" -ForegroundColor Blue
Set-Location backend

$SERVICE_NAME = "healthcare-backend"
$REGION = "us-central1"

# Build and push Docker image
Write-Host "Building Docker image...`n" -ForegroundColor Blue
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run...`n" -ForegroundColor Blue
gcloud run deploy $SERVICE_NAME `
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --set-env-vars "GROQ_API_KEY=$env:GROQ_API_KEY" `
  --set-env-vars "CORS_ORIGINS=https://$PROJECT_ID.web.app,https://$PROJECT_ID.firebaseapp.com" `
  --set-env-vars "DATABASE_URL=sqlite:///./healthcare.db"

# Get the backend URL
$BACKEND_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
Write-Host "✅ Backend deployed at: $BACKEND_URL`n" -ForegroundColor Green

Set-Location ..

# Update frontend environment
Write-Host "📝 Updating frontend environment...`n" -ForegroundColor Blue
Set-Location frontend

# Create .env file with backend URL
"VITE_API_BASE_URL=$BACKEND_URL" | Set-Content .env
Write-Host "Created .env with VITE_API_BASE_URL=$BACKEND_URL" -ForegroundColor Green

# Build frontend
Write-Host "🔨 Building frontend...`n" -ForegroundColor Blue
npm install
npm run build

Set-Location ..

# Deploy frontend to Firebase Hosting
Write-Host "`n🌐 Deploying frontend to Firebase Hosting...`n" -ForegroundColor Blue
firebase deploy --only hosting

Write-Host "`n✅ Deployment complete!`n" -ForegroundColor Green
Write-Host "Frontend: https://$PROJECT_ID.web.app" -ForegroundColor Green
Write-Host "Backend: $BACKEND_URL" -ForegroundColor Green
Write-Host "`nDon't forget to update CORS_ORIGINS if you have a custom domain!" -ForegroundColor Blue

