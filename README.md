# JobYaari AI Assistant

Lightweight Streamlit app that scrapes JobYaari.com (demo/scraper) and exposes a chat interface backed by an offline Llama3 model (via Ollama).

This repository contains a single Streamlit app `jobyaari_bot.py` which:
- Scrapes job listings by category from JobYaari (or generates sample data if scraping fails).
- Builds a small searchable knowledge base from the scraped jobs.
- Uses an offline Llama3 model (Ollama) to answer user queries and optionally attach scraped job results.

## Quick status
- App file: `jobyaari_bot.py`
- UI: Streamlit
- Language model: Llama3 (via Ollama)

## Prerequisites
- Python 3.9+ (3.10 or 3.11 recommended)
- Ollama installed (for offline Llama3 usage)
- Internet connection for scraping (optional — the app will use sample data if scraping fails)

## Install dependencies
Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Ollama (Llama3) setup
The app uses an Ollama-hosted Llama3 model. Follow these steps to run Ollama locally:

```bash
# Install Ollama (macOS/Linux example from official site)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the Llama3 model (8B recommended in the app)
ollama pull llama3:8b

# Start Ollama server
ollama serve
```

Notes:
- On Windows, follow the official Ollama installation instructions for Windows.
- Make sure `ollama serve` is running before starting the Streamlit app so the `Ollama` client can connect.

## Run the Streamlit app

```powershell
streamlit run jobyaari_bot.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

## What to expect
- Click "Scrape Latest Jobs" in the sidebar to fetch job data from JobYaari.com.
- If scraping fails (site changes or blocked), the app will populate sample jobs so you can test the chat and exploration features.
- The chat uses the Llama3 model to answer queries and will append matching job results when relevant.

## Notes & troubleshooting
- If you see errors when loading the Llama model, make sure Ollama is installed, the model is pulled, and `ollama serve` is running.
- If scraping returns few jobs, the app injects sample jobs for demonstration.
- The app is intended for educational/demo purposes. Respect robots.txt and site scraping policies when scraping real sites.

## Uploading to GitHub
Example Git commands to initialize and push this repository (replace `<remote-url>`):

```powershell
git init
git add .
git commit -m "Initial commit: JobYaari AI Assistant"
git branch -M main
git remote add origin <remote-url>
git push -u origin main
```

## License
Add a license of your choice. This project does not include a license by default.

---
If you'd like, I can also initialize a Git repository here, create a remote, and push (you'll need to provide the remote URL or authorize push access).