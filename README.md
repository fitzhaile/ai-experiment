# Eugene the AI Sea Cow 🦭

A simple, elegant chat interface powered by OpenAI GPT and Anthropic Claude models with live web search capability.

## Overview

Eugene is a conversational AI assistant that can:
- Answer questions using multiple AI models (GPT-4o, GPT-4o-mini, Claude 3.5 Haiku)
- Search the web for current information using Brave Search API
- Filter results by data source (specific websites or .gov domains)
- Apply intelligent pronoun substitution for location-specific queries
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
│                     AI SERVICES & APIs                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • OpenAI Chat Completions (GPT models)                │ │
│  │  • Anthropic Messages API (Claude models)              │ │
│  │  • Brave Search API (web search with site filters)     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
ai-experiment/
├── app.py                      # Main Flask server (backend)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
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
├── Procfile                    # Deployment config for Render
├── render.yaml                 # Deployment config for Render
├── CLAUDE_SETUP.md             # Claude API setup instructions
├── RENDER_DEPLOYMENT.md        # Render deployment guide
└── CODE_REVIEW.md              # Code review and cleanup documentation
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
2. Select a data source from the dropdown (bryancountyga.com, seda.org, etc.)
3. Select an AI model (GPT-4o, Claude 3.5 Haiku, etc.)
4. Type a question in the input field
5. Click "Submit" or press Enter
6. Eugene will search the web and respond with an answer

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

2. **AI Integration**:
   - **OpenAI models**: GPT-4o, GPT-4o-mini, GPT-4-turbo
   - **Anthropic models**: Claude 3.5 Haiku, Claude 3 Haiku
   - **Web search**: Brave Search API with site-specific filtering
   - **Pronoun substitution**: Automatically replaces "you/your" with location names for better searches

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
| `ANTHROPIC_API_KEY` | Conditional | - | Your Anthropic API key (required for Claude models) |
| `BRAVE_API_KEY` | **Yes** | - | Your Brave Search API key for web search |
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

### Testing the Application

The app automatically performs web searches for all queries. Test different features:

1. **Test different data sources**: Try each dropdown option
2. **Test different models**: Switch between GPT and Claude models
3. **Test pronoun substitution**: Try "What is your population?" with Bryan County selected
4. **Test markdown rendering**: Responses include bold, links, and formatting

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

1. Make sure you have a valid Brave Search API key set in `.env`:
   ```bash
   echo "BRAVE_API_KEY=your-brave-api-key" >> .env
   ```

2. Check that the data source dropdown is working (it adds site: filters to searches)

3. Look at the server logs for error messages (search for "Brave Search" entries)

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

### Documentation Files

- **`CLAUDE_SETUP.md`**: Instructions for setting up Claude API access
- **`RENDER_DEPLOYMENT.md`**: Comprehensive guide for deploying to Render
- **`DEPLOYMENT_CHECKLIST.md`**: Quick deployment checklist
- **`CODE_REVIEW.md`**: Code review findings and cleanup documentation

## Tech Stack

- **Backend**: Python 3, Flask, OpenAI Python SDK, Anthropic Python SDK
- **Frontend**: Vanilla JavaScript (no frameworks), HTML5, CSS3
- **CSS Framework**: Pico CSS (minimal, modern CSS framework)
- **AI Models**: OpenAI GPT-4o/mini, Anthropic Claude 3.5 Haiku
- **Web Search**: Brave Search API with site filtering
- **Deployment**: Render (with gunicorn)

## License

This is a personal project. Use it however you'd like! 🦭

---

**Questions?** Check the extensive comments in the code files - they explain everything in detail!