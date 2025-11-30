# 🚀 Complete Deployment Guide: GitHub to Render

## Step-by-Step Process from Start to Finish

---

## 📋 **STEP 1: Prepare Your Local Repository**

### 1.1 Check Current Status
Open PowerShell/Terminal in your project folder and run:
```powershell
cd "C:\Users\kvvrr\OneDrive\Agribuddy-Deploy2kvvrr"
git status
```

### 1.2 Initialize Git (if not already done)
```powershell
git init
```

### 1.3 Files You MUST Push to GitHub

✅ **Push These Files:**
- `app.py` - Main application
- `utils.py` - Utility functions
- `requirements.txt` - Dependencies
- `render.yaml` - Render configuration
- `vercel.json` - Vercel configuration (optional)
- `Procfile` - Process file
- `.gitignore` - Git ignore rules
- `.gitattributes` - Git LFS configuration (for large files)
- `README.md` - Documentation
- `DEPLOYMENT.md` - Deployment guide
- `dockerfile` - Docker configuration
- `models/` folder - **ALL model files** (soil_model.h5, plant_disease_model.h5, JSON files)
- `static/` folder - All static files (images, CSS, JS)
- `templates/` folder - HTML templates
- `*.csv` files - All CSV data files
- `*.xlsx` files - Excel data files
- `Uploads/.gitkeep` - Keep folder structure

❌ **DO NOT Push:**
- `__pycache__/` - Python cache (already in .gitignore)
- `Uploads/*.png`, `Uploads/*.jpg` - User uploads (already in .gitignore)
- `.env` files - Environment variables (already in .gitignore)
- `venv/` or `.venv/` - Virtual environment (already in .gitignore)

---

## 📦 **STEP 2: Set Up Git LFS for Large Files**

Your model files (~26MB each) should use Git LFS to avoid issues.

### 2.1 Install Git LFS (if not installed)
Download from: https://git-lfs.github.com/
Or use Chocolatey:
```powershell
choco install git-lfs
```

### 2.2 Initialize Git LFS
```powershell
git lfs install
```

### 2.3 Track .h5 Files with LFS
```powershell
git lfs track "*.h5"
git lfs track "models/*.h5"
```

This will update your `.gitattributes` file automatically.

---

## 🔵 **STEP 3: Create GitHub Repository**

### 3.1 Go to GitHub
1. Open https://github.com
2. Sign in to your account
3. Click the **"+"** icon in the top right
4. Select **"New repository"**

### 3.2 Repository Settings
- **Repository name**: `agribuddy` (or any name you prefer)
- **Description**: "AgriBuddy - Flask ML App for Crop Recommendations"
- **Visibility**: Choose **Public** (free) or **Private** (if you have GitHub Pro)
- **DO NOT** initialize with README, .gitignore, or license (we already have these)
- Click **"Create repository"**

### 3.3 Copy Repository URL
After creating, GitHub will show you the repository URL. Copy it (it looks like):
```
https://github.com/yourusername/agribuddy.git
```

---

## 📤 **STEP 4: Push Code to GitHub**

### 4.1 Add All Files
```powershell
git add .
```

### 4.2 Check What Will Be Committed
```powershell
git status
```

