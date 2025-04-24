# Slack-AI-Prompt-Generator

A Flask-based Slack bot that generates prompts using GPT-4 from OpenAI based on messages sent in Slack channels or DMs. It can regenerate prompts on demand, score them for quality, and log everything to Google Sheets.

---

## 🚀 Features

- ✅ Listens to messages in channels and DMs
- 🧠 Generates prompts using GPT-4
- 🔁 Includes a “Regenerate” button to get new variations
- 📊 Scores prompts based on usefulness and clarity
- 📝 Stores prompts, scores, and user info in a Google Sheet

---

## 📦 Requirements

- Python 3.8+
- Slack app with necessary bot scopes
- Google service account for Sheets API
- OpenAI API key

---

## 🔧 Setup

### 1. Clone and install

```bash
git clone https://github.com/lellisds/Slack-AI-Prompt-Generator.git
cd Slack-AI-Prompt-Generator
pip install -r requirements.txt
