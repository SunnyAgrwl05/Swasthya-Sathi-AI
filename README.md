# 🩺 Swasthya Sathi AI

<p align="center">

![CI](https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/SunnyAgrwl05/Swasthya-Sathi-AI)
![Stars](https://img.shields.io/github/stars/SunnyAgrwl05/Swasthya-Sathi-AI)
![Forks](https://img.shields.io/github/forks/SunnyAgrwl05/Swasthya-Sathi-AI)
![Issues](https://img.shields.io/github/issues/SunnyAgrwl05/Swasthya-Sathi-AI)

</p>

> **An AI-powered attendance management agent for rural healthcare workers.**
>
> Built with **Gemini Function Calling + FastAPI + React** for the **Google AI Agent Builder Series 2026**.

---

## 🌐 Live Demo

**Frontend**

https://swasthya-sathi-ai-one.vercel.app

**Backend API**

https://your-render-url.onrender.com

---

## 📸 Preview

![Dashboard](assets/dashboard.png)

---

# 🚑 Problem Statement

Rural Primary Health Centres depend on hundreds of ASHA, ANM and Anganwadi workers.

Attendance is usually tracked using:

- Paper registers
- WhatsApp groups
- Excel sheets

As a result,

- supervisors don't know who missed attendance
- attendance summaries take time
- low-performing workers are discovered too late

Swasthya Sathi AI solves this with an intelligent AI Agent.

---

# 🤖 Why This Isn't Just Another Chatbot

Unlike traditional chatbot CRUD apps,

Swasthya Sathi AI gives Gemini access to real backend tools.

Instead of generating fake responses, Gemini decides which function should run.

Example:

```
Mark Sunny Kumar present today
then show this month's attendance.
```

Gemini automatically executes

```
mark_attendance()

↓

get_attendance_summary()
```

without writing custom workflow code.

The supervisor simply talks naturally.

---

# ✨ Features

- AI Agent with automatic function calling
- Hindi + English conversations
- Attendance analytics dashboard
- Attendance summary
- Low attendance detection
- Worker management
- Daily attendance tracking
- REST APIs
- Responsive UI
- Docker support
- GitHub Actions CI

---

# 🏗 Architecture

```text
                User

                  │

                  ▼

      React + Vite Frontend

                  │

             REST API

                  │

                  ▼

          FastAPI Backend

                  │

      Gemini Function Calling

      ┌─────────┼──────────┐

      ▼         ▼          ▼

Attendance  Analytics   Workers

                  │

                  ▼

             SQLite Database
```

---

# ⚡ Tech Stack

| Layer | Technology |
|--------|------------|
| AI | Gemini 2.0 Flash |
| Backend | FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Frontend | React + Vite |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Deployment | Render + Vercel |
| Testing | Pytest |
| CI | GitHub Actions |
| Container | Docker |

---

# 📂 Project Structure

(keep your current tree)

---

# 📖 REST APIs

| Method | Endpoint | Description |
|----------|-------------|----------------|
| GET | /api/workers | List workers |
| GET | /api/attendance | Attendance |
| POST | /api/chat | AI Agent |
| POST | /api/attendance | Mark attendance |

---

# 🚀 Local Setup

(keep current)

---

# 🐳 Docker

(keep current)

---

# ☁ Deployment

(keep current)

---

# 💬 Example Prompts

```
Sunny Kumar ko present mark karo

Kajal Kumari ki attendance dikhao

Is month sabse kam attendance kiski hai?

Kal absent mark karo

Aaj kisne attendance nahi lagayi?
```

---

# 🧪 Testing

Run backend tests

```bash
pytest
```

GitHub Actions automatically executes tests on every push.

---

# 🛣 Roadmap

## Completed

- AI Agent
- Dashboard
- Charts
- Docker
- CI/CD
- REST APIs
- Deployment

## Planned

- Authentication
- Voice Assistant
- WhatsApp Integration
- SMS Alerts
- Export PDF
- Multi-language
- Notifications

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository

2. Create a branch

```
git checkout -b feature-name
```

3. Commit

```
git commit -m "Add feature"
```

4. Push

```
git push origin feature-name
```

5. Open a Pull Request.

---

# ⭐ Support

If you like this project,

please consider giving it a ⭐ on GitHub.

---

# 👨‍💻 Author

**Sunny Kumar**

Co-Organizer & Tech Lead — GDG On Campus BCE Patna

Beta MLSA

Google Student Ambassador

LinkedIn

GitHub

---

# 📜 License

MIT License
