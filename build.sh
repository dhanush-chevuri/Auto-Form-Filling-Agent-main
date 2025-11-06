#!/usr/bin/env bash
# Build script for Render

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install Node.js dependencies
cd frontend

# Remove any .env file that might exist
rm -f .env

npm install

# Build React app without REACT_APP_API_URL (will use default /api path)
unset REACT_APP_API_URL
npm run build
cd ..
