# 🌐 Cross-Cloud Deployment Guide

## 🚀 Backend on AWS ECS + Frontend on Other Cloud

### **1. Deploy Backend to AWS ECS**
```bash
# Setup AWS infrastructure
export OPENROUTER_API_KEY="your_key"
export LLAMA_CLOUD_API_KEY="your_key"
./aws/setup-infrastructure.sh

# Deploy backend
./aws/deploy-demo.sh

# Get backend public IP
aws ecs describe-tasks --cluster auto-form-filler-cluster \
  --tasks $(aws ecs list-tasks --cluster auto-form-filler-cluster \
  --service-name auto-form-filler-demo --query 'taskArns[0]' --output text) \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text | xargs -I {} aws ec2 describe-network-interfaces \
  --network-interface-ids {} --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text
```

### **2. Configure Frontend for Cross-Origin**

#### **Update .env.production:**
```bash
# Replace with your ECS public IP
REACT_APP_API_URL=http://54.123.45.67:8000
```

#### **Deploy Frontend to Any Cloud:**

**Vercel:**
```bash
npm install -g vercel
vercel --prod
# Set environment variable: REACT_APP_API_URL=http://YOUR_ECS_IP:8000
```

**Netlify:**
```bash
npm run build
# Upload build/ folder to Netlify
# Set environment variable: REACT_APP_API_URL=http://YOUR_ECS_IP:8000
```

**Firebase Hosting:**
```bash
npm install -g firebase-tools
npm run build
firebase deploy
# Set environment variable in Firebase console
```

### **3. CORS Configuration**

#### **Backend (Automatic):**
- ✅ **Allows all origins** for cross-cloud deployment
- ✅ **Environment configurable** via `ALLOWED_ORIGINS`
- ✅ **Proper headers** for cross-origin requests

#### **Frontend (Automatic):**
- ✅ **Dynamic API URL** from environment variables
- ✅ **Timeout handling** for network requests
- ✅ **Proper headers** for API calls

### **4. Security Considerations**

#### **Production CORS (Recommended):**
```bash
# In ECS task definition, add environment variable:
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

#### **HTTPS Setup (Recommended):**
```bash
# Use CloudFront + ACM for HTTPS on backend
# Use cloud provider's HTTPS for frontend
```

## 🔧 **Troubleshooting CORS**

### **Common Issues:**
1. **Mixed Content** - Use HTTPS for both frontend and backend
2. **Preflight Requests** - Backend handles OPTIONS automatically
3. **Credentials** - Set to false for wildcard origins

### **Testing CORS:**
```bash
# Test from browser console
fetch('http://YOUR_ECS_IP:8000/api/health')
  .then(r => r.json())
  .then(console.log)
```

## 💰 **Cost Breakdown:**
- **AWS ECS Backend**: ~$4.74/month
- **Frontend Hosting**: 
  - Vercel: FREE (hobby plan)
  - Netlify: FREE (starter plan)
  - Firebase: FREE (spark plan)

**Total Cost: ~$5/month** for full cross-cloud deployment! 🎉