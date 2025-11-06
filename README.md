# 🤖 Auto Form Filling GenAI Agent

A smart application that automatically fills Google Forms using your resume data with AI-powered field mapping.

## ✨ Features

- 📄 **Resume Parsing**: Supports PDF, DOCX, and TXT formats
- 🧠 **AI-Powered**: Uses OpenRouter and Llama Cloud APIs for intelligent data extraction
- 🎯 **Smart Form Filling**: Automatically maps resume data to Google Form fields
- 🚀 **Direct Submission**: Submits forms without browser automation
- 💻 **User-Friendly**: Clean React interface with drag-and-drop upload

## 🛠️ Tech Stack

**Backend**: FastAPI, OpenRouter API, Llama Cloud API, Google Forms API  
**Frontend**: React 18, Axios, Bootstrap  
**AI Libraries**: LlamaIndex, OpenRouter LLM

## 🚀 Quick Start Guide

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker and Docker Compose installed
- Git installed

#### Steps
1. Clone the repository:
```bash
git clone <your-repo-url>
cd auto-form-filling-agent
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Add your API keys to `.env`:
```
OPENROUTER_API_KEY=your_openrouter_key_here
LLAMA_CLOUD_API_KEY=your_llama_cloud_key_here
```

4. Run with Docker:
```bash
docker-compose up --build
```

✅ **Application running at:**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

### Option 2: Manual Setup

#### Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- Git installed

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd auto-form-filling-agent
```

### Step 2: Get API Keys (Required)

