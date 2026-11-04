ZLENDO STUDIO - LOCAL DEVELOPMENT SETUP
=======================================

Zlendo Studio is a customized version of Label Studio with support for custom ML models (e.g., YOLO via Ultralytics).
This guide explains how to run the frontend, backend, and ML backend locally.

-------------------------
FOLDER STRUCTURE OVERVIEW
-------------------------

label-Studio/
├── LS/                         → Python virtual environment (activate this)
├── label-studio/              → Django backend
├── label-studio-ml-backend/   → Custom ML backend (Ultralytics, etc.)
├── web/                       → React frontend
└── requirements.txt           → Python dependencies

-------------------------
BACKEND SETUP (DJANGO)
-------------------------

1. Activate virtual environment:
   ---------------------------------
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   LS\Scripts\activate

2. Install Python dependencies:
   ---------------------------------
   (Ensure your requirements.txt contains:)
   ultralytics
   label-studio
   -e ./label-studio

   Then run:
   pip install -r requirements.txt

3. Apply database migrations:
   ---------------------------------
   python label-studio/manage.py migrate

4. Collect static files (optional):
   ---------------------------------
   python label-studio/manage.py collectstatic --noinput

5. Change backend ports (optional):
   ---------------------------------
   Edit label-studio/core/settings/base.py to change HOSTNAME and PORT.

6. Run backend server:
   ---------------------------------
   python label-studio/manage.py runserver

-------------------------
FRONTEND SETUP (React UI)
-------------------------

1. Navigate to the 'web' folder:
   ---------------------------------
   cd web

2. Install frontend dependencies:
   ---------------------------------
   npm install --legacy-peer-deps
   npm install --save-dev cross-env --legacy-peer-deps

3. Run frontend dev server:
   ---------------------------------
   npm run dev

-------------------------
ML BACKEND SETUP (YOLO)
-------------------------

1. Model Directory:
   label-studio-ml-backend/label-studio-ml-backend/my_ml_backend/

2. Example implementation (model.py):
   ---------------------------------
   from label_studio_ml.model import LabelStudioMLBase
   from ultralytics import YOLO

   class ZlendoModel(LabelStudioMLBase):
       def setup(self):
           self.model = YOLO("path/to/model.pt")

       def predict(self, tasks, **kwargs):
           return []

3. Install ML Backend SDK (first-time / editable setup):
   ---------------------------------
   LS\Scripts\activate
   cd label-studio-ml-backend\label-studio-ml-backend
   pip install -e .

   (Note: For Python 3.10, ensure requirements.txt uses label-studio-sdk==1.0.2)

4. Run ML Backend Server:
   ---------------------------------
   cd label-studio-ml-backend\label-studio-ml-backend

   # Option A: Using CLI (Recommended)
   label-studio-ml start my_ml_backend -p 9090

   # Option B: Run with custom host/debug
   label-studio-ml start my_ml_backend -p 9090 --host 0.0.0.0 -d

   # Option C: Direct Python execution
   python my_ml_backend\_wsgi.py -p 9090

   # Option D: Run with Docker
   cd my_ml_backend
   docker-compose up

5. Connect ML Backend in Label Studio:
   ---------------------------------
   a. Open your project in Label Studio.
   b. Navigate to: Settings > Machine Learning > Add Model.
   c. Set URL: http://localhost:9090 (or http://127.0.0.1:9090).
   d. Enable "Retrieve predictions when loading a task automatically" if desired.
   e. Click "Validate and Save".

---------------------------------------------
SERVER / REMOTE DEPLOYMENT (IP: 45.64.105.163)
---------------------------------------------

When running or deploying on the server (IP: 45.64.105.163), only two configuration files are modified:

1. Frontend Configuration: label-studio/web/webpack.config.js
   ----------------------------------------------------------
   ```javascript
   const FRONTEND_HMR = process.env.FRONTEND_HMR === "true";
   const FRONTEND_HOSTNAME = FRONTEND_HMR ? process.env.FRONTEND_HOSTNAME || "http://45.64.105.163:4467" : "";
   const DJANGO_HOSTNAME = process.env.DJANGO_HOSTNAME || "http://45.64.105.163:4464";
   const HMR_PORT = FRONTEND_HMR ? +new URL(FRONTEND_HOSTNAME).port : 4467;
   ```

2. Backend Configuration: label-studio/label_studio/core/settings/base.py
   -----------------------------------------------------------------------
   - Hostname & Port:
     ```python
     FRONTEND_HOSTNAME = get_env('FRONTEND_HOSTNAME', 'http://45.64.105.163:4467' if FRONTEND_HMR else HOSTNAME)
     INTERNAL_PORT = get_env('PORT', '4464')
     ```

   - CSRF Trusted Origins:
     ```python
     CSRF_TRUSTED_ORIGINS = [
         "http://localhost:8020",
         "http://45.64.105.163:4467",
         "http://45.64.105.163:4464",
         "http://45.64.105.163:4466",
     ]
     ```

----------------------
DEFAULTS PORTS
-----------------------

| Component   | Port  |
|-------------|-------|
| Backend     | 8080  |
| Frontend    | 8010  |
| ML Backend  | 9090  |
-------------------------
PORTS CONFIGURATION
-------------------------

| Component          | Local Port | Server Port | Server URL                  |
|--------------------|------------|-------------|-----------------------------|
| Backend (Django)   | 8000 / 8080| 4464        | http://45.64.105.163:4464   |
| Frontend (React)   | 8010 / 8020| 4467        | http://45.64.105.163:4467   |
| ML Backend (YOLO)  | 9090       | 4466        | http://45.64.105.163:4466   |

-------------------------
TROUBLESHOOTING
-------------------------

- Login keeps redirecting: Add no-cache headers in middleware.
- Frontend UI not loading: Make sure npm dev server is running.
- ML backend not predicting: Check model path and load status.
- ML backend port conflict: Start with a different port (e.g. -p 9091 or -p 4466).
- label-studio-ml not recognized: Ensure venv is activated and run 'pip install -e .' inside label-studio-ml-backend/label-studio-ml-backend.

-------------------------
STARTUP SUMMARY
-------------------------

=== LOCAL DEVELOPMENT ===

# 1. Activate & start backend (Terminal 1)
LS\Scripts\activate
python label-studio/manage.py runserver

# 2. Activate & start ML backend (Terminal 2)
LS\Scripts\activate
cd label-studio-ml-backend\label-studio-ml-backend
label-studio-ml start my_ml_backend -p 9090

# 3. Start frontend (Terminal 3)
cd web
npm run dev

=== SERVER DEPLOYMENT (45.64.105.163) ===

# 1. Activate & start backend (Terminal 1)
LS\Scripts\activate
python label-studio/manage.py runserver 0.0.0.0:4464

# 2. Activate & start ML backend (Terminal 2)
LS\Scripts\activate
cd label-studio-ml-backend\label-studio-ml-backend
label-studio-ml start my_ml_backend -p 4466

# 3. Start frontend (Terminal 3)
cd web
npm run dev

-------------------------
CREDITS
-------------------------

- Based on: Label Studio by HumanSignal
- Customized as: Zlendo Studio (Internal Use)
