---
title: Agribuddy Deploy2
emoji: 👁
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
short_description: kvvrr-agribuddy
---

## Agribuddy

AgriBuddy is a Flask-powered assistant that predicts suitable crops, forecasts rainfall, and diagnoses plant health from leaf photos using TensorFlow/Keras models.

## Local Development

1. Create a virtual environment and install the dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. Start the server:
   ```
   python app.py
   ```
3. Visit `http://localhost:7860` and accept the splash screen terms to access all tabs.

## Docker Deployment

1. Build the image locally:
   ```
   docker build -t agribuddy .
   ```
2. Run the container:
   ```
   docker run -p 7860:7860 agribuddy
   ```
3. Open `http://localhost:7860`. Gunicorn serves the Flask app inside the container.

## 🚀 Deployment to Render (Recommended)

**Quick Deploy:**
1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Blueprint" (or "Web Service")
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and deploy

**Manual Setup:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --threads 2 app:app`
- **Health Check Path**: `/healthz`

See `DEPLOYMENT.md` for detailed instructions.

## 🌐 Deployment to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Follow the prompts

**Note**: Render is recommended for this app as it handles ML models better.

## Hugging Face Space

This repo already contains a `dockerfile` and the Space metadata above (`sdk: docker`). To deploy:

1. Create a new Space on Hugging Face with the **Docker** SDK.
2. Push this repository (including large model files in `models/`).
3. Hugging Face automatically builds the Docker image and exposes the app on the default port (the Flask app reads `$PORT`, so no extra config is required).

For reference on optional Space settings, see the [Hugging Face configuration docs](https://huggingface.co/docs/hub/spaces-config-reference).
