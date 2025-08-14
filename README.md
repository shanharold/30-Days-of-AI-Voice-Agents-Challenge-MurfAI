# 30 Days of AI Voice Agents 🚀

Welcome to the **30 Days of AI Voice Agents Challenge** with Murf Ai! This project is a hands-on journey to designing, building, and deploying production-ready AI Voice Agents using Python, FastAPI, and modern speech technologies. Whether you’re joining for the challenge or exploring voice tech, this repo offers a modular foundation for rapid prototyping and extension.

---

## 🌟 Project Overview

- **Goal:** Build an extensible platform for AI-powered voice agents over 30 days.
- **What you’ll find:** Speech-to-text (STT), text-to-speech (TTS), dialogue management, and ready-to-use API endpoints.
- **Challenge spirit:** Daily logs, incremental features, and practical, production-minded code.

---

## 🏗️ Architecture

```
+-----------+        +-----------+        +-----------+
|  Client   | <----> |  FastAPI  | <----> |  Voice    |
| (Web/UI)  |        |  Backend  |        |  APIs     |
+-----------+        +-----------+        +-----------+
                            |
                            v
                   +----------------+
                   |  AI/LLM Models |
                   +----------------+
```

- **FastAPI Backend**: Central hub for all voice agent logic and API endpoints.
- **Voice APIs**: Integration with services for speech recognition and synthesis.
- **Extensible Modules**: Easily add new agents or features.

---

## ✨ Features

- 🎤 **Speech-to-Text**: Real-time and batch conversion using top APIs.
- 🔊 **Text-to-Speech**: Multi-voice, multi-language synthesis.
- 🧠 **Dialogue Agents**: LLM-powered conversation flows.
- 📊 **Daily Logs**: Track your progress, experiments, and results.
- 🚀 **API-First**: Swagger docs (visit `/docs`) for easy testing.

---

## 🛠️ Technologies

- [Python 3.8+](https://python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [OpenAI, Murf.ai, etc.](https://openai.com/)
- (Optional) [Docker](https://www.docker.com/)

---

## 🏃‍♂️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/shanharold/30-Days-of-AI-Voice-Agents-Challenge-MurfAI.git
cd 30-Days-of-AI-Voice-Agents-Challenge-MurfAI
```

### 2. Set Up Your Environment

```bash
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_key
VOICE_API_KEY=your_voice_service_key
# Add any other keys or configuration here
```

### 4. Run the API Server

```bash
uvicorn main:app --reload
```
- Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

---

## 📂 Directory Structure

```
.
├── agents/             # Voice agent modules
├── api/                # FastAPI endpoints
├── logs/               # Daily logs and progress
├── static/             # (Optional) Static files
├── main.py             # FastAPI entrypoint
├── requirements.txt
└── README.md
```

---

## 🖼️ Screenshots

[Sample Agent Output](static/sgent_ui.png)
[API Docs Screenshot](static/api_docs.png)

---

## 💡 Contributing

Pull requests, ideas, and feedback are welcome! Please fork the repo, create a branch, and open a PR.

---

## 📝 License

MIT License © 2025 [shanharold](https://github.com/shanharold)

---

## 🙋‍♂️ Questions? Ideas?

Open an issue or connect on [LinkedIn](https://www.linkedin.com/in/shan-harold).

---

Happy hacking and good luck with your voice agent journey! 🚀