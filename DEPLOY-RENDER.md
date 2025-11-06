# Deploy to Render - Step by Step Guide

## Quick Deploy (Recommended)

### 1. Push to GitHub

```bash
cd automatic-job-application-filler
git init
git add .
git commit -m "Initial commit - Auto Form Filler with ATS detection"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 2. Deploy on Render

1. **Go to Render**: https://render.com/
2. **Sign up/Login** with GitHub
3. **Click "New +"** → Select **"Web Service"**

### 3. Configure Web Service

**Connect Repository:**
- Choose your GitHub repository
- Click "Connect"

**Configure Build:**
```
Name: auto-form-filler
Region: Choose closest to you
Branch: main
Root Directory: (leave empty)
Runtime: Python 3
Build Command: bash build.sh
Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
- Free tier (for testing)
- Or Starter ($7/month for production)

### 4. Add Environment Variables (Optional)

If you want AI-powered features, add these in Render dashboard:

```
OPENROUTER_API_KEY=your_key_here
LLAMA_CLOUD_API_KEY=your_key_here
```

### 5. Deploy!

- Click **"Create Web Service"**
- Wait 5-10 minutes for build
- Your app will be live at: `https://your-app-name.onrender.com`

---

## Alternative: Deploy Backend & Frontend Separately

### Option A: Backend on Render, Frontend on Netlify

**Backend on Render:**
1. Follow steps above
2. Note your backend URL: `https://your-backend.onrender.com`

**Frontend on Netlify:**
1. Go to https://netlify.com
2. Drag & drop your `frontend/build` folder
3. Update environment variable:
   - `REACT_APP_API_URL=https://your-backend.onrender.com`
4. Redeploy

### Option B: Both on Render (2 services)

**Backend Service:**
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Frontend Service:**
- Root Directory: `frontend`
- Build Command: `npm ci && npm run build`
- Start Command: `npx serve -s build -l $PORT`
- Add Environment Variable: `REACT_APP_API_URL=https://your-backend.onrender.com`

---

## What Happens During Deployment

1. **Build Phase:**
   - Installs Python dependencies
   - Installs Node.js dependencies
   - Builds React production bundle
   - Takes ~5-10 minutes

2. **Runtime:**
   - Backend serves API at `/api/*`
   - Backend serves frontend static files
   - Single URL for entire app

3. **Health Check:**
   - Render checks `/api/health`
   - Auto-restarts if needed

---

## Troubleshooting

### Build Fails
- Check `build.sh` has Unix line endings (LF not CRLF)
- Run locally: `bash build.sh`

### Frontend Not Loading
- Build frontend locally first: `cd frontend && npm run build`
- Check `frontend/build` folder exists
- Verify `main.py` serves static files correctly

### CORS Errors
- Already configured with `allow_origins=["*"]`
- Should work out of the box

### Slow Response
- Free tier "spins down" after 15 min inactivity
- First request takes ~30 seconds to wake up
- Upgrade to paid tier for always-on

---

## Post-Deployment

### Test Your Deployed App

1. Visit: `https://your-app.onrender.com`
2. Upload a test resume PDF
3. Enter a Google Form URL
4. Submit and verify it works

### Monitor Logs

- Go to Render dashboard
- Click your service
- View "Logs" tab
- Check for errors

### Update Deployment

```bash
git add .
git commit -m "Update"
git push
```

Render auto-deploys on push!

---

## Production Checklist

- [ ] Set custom domain (optional)
- [ ] Add SSL certificate (free with Render)
- [ ] Set environment variables
- [ ] Test with real PDFs
- [ ] Test with real Google Forms
- [ ] Monitor logs for errors
- [ ] Set up health check notifications
- [ ] Consider upgrading to paid tier

---

## Free Tier Limitations

- 750 hours/month free compute
- Spins down after 15 min inactivity
- Slower cold starts
- 512 MB RAM
- Good for testing!

Upgrade to **Starter** ($7/mo) for:
- Always-on service
- Faster performance
- More RAM
- Better for production

---

## Need Help?

- Render Docs: https://render.com/docs
- Check `app.log` for backend errors
- Browser DevTools for frontend errors
- GitHub Issues for this project

---

**Your app is production-ready! 🚀**
