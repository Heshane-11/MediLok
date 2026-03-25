<div align="center">

# 🏥 MediLok

### AI-Powered Telemedicine Platform

**Bridging patients and doctors through intelligent, real-time virtual care**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat-square&logo=django)
![Groq](https://img.shields.io/badge/AI-LLaMA%203.1%20via%20Groq-orange?style=flat-square)
![ZEGOCLOUD](https://img.shields.io/badge/Video-ZEGOCLOUD-blueviolet?style=flat-square)
![Twilio](https://img.shields.io/badge/SMS-Twilio-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 📌 Overview

**MediLok** is a full-stack telemedicine platform that enables patients to consult with doctors remotely through real-time video calls, AI-assisted pre-diagnosis, and a structured consultation request workflow.

At its core, MediLok integrates **Generative AI (LLaMA 3.1 via the Groq API)** to provide patients with intelligent, instant symptom analysis before connecting them with a verified doctor. The platform handles the entire consultation lifecycle — from request to video call — with SMS notifications powered by **Twilio** and real-time video powered by **ZEGOCLOUD**.

> Built to reduce barriers to healthcare access by making quality medical consultation available from any device, anywhere.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI Doctor Chat** | LLaMA 3.1 (via Groq API) provides instant, context-aware responses to patient symptoms before a doctor is available |
| 📹 **Video Consultation** | Real-time HD video and voice calls between patient and doctor powered by ZEGOCLOUD |
| 📋 **Consultation Requests** | Structured patient→doctor request workflow with accept/reject controls |
| ⏱️ **10-Minute Join Window** | Auto-expiring session logic — consultations expire if either party doesn't join within 10 minutes of acceptance |
| 📲 **SMS Notifications** | Automated Twilio SMS alerts sent to patients on request acceptance, rejection, and session start |
| 👤 **Patient Profiles & Reports** | Persistent patient health profiles with uploadable reports and consultation history |
| 📚 **Health Education** | Curated disease information and health education content for patients |
| 🔐 **Google OAuth** | Secure, one-click authentication via Google OAuth 2.0 |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11** + **Django 4.x** — core framework and REST routing
- **SQLite** — development database (easily swappable to PostgreSQL for production)

### Frontend
- **HTML5**, **CSS3**, **Bootstrap 5**, **JavaScript (ES6)**
- Django templating engine for server-side rendering

### Integrations & APIs
- **Groq API** — LLaMA 3.1 8B model for generative AI responses
- **ZEGOCLOUD** — real-time video/audio consultation infrastructure
- **Twilio** — programmable SMS for patient notifications
- **Google OAuth 2.0** — authentication via `django-allauth`

---

## 🏗️ System Architecture & Workflow

```
Patient                        Platform                        Doctor
  │                               │                               │
  ├─── Logs in (Google OAuth) ───▶│                               │
  │                               │                               │
  ├─── Chats with AI Doctor ─────▶│◀── LLaMA 3.1 (Groq API) ────┤
  │    (symptom pre-analysis)      │                               │
  │                               │                               │
  ├─── Sends consultation ────────▶│──── Notifies doctor ─────────▶│
  │    request to doctor           │                               │
  │                               │          Doctor reviews        │
  │                               │◀─── Accept / Reject ──────────┤
  │                               │                               │
  │◀── SMS notification (Twilio) ─┤                               │
  │                               │                               │
  ├─── Joins video call ──────────▶│◀────── Joins video call ──────┤
  │    (within 10-min window)      │         (ZEGOCLOUD)           │
  │                               │                               │
  └─── Consultation complete ─────▶│──── Session recorded ─────────▶
```

**Step-by-step:**
1. Patient registers/logs in via Google OAuth
2. Patient optionally uses **AI Doctor Chat** for initial symptom analysis
3. Patient browses the doctor list and submits a **consultation request**
4. Doctor receives the request and **accepts or rejects** it
5. Patient receives an **SMS notification** via Twilio with the outcome
6. On acceptance, both parties have a **10-minute window** to join the video call
7. Real-time **video/voice consultation** takes place via ZEGOCLOUD
8. Consultation history and reports are saved to the patient's profile

---

## 📁 Project Structure

```
medilok/
│
├── medilok/                  # Django project config (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── doctor/                   # Doctor module — profiles, availability, requests
│   ├── models.py             # Doctor, ConsultationRequest models
│   ├── views.py              # Request handling, accept/reject, video session
│   ├── urls.py
│   └── templates/doctor/
│
├── disease/                  # Health education — disease info and articles
│   ├── models.py
│   ├── views.py
│   └── templates/disease/
│
├── patient/                  # Patient module — profiles, reports, history
│   ├── models.py
│   ├── views.py
│   └── templates/patient/
│
├── ai_chat/                  # AI Doctor Chat — Groq API integration
│   ├── views.py              # Handles LLaMA 3.1 prompt/response cycle
│   └── templates/ai_chat/
│
├── templates/                # Shared base templates
│   └── base.html
│
├── static/                   # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
│
├── requirements.txt
├── .env.example
└── manage.py
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/heshane-garg/medilok.git
cd medilok
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file
```bash
cp .env.example .env
# Fill in all required keys (see Environment Variables section below)
```

### 5. Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (optional, for admin access)
```bash
python manage.py createsuperuser
```

### 7. Start the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## 🔑 Environment Variables

Create a `.env` file in the root directory with the following keys:

```env
# Django
SECRET_KEY=your_django_secret_key
DEBUG=True

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Twilio (SMS Notifications)
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

# Groq (Generative AI — LLaMA 3.1)
GROQ_API_KEY=your_groq_api_key

# ZEGOCLOUD (Video Calls)
ZEGO_APP_ID=your_zego_app_id
ZEGO_SERVER_SECRET=your_zego_server_secret
```

> ⚠️ Never commit your `.env` file. It is listed in `.gitignore` by default.

---

## 🛣️ Key Routes & Endpoints

| Route | Description |
|---|---|
| `/` | Landing page |
| `/doctor_list/` | Browse all available doctors |
| `/chat_with_ai/` | AI Doctor Chat (LLaMA 3.1 via Groq) |
| `/doctor_requests/` | Doctor dashboard — view incoming consultation requests |
| `/my_requests/` | Patient dashboard — track sent requests and their status |
| `/video_call/<id>/` | ZEGOCLOUD video consultation room for a specific session |
| `/accounts/google/login/` | Google OAuth login |
| `/admin/` | Django admin panel |

---

## 📸 Screenshots

> _Screenshots coming soon.

| AI Doctor Chat | Video Consultation | Doctor Dashboard |
|:---:|:---:|:---:|
| ![AI Chat](https://via.placeholder.com/280x180?text=AI+Doctor+Chat) | ![Video Call](https://via.placeholder.com/280x180?text=Video+Consultation) | ![Dashboard](https://via.placeholder.com/280x180?text=Doctor+Dashboard) |

| Patient Requests | Doctor List | SMS Notification |
|:---:|:---:|:---:|
| ![Requests](https://via.placeholder.com/280x180?text=My+Requests) | ![Doctors](https://via.placeholder.com/280x180?text=Doctor+List) | ![SMS](https://via.placeholder.com/280x180?text=SMS+Alert) |

---

## 🧩 Challenges & Solutions

### 1. Real-Time Video Communication
**Challenge:** Establishing low-latency, reliable video sessions between patients and doctors without building custom WebRTC infrastructure.  
**Solution:** Integrated **ZEGOCLOUD SDK**, which handles signaling, TURN/STUN servers, and session management out of the box. Session tokens are generated server-side using ZEGO's token API, ensuring each call is authenticated and scoped to a unique consultation ID.

### 2. 10-Minute Join Window Logic
**Challenge:** Preventing ghost sessions where one party accepts but never joins, leaving the other waiting indefinitely.  
**Solution:** On request acceptance, a `session_expiry` timestamp is stored (acceptance time + 10 minutes). Both join endpoints validate against this timestamp — expired sessions are auto-cancelled and the patient is notified via SMS.

### 3. Secure Session & OAuth Handling
**Challenge:** Managing secure user sessions across Google OAuth flows without exposing tokens or session data.  
**Solution:** Used `django-allauth` for OAuth, combined with Django's built-in session framework and CSRF protection. All sensitive keys are loaded from environment variables via `python-decouple`.

### 4. Generative AI Response Integration
**Challenge:** Integrating LLaMA 3.1 responses in a way that feels conversational without exposing raw API errors to patients.  
**Solution:** Built a dedicated `ai_chat` module with a prompt wrapper that includes system-level medical context, graceful error handling, and response sanitization before rendering to the frontend.

---

## 🚀 Future Improvements

- 🌐 **Multi-language AI responses** — support regional Indian languages (Hindi, Tamil, Bengali) via translation layer
- 📅 **Appointment scheduling** — calendar-based booking system with doctor availability slots
- 💳 **Payment integration** — Razorpay/Stripe for paid consultations and prescription fees
- 📊 **Analytics dashboard** — consultation metrics, AI usage stats, and doctor performance reports
- 📱 **Mobile app** — React Native client consuming a Django REST API backend
- 🔔 **Push notifications** — browser and mobile push alerts for consultation updates
- 🏥 **EHR integration** — connect with Electronic Health Record systems for richer patient history

---

## 👨‍💻 Author

**Heshane Garg**  
Full-Stack Developer | AI & Web Enthusiast

[![GitHub](https://img.shields.io/badge/GitHub-heshanegarg-181717?style=flat-square&logo=github)](https://github.com/Heshane-11)

---

## 📝 Notes

- **ML models** — Large language model inference is handled entirely via the **Groq API** (cloud-based). No local ML model files are required or included in this repository.
- **Environment file** — The `.env` file is intentionally excluded from version control for security. Use `.env.example` as a reference to configure your own.
- **Database** — SQLite is used for development convenience. For production deployment, migrate to **PostgreSQL** by updating `DATABASES` in `settings.py` and installing `psycopg2`.

---

<div align="center">


</div>
