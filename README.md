# 🧠 MindEase — AI-Powered Mental Wellness Tracker

> **PromptWars Hackathon** | Google for Developers — Build with AI

## 🎯 Problem Statement

Students preparing for high-stakes board exams and competitive entrance tests (NEET, JEE, CUET, CAT, GATE, UPSC) face severe stress, burnout, and self-doubt. **MindEase** uses Google Gemini AI to analyze daily journaling and mood logs, uncovering hidden stress triggers and emotional patterns that standard trackers miss.

## ✨ Key Features

- **📝 AI-Powered Journaling** — Write daily journal entries analyzed by Gemini AI for emotional patterns, hidden stress triggers, and burnout risk
- **💬 MindEase Buddy** — Conversational AI companion providing real-time coping strategies, breathing exercises, and motivational support
- **📊 Mood Tracking** — Interactive mood slider with visual trend charts powered by Chart.js
- **🧘 Mindfulness Exercises** — Interactive breathing exercises (4-7-8, Box Breathing), grounding techniques, and quick stress busters
- **📈 Wellness Analytics** — Mood trends, emotion distribution, burnout risk timeline, and stress trigger analysis
- **🔔 Proactive Alerts** — AI detects concerning patterns and suggests interventions
- **🆘 Crisis Support** — Integrated Indian mental health helplines (iCall, Vandrevala Foundation, NIMHANS, AASRA)

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.x (Python 3.12) |
| Database | SQLite (dev) / MySQL (production) |
| AI Engine | Google Gemini 2.0 Flash via OpenRouter (`openai` SDK) |
| Frontend | Django Templates + Vanilla CSS + JavaScript |
| Charts | Chart.js 4.x |
| Design | Glassmorphism + Dark/Light Theme |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenRouter API Key ([Get one free](https://openrouter.ai/keys))

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd anuj-promptwar

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

Visit **http://localhost:8000** to start using MindEase!

## 📱 Screenshots

### Login & Registration
Beautiful glassmorphism auth pages with exam type selection.

### Dashboard
Stats cards, mood chart, quick mood check-in, recent entries, and AI insights.

### AI Journal Analysis
Write journal entries → Gemini AI analyzes for emotional patterns, burnout risk, stress triggers, and provides personalized coping strategies.

### AI Chat Buddy
Real-time conversational AI with quick action buttons for breathing exercises, motivation, study tips, and more.

### Mindfulness Exercises
Interactive breathing circle, 5-4-3-2-1 grounding technique, and curated stress busters.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              DJANGO TEMPLATES                    │
│    Glassmorphism CSS + Chart.js + Vanilla JS     │
└────────────────────┬────────────────────────────┘
                     │ HTTP / AJAX
┌────────────────────▼────────────────────────────┐
│               DJANGO BACKEND                     │
│  accounts │ journal │ chat │ wellness │ analytics│
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌──────────┐
   │ SQLite/ │ │ Gemini   │ │  Static  │
   │  MySQL  │ │  2.0 API │ │  Files   │
   └─────────┘ └──────────┘ └──────────┘
```

## 🔒 Safety & Ethics

- **Crisis Detection**: AI system prompt mandates helpline referral for severe distress
- **Not a Therapist**: Clear disclaimer that MindEase is a wellness companion, not medical advice
- **Data Privacy**: Journal entries stored locally, API keys in `.env`
- **CSRF Protection**: Django's built-in CSRF middleware
- **Input Validation**: Django Forms + ORM parameterized queries

## 👥 Team

- **Anuj** — Full-Stack Developer

## 📄 License

Built for PromptWars Hackathon by Google for Developers.