You should see:
- ✅ All Python files
- ✅ All model files (models/*.h5)
- ✅ All static files
- ✅ All configuration files
- ❌ No __pycache__, venv, or .env files

### 4.3 Commit Files
```powershell
git commit -m "Initial commit: Agribuddy Flask app ready for Render deployment"
```

### 4.4 Add Remote Repository
Replace `yourusername` and `agribuddy` with your actual GitHub username and repo name:
```powershell
git remote add origin https://github.com/yourusername/agribuddy.git
```

### 4.5 Push to GitHub
```powershell
git branch -M main
git push -u origin main
```

**Note**: If you get authentication errors:
- Use GitHub Personal Access Token instead of password
- Or use GitHub Desktop app for easier authentication

### 4.6 Verify Upload
1. Go to your GitHub repository page
2. Check that all files are there:
   - ✅ `app.py`
   - ✅ `models/` folder with `.h5` files
   - ✅ `static/` folder
   - ✅ `templates/` folder
   - ✅ `render.yaml`

---

## 🎨 **STEP 5: Deploy to Render**

### 5.1 Create Render Account
1. Go to https://render.com
2. Click **"Get Started for Free"**
3. Sign up with your GitHub account (recommended) or email

### 5.2 Create New Web Service

#### Option A: Using Blueprint (Automatic - Recommended)
1. In Render Dashboard, click **"New +"** → **"Blueprint"**
2. Click **"Connect account"** and authorize GitHub
3. Select your repository: `yourusername/agribuddy`
4. Render will automatically detect `render.yaml`
5. Click **"Apply"**
6. Render will create the service automatically

#### Option B: Manual Setup
1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub account (if not connected)
3. Select your repository: `yourusername/agribuddy`
4. Configure:
   - **Name**: `agribuddy` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty (root folder)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --threads 2 app:app`
   - **Plan**: Choose **Free** (or paid if you need more resources)
5. Click **"Create Web Service"**

### 5.3 Configure Environment Variables
Render will automatically set:
- `PORT` - Automatically set by Render
- `PYTHON_VERSION` - From render.yaml

**No additional environment variables needed!**

### 5.4 Monitor Deployment
1. Render will start building your app
2. Watch the build logs:
   - Installing dependencies
   - Building application
   - Starting service
3. Build time: ~5-10 minutes (first time)
4. You'll see logs like:
   ```
   Installing dependencies...
   Building application...
   Starting service...
   ```

### 5.5 Check Health
1. Once deployed, Render will show a URL like: `https://agribuddy.onrender.com`
2. Test health endpoint: `https://agribuddy.onrender.com/healthz`
   - Should return: `{"status": "ok"}`
3. Visit main URL: `https://agribuddy.onrender.com`
   - Your app should load!

---

## ✅ **STEP 6: Verify Deployment**

### 6.1 Test All Features
1. **Home Page**: Should load correctly
2. **Crop Recommendation**: Upload soil image, select state
3. **Rainfall Prediction**: Enter subdivision, year, month
4. **Plant Health**: Upload leaf image

### 6.2 Check Logs
In Render Dashboard:
1. Go to your service
2. Click **"Logs"** tab
3. Check for any errors
4. Look for: "Soil model loaded successfully"

### 6.3 Common Issues & Fixes

**Issue**: Models not loading
- **Fix**: Check that `models/` folder is in GitHub repository
- **Fix**: Verify model files are committed (not in .gitignore)

**Issue**: Build fails
- **Fix**: Check `requirements.txt` has all dependencies
- **Fix**: Check Render logs for specific error

**Issue**: App crashes on startup
- **Fix**: Check PORT is set correctly (should be automatic)
- **Fix**: Check gunicorn command in render.yaml

---

## 📝 **STEP 7: Post-Deployment**

### 7.1 Update Render Settings (Optional)
- **Auto-Deploy**: Enabled by default (deploys on every push)
- **Health Check**: Already configured (`/healthz`)
- **Environment**: Production

### 7.2 Custom Domain (Optional)
1. In Render Dashboard → Your Service → Settings
2. Scroll to "Custom Domain"
3. Add your domain
4. Follow DNS configuration instructions

### 7.3 Monitor Usage
- Free tier: 750 hours/month
- App sleeps after 15 minutes of inactivity (free tier)
- First request after sleep takes ~30 seconds (cold start)

---

## 🎯 **Quick Reference Commands**

### Local Development
```powershell
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Access at http://localhost:7860
```

### Git Commands
```powershell
# Check status
git status

# Add files
git add .

# Commit
git commit -m "Your message"

# Push to GitHub
git push origin main
```

### Render Dashboard
- URL: https://dashboard.render.com
- View logs: Service → Logs tab
- View metrics: Service → Metrics tab
- Restart service: Service → Manual Deploy → Clear build cache & deploy

---

## 📞 **Need Help?**

### Render Support
- Documentation: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Common Render URLs
- Your app: `https://your-app-name.onrender.com`
- Health check: `https://your-app-name.onrender.com/healthz`

---

## ✅ **Checklist Before Deployment**

- [ ] All files committed to Git
- [ ] Model files (.h5) are in repository
- [ ] `render.yaml` is in root directory
- [ ] `requirements.txt` is up to date
- [ ] `.gitignore` excludes unnecessary files
- [ ] GitHub repository is public or Render has access
- [ ] Git LFS is set up (for large files)

---

## 🎉 **You're Done!**

Your app should now be live at: `https://your-app-name.onrender.com`

**Next Steps:**
1. Share your app URL
2. Monitor usage in Render Dashboard
3. Set up custom domain (optional)
4. Upgrade plan if needed (for no sleep, more resources)

---

**Good Luck with Your Deployment! 🚀**

