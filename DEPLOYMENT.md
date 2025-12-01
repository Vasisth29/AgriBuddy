# Deployment Guide for Agribuddy

This app is now ready to deploy on **Render** or **Vercel**.

## 🚀 Quick Deploy to Render

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and deploy

### Option 2: Manual Setup
1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: agribuddy (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --threads 2 app:app`
   - **Health Check Path**: `/healthz`
6. Click "Create Web Service"

### Important Notes for Render:
- The app will automatically use the PORT environment variable
- Health check endpoint is available at `/healthz`
- Model files in `models/` folder will be included in deployment
- Uploads folder will be created automatically

## 🌐 Deploy to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Follow the prompts, or use:
   ```bash
   vercel --prod
   ```

**Note**: Vercel is better suited for serverless functions. For Flask apps with ML models, **Render is recommended** as it provides persistent storage and better handling of large model files.

## 📋 Pre-Deployment Checklist

- ✅ All files moved to root directory
- ✅ `render.yaml` created for Render
- ✅ `vercel.json` created for Vercel
- ✅ `Procfile` created for Heroku compatibility
- ✅ `.gitignore` configured
- ✅ App configured to read PORT from environment
- ✅ Debug mode disabled in production

## 🔧 Environment Variables

No environment variables are required by default. The app will:
- Use PORT from Render/Vercel automatically
- Create Uploads folder automatically
- Load models from `models/` directory

## 📁 Project Structure

```
.
├── app.py                 # Main Flask application
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── vercel.json           # Vercel deployment config
├── Procfile              # Heroku/Render process file
├── models/               # ML models (soil_model.h5, plant_disease_model.h5)
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
└── Uploads/              # User uploads (created automatically)
```

## 🐛 Troubleshooting

### If deployment fails:
1. Check that all model files are committed to Git
2. Verify requirements.txt has all dependencies
3. Check Render/Vercel logs for specific errors
4. Ensure PORT environment variable is set (should be automatic)

### If models don't load:
- Verify `models/` folder is in the repository
- Check file paths in app.py are relative (they are)
- Ensure model files are not in .gitignore

## 🎯 Recommended: Render

For this Flask app with ML models, **Render is the best choice** because:
- Better handling of large model files
- Persistent file system
- More suitable for long-running processes
- Better for ML/AI applications