#### OpenRouter API Key (Free)
1. Go to [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for a free account
3. Go to "Keys" section
4. Create a new API key
5. Copy the key (starts with `sk-or-v1-...`)

#### Llama Cloud API Key (Free)
1. Go to [Llama Cloud](https://cloud.llamaindex.ai/)
2. Sign up for a free account
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `llx-...`)

### Step 3: Setup Backend

#### Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# Or on Windows
venv\Scripts\activate
```

#### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in the `backend` folder:
```bash
cd backend
touch .env
```

Add your API keys to `.env`:
```
OPENROUTER_API_KEY=your_openrouter_key_here
LLAMA_CLOUD_API_KEY=your_llama_cloud_key_here
```

#### Start Backend Server
```bash
python main.py
```
✅ Backend running at: `http://localhost:8000`

### Step 4: Setup Frontend

#### Install Dependencies
```bash
# Open new terminal
cd frontend
npm install
```

#### Start Frontend
```bash
npm start
```
✅ Frontend running at: `http://localhost:3000`

### Option 3: AWS ECS Deployment (Production)

#### Prerequisites
- AWS CLI installed and configured
- Docker installed

#### Steps
1. Clone and setup:
```bash
git clone <your-repo-url>
cd auto-form-filling-agent
```

2. Setup AWS infrastructure:
```bash
# Export your API keys
export OPENROUTER_API_KEY="your_openrouter_key_here"
export LLAMA_CLOUD_API_KEY="your_llama_cloud_key_here"

# Create infrastructure (ECR, ECS, Secrets)
./aws/setup-infrastructure.sh
```

3. Deploy to AWS:
```bash
./aws/deploy.sh
```

✅ **Production deployment complete!**

See `aws/README.md` for detailed deployment guide.

## 🎯 How to Use

### 1. Prepare Your Resume
- Save your resume as PDF, DOCX, or TXT
- Include: Name, Email, Phone, Skills, Education, Work Experience

### 2. Get Google Form URL
- Open any Google Form
- Copy the URL (should contain `docs.google.com/forms`)

### 3. Fill the Form
1. Open `http://localhost:3000`
2. Upload your resume file
3. Paste the Google Form URL
4. Click "Submit Form Directly"
5. ✅ Form submitted automatically!

## 📁 Project Structure

```
auto-form-filling-agent/
├── backend/
│   ├── services/
│   │   ├── resume_parser.py         # AI resume parsing
│   │   └── google_forms_service.py  # Form submission
│   ├── main.py                      # FastAPI server
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Development container
│   ├── Dockerfile.prod              # Production container
│   └── .env                         # API keys (create this)
├── frontend/
│   ├── src/
│   │   ├── components/              # React components
│   │   └── services/                # API calls
│   ├── package.json                 # Node dependencies
│   ├── Dockerfile                   # Frontend container
│   └── public/
├── aws/
│   ├── setup-infrastructure.sh      # AWS infrastructure setup
│   ├── deploy.sh                    # AWS deployment script
│   ├── iam-policies.json            # Security policies
│   └── README.md                    # AWS deployment guide
├── docker-compose.yml               # Local development
├── .env.example                     # Environment template
└── README.md
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/parse-resume` | POST | Extract data from resume |
| `/api/analyze-form` | POST | Analyze Google Form structure |
| `/api/fill-form` | POST | Fill and submit form |
| `/api/health` | GET | Health check |
| `/api/hello` | GET | Test endpoint |

## 🐛 Troubleshooting

### Backend Issues

**Error: "Module not found"**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r backend/requirements.txt
```

**Error: "API key not found"**
- Check `.env` file exists in `backend/` folder
- Verify API keys are correct (no extra spaces)
- Restart backend server after adding keys

### Frontend Issues

**Error: "npm command not found"**
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Restart terminal after installation

**Error: "Connection refused"**
- Make sure backend is running on port 8000
- Check `http://localhost:8000/api/health`

### Form Submission Issues

**Error: "Invalid form URL"**
- Use Google Forms URLs only
- URL should contain `docs.google.com/forms`
- Try with a simple test form first

## 🎓 For Students & Beginners

### Learning Resources
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
- **React**: [reactjs.org](https://reactjs.org/)
- **Python Virtual Environments**: [docs.python.org](https://docs.python.org/3/tutorial/venv.html)

### Common Commands

#### Docker Commands
```bash
# Start application
docker-compose up

# Start in background
docker-compose up -d

# Rebuild containers
docker-compose up --build

# Stop application
docker-compose down

# View logs
docker-compose logs
```

#### Manual Setup Commands
```bash
# Check Python version
python --version

# Check Node version
node --version

# Install Python package
pip install package_name

# Install Node package
npm install package_name
```

### Project Customization
- **Add new resume fields**: Edit `resume_parser.py`
- **Change AI models**: Modify `config.py`
- **Update UI**: Edit React components in `frontend/src/components/`
- **Add new endpoints**: Add routes in `main.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature-name`
6. Create Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Need Help?

- **Issues**: Create an issue on GitHub
- **Questions**: Check existing issues first
- **Documentation**: Read this README carefully

---

**Happy Coding! 🚀**

*Made with ❤️ for students and developers*

## One‑click start scripts (Windows PowerShell)

To make running the app trivial on Windows, this repo includes PowerShell helper scripts that create virtual environments, install deps and launch both the backend and frontend in separate terminal windows.

- `start-backend.ps1` — creates `backend\venv` (if missing), installs Python packages from `backend/requirements.txt` and runs the FastAPI server on port 8000.
- `start-frontend.ps1` — runs `npm ci` in `frontend/` and starts the React dev server on port 3000.
- `start-all.ps1` — launches both helpers in separate PowerShell windows (one command to start everything).
- `start-docker.ps1` — runs `docker-compose up --build` from the repo root (requires Docker).

Usage (PowerShell):
```powershell
cd "C:\Users\venki\OneDrive\Desktop\ROUTER\automatic-job-application-filler"
# Start both frontend & backend in separate windows
.\start-all.ps1

# Or run individually (open two PowerShell windows):
.\start-backend.ps1
.\start-frontend.ps1
```

Notes:
- Before running the backend, copy `backend/.env.example` to `backend/.env` and add your API keys (OpenRouter / Llama Cloud).
- The frontend will use `frontend/.env` which contains `REACT_APP_API_URL=http://localhost:8000`. If you prefer, the project also sets a `proxy` in `frontend/package.json` so create-react-app will forward `/api` calls to the backend during development.

If you want a single-click shortcut (Windows) I can add a `.lnk` or a `.bat` that runs `start-all.ps1`.