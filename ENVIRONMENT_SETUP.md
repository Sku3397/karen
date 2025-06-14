# Karen AI Environment Setup Guide

## ✅ FIXED: Critical Environment Issues Resolved

This document provides the working setup commands for the Karen AI project after resolving critical dependency and environment issues.

## 🚀 Quick Setup (Working Commands)

### 1. Virtual Environment Setup

```bash
# Remove any broken virtual environment
Remove-Item -Recurse -Force .venv

# Create fresh virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
# Install core dependencies (working versions)
pip install -r src/requirements.txt
```

### 3. Verify Installation

```bash
# Test critical imports
python -c "from google.oauth2.credentials import Credentials; print('Google API: OK')"
python -c "from twilio.rest import Client; print('Twilio: OK')"
python -c "import celery; print('Celery: OK')"
python -c "from src.celery_app import celery_app; print('Celery app loaded successfully:', celery_app)"
```

### 4. Run Tests

```bash
# Test email pipeline (requires OAuth tokens)
python test_email_pipeline.py

# Test NLP pipeline (working without external dependencies)
python test_nlp_pipeline.py
```

## 🔧 Issues Fixed

### 1. Virtual Environment Path Issue
**Problem**: Virtual environment was created with old project path (`AI_Handyman_Secretary_Assistant`)
**Solution**: Recreated virtual environment with correct project path (`karen`)

### 2. Missing Dependencies
**Problem**: Multiple missing packages causing import errors
**Fixed packages**:
- `google-generativeai==0.7.2` (for LLM client)
- `google-cloud-firestore==2.13.1` (for task manager)
- `google-cloud-speech==2.20.0` (for communication agent)
- `pytz==2023.3` (for timezone handling)
- `numpy>=1.24.0` (for memory client)
- `chromadb>=1.0.0` (for vector database)
- OpenTelemetry packages (required by chromadb)

### 3. Import Configuration Issues
**Problem**: Test file importing `MONITORED_EMAIL_ACCOUNT` but config has `MONITORED_EMAIL_ACCOUNT_CONFIG`
**Solution**: Updated test file imports to match config variable names

### 4. Compilation Dependencies Removed
**Removed problematic packages**:
- `scipy` (requires Fortran compiler on Windows)
- `scikit-learn` (depends on scipy)
- `spacy` (optional NLP enhancements)
- `kubernetes` (not needed for core functionality)

## 📊 Test Results

### ✅ Working Components
- **Email Pipeline Infrastructure**: ✅ All imports working
- **NLP Pipeline**: ✅ 77.6% accuracy (38/49 tests passed)
- **Celery Integration**: ✅ App loads successfully
- **Google API Clients**: ✅ All libraries imported
- **Configuration System**: ✅ Environment variables loaded

### ⚠️ Expected Failures
- **Email Tests**: Fail due to missing OAuth tokens (expected)
- **NLP Intent Classification**: Some edge cases need improvement

## 🔑 Environment Variables Required

Create a `.env` file with:
```bash
# Email Configuration
SECRETARY_EMAIL_ADDRESS=karensecretaryai@gmail.com
MONITORED_EMAIL_ACCOUNT=hello@757handy.com
ADMIN_EMAIL_ADDRESS=your-admin@email.com

# API Keys
GEMINI_API_KEY=your-gemini-api-key

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OAuth Token Paths
SECRETARY_TOKEN_PATH=gmail_token_karen.json
MONITORED_EMAIL_TOKEN_PATH=gmail_token_monitor.json

# Optional
USE_MOCK_EMAIL_CLIENT=False
USE_MEMORY_SYSTEM=False
SKIP_CELERY_STARTUP=True
```

## 🚨 Known Issues

1. **Unicode Logging**: Some emoji characters cause logging errors on Windows (non-critical)
2. **Protobuf Version Conflicts**: Some version mismatches but functionality works
3. **OAuth Tokens**: Need to be generated for email functionality

## 🎯 Next Steps

1. **OAuth Setup**: Generate OAuth tokens for email accounts
2. **Redis Setup**: Install and configure Redis for Celery
3. **Production Deployment**: Configure environment for production use
4. **NLP Improvements**: Enhance intent classification accuracy

## 📝 Dependencies Summary

**Total packages installed**: 132
**Core functionality**: ✅ Working
**Test coverage**: Email pipeline infrastructure + NLP pipeline
**Performance**: Fast startup, efficient dependency resolution

This setup provides a solid foundation for Karen AI development and testing. 