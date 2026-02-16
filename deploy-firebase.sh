#!/bin/bash

# Firebase Deployment Script for Healthcare App
# This script deploys backend to Cloud Run and frontend to Firebase Hosting

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Firebase Deployment...${NC}\n"

# Check if required tools are installed
if ! command -v firebase &> /dev/null; then
    echo -e "${YELLOW}Firebase CLI not found. Installing...${NC}"
    npm install -g firebase-tools
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Google Cloud SDK not found. Please install from: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Get project ID
if [ -f .firebaserc ]; then
    PROJECT_ID=$(grep -o '"default": "[^"]*"' .firebaserc | cut -d'"' -f4)
else
    read -p "Enter your Firebase Project ID: " PROJECT_ID
    echo "{\"projects\": {\"default\": \"$PROJECT_ID\"}}" > .firebaserc
fi

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "your-firebase-project-id" ]; then
    echo -e "${YELLOW}Please set your Firebase Project ID in .firebaserc${NC}"
    exit 1
fi

echo -e "${GREEN}Using Firebase Project: $PROJECT_ID${NC}\n"

# Check for Groq API key
if [ -z "$GROQ_API_KEY" ]; then
    if [ -f backend/.env ]; then
        GROQ_API_KEY=$(grep "GROQ_API_KEY" backend/.env | cut -d'=' -f2 | tr -d ' "')
    fi
fi

if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "your_groq_api_key_here" ]; then
    echo -e "${YELLOW}⚠️  GROQ_API_KEY not set. Please set it as an environment variable or in backend/.env${NC}"
    read -p "Enter your Groq API Key: " GROQ_API_KEY
fi

# Set Google Cloud project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}Enabling required Google Cloud APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy Backend to Cloud Run
echo -e "\n${BLUE}📦 Building and deploying backend to Cloud Run...${NC}"
cd backend

SERVICE_NAME="healthcare-backend"
REGION="us-central1"

# Build and push Docker image
echo -e "${BLUE}Building Docker image...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars GROQ_API_KEY=$GROQ_API_KEY \
  --set-env-vars CORS_ORIGINS=https://$PROJECT_ID.web.app,https://$PROJECT_ID.firebaseapp.com \
  --set-env-vars DATABASE_URL=sqlite:///./healthcare.db

# Get the backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Backend deployed at: $BACKEND_URL${NC}\n"

cd ..

# Update frontend environment
echo -e "${BLUE}📝 Updating frontend environment...${NC}"
cd frontend

# Create .env file with backend URL
echo "VITE_API_BASE_URL=$BACKEND_URL" > .env
echo -e "${GREEN}Created .env with VITE_API_BASE_URL=$BACKEND_URL${NC}"

# Build frontend
echo -e "${BLUE}🔨 Building frontend...${NC}"
npm install
npm run build

cd ..

# Deploy frontend to Firebase Hosting
echo -e "\n${BLUE}🌐 Deploying frontend to Firebase Hosting...${NC}"
firebase deploy --only hosting

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}Frontend: https://$PROJECT_ID.web.app${NC}"
echo -e "${GREEN}Backend: $BACKEND_URL${NC}"
echo -e "\n${BLUE}Don't forget to update CORS_ORIGINS if you have a custom domain!${NC}"

