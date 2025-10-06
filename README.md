# Eugene the AI Sea Cow 🦭

A simple, elegant chat interface powered by OpenAI's GPT-5-mini with live web search capability.

## Overview

Eugene is a conversational AI assistant that can:
- Answer questions using GPT-5-mini (OpenAI's latest mini model)
- Search the web for current information (using OpenAI's web_search tool)
- Filter results to only cite .gov sources (optional)
- Remember conversation context for natural, multi-turn discussions

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  templates/index.html (Chat UI)                        │ │
│  │  ├─ static/css/pico.min.css (CSS framework)            │ │
│  │  ├─ static/css/custom.css (Custom styles)              │ │
│  │  └─ static/js/app.js (Interactive behavior)            │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↕                                 │
│                    HTTP Requests/Responses                   │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                      FLASK SERVER (app.py)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  GET  /          → Serve chat UI                       │ │
│  │  POST /api/chat  → Process messages & return response  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↕                                 │
│                  OpenAI API Client (openai_client)           │
└─────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────┐
│                       OPENAI API                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • Chat Completions API (standard chat)                │ │
│  │  • Responses API (web search enabled)                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
ai-experiment/
├── app.py                      # Main Flask server (backend)
├── ai-experiment.py            # Standalone test script (optional)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API key)
│
├── templates/
│   └── index.html              # Chat UI HTML structure
│
├── static/
│   ├── css/
│   │   ├── pico.min.css        # Pico CSS framework
│   │   └── custom.css          # Custom styles and overrides
│   └── js/
│       └── app.js              # Frontend JavaScript (chat logic)
│
├── backups/                    # Project backups (.tar.gz files)
├── Procfile                    # Deployment config for Render
└── render.yaml                 # Deployment config for Render
```

## Quick Start

### 1. Install Dependencies

```bash
# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Run the Server

```bash
# Start the development server
PORT=8080 FLASK_DEBUG=1 python app.py
```

The server will start at: **http://127.0.0.1:8080/**

### 4. Use the Chat Interface

1. Open http://127.0.0.1:8080/ in your browser
2. Type a question in the input field
3. (Optional) Check ".gov only" to filter web results to government sources
4. Click "Submit" or press Enter
5. Eugene will respond with an answer (and search the web if needed)

## How It Works

### Frontend (Browser)

1. **HTML** (`templates/index.html`): Defines the structure of the chat interface
2. **CSS** (`static/css/`): Styles the interface using Pico CSS + custom overrides
3. **JavaScript** (`static/js/app.js`): Handles user interactions:
   - Captures user input
   - Sends messages to the server
   - Displays AI responses
   - Converts markdown to HTML for formatting

### Backend (Server)

1. **Flask** (`app.py`): Web server that:
   - Serves the HTML page
   - Provides the `/api/chat` endpoint
   - Manages conversation history
   - Calls OpenAI API

2. **OpenAI Integration**:
   - **Standard mode**: Uses Chat Completions API (fast, no web access)
   - **Web search mode**: Uses Responses API with `web_search` tool (can access current information)

### Conversation Flow

```
User types message
    ↓
JavaScript sends POST to /api/chat?web=1
    ↓
Flask receives message history
    ↓
Flask calls OpenAI API (with web_search if enabled)
    ↓
OpenAI returns response (may include web search results)
    ↓
Flask sends response back to browser
    ↓
JavaScript displays response in chat
    ↓
User sees answer and can continue conversation
```

## Environment Variables

Set these in your `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | - | Your OpenAI API key from platform.openai.com |
| `PORT` | No | 5000 | Port number for the server |
| `FLASK_DEBUG` | No | 0 | Set to "1" for auto-reload and debug mode (dev only) |

## Development

### Running in Debug Mode

Debug mode enables:
- Auto-reload when code changes
- Detailed error messages
- Interactive debugger

```bash
FLASK_DEBUG=1 PORT=8080 python app.py
```

### Testing the OpenAI API

Use `ai-experiment.py` to test API calls independently:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the test script
python ai-experiment.py
```

### Making Changes

The server will auto-reload when you modify Python files (if `FLASK_DEBUG=1`).

For CSS/JS changes, just refresh your browser (no server restart needed).

## Deployment

This app is configured for deployment on [Render](https://render.com):

1. Push your code to a Git repository (GitHub, GitLab, etc.)
2. Create a new Web Service on Render
3. Connect your repository
4. Render will automatically detect `render.yaml` and deploy
5. Add your `OPENAI_API_KEY` as an environment variable in Render's dashboard

The app uses:
- `Procfile`: Tells Render how to start the server (using gunicorn)
- `render.yaml`: Defines the deployment configuration

## Troubleshooting

### "OPENAI_API_KEY not set"

Make sure you've created a `.env` file with your API key:

```bash
echo "OPENAI_API_KEY=sk-proj-..." > .env
```

### "Address already in use"

Another process is using the port. Either:
- Kill the process: `lsof -ti :8080 | xargs kill -9`
- Use a different port: `PORT=8081 python app.py`

### Web search not working

1. Make sure you're using a recent version of the OpenAI Python library:
   ```bash
   pip install --upgrade openai
   ```

2. Check that the `.gov only` checkbox is working (it adds instructions to the message)

3. Look at the server logs for error messages

### Chat not displaying properly

1. Check browser console for JavaScript errors (F12 → Console tab)
2. Make sure all static files are loading (F12 → Network tab)
3. Try a hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

## Files Explained

### Core Application Files

- **`app.py`**: Main Flask server. Handles HTTP requests and OpenAI API calls.
- **`templates/index.html`**: HTML structure for the chat interface.
- **`static/js/app.js`**: Frontend JavaScript for interactive behavior.
- **`static/css/custom.css`**: Custom styles and Pico CSS overrides.
- **`static/css/pico.min.css`**: Pico CSS framework (minimal, modern styles).

### Configuration Files

- **`.env`**: Environment variables (API key, port, etc.) - **NOT committed to Git**
- **`requirements.txt`**: Python package dependencies
- **`Procfile`**: Tells Render how to start the server
- **`render.yaml`**: Render deployment configuration

### Optional Files

- **`ai-experiment.py`**: Standalone script for testing OpenAI API calls
- **`backups/`**: Directory containing project backups

## Tech Stack

- **Backend**: Python 3, Flask, OpenAI Python SDK
- **Frontend**: Vanilla JavaScript (no frameworks), HTML5, CSS3
- **CSS Framework**: Pico CSS (minimal, classless CSS framework)
- **AI**: OpenAI GPT-5-mini with web_search tool
- **Deployment**: Render (with gunicorn)

## License

This is a personal project. Use it however you'd like! 🦭

---

**Questions?** Check the extensive comments in the code files - they explain everything in detail!