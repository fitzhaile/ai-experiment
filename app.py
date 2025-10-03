"""
Flask app: serves a tiny UI at `/` and an API at `/api/haiku`.

How it works (high level):
- Loads environment variables from `.env` (via python-dotenv) so you don't
  have to export them manually in your shell.

- Initializes a Flask app and enables CORS so the static page can call the API.

- GET `/` returns a minimal HTML page with a text box and button.

- GET `/api/haiku` calls OpenAI with your prompt and returns JSON `{text: ...}`.

Key environment variables:
- OPENAI_API_KEY (required): your real API key.

- OPENAI_MODEL (optional): defaults to `gpt-5-mini` with fallback to `gpt-4o-mini`.

- OPENAI_PROJECT (optional): project ID if you use project-scoped keys.

- PORT (optional): which port Flask should bind to when running `python app.py`.

- FLASK_DEBUG (optional): `1` enables auto-reload and debug logging.
"""

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request
from openai import OpenAI
from flask_cors import CORS
import logging
import os

from pathlib import Path
# Load `.env` from the app directory so starting the app from any cwd still works
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)
logging.basicConfig(level=logging.INFO)
if os.getenv("OPENAI_API_KEY"):
    logging.info("OPENAI_API_KEY detected: %s***", (os.getenv("OPENAI_API_KEY") or "")[:7])
else:
    logging.warning("OPENAI_API_KEY not set")

app = Flask(__name__)
CORS(app)


@app.get("/")
def index():
    # Return a minimal HTML page with a simple chat UI.
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>AI Chat</title>
      <style>
        :root { color-scheme: light dark; }
        body { font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; }
        .container { max-width: 900px; width: 100%; margin: 2rem auto; padding: 0 1rem; box-sizing: border-box; }
        .row { display: flex; gap: 8px; margin-top: 10px; }
        input { flex: 1; height: 40px; padding: 0 10px; font-size: 16px; box-sizing: border-box; }
        button { padding: 0.6rem 1rem; font-size: 1rem; }
        .log { margin-top: 16px; display: flex; flex-direction: column; gap: 14px; }
        .msg { max-width: 80%; padding: 10px 12px; border-radius: 12px; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; }
        .user { align-self: flex-end; background: #0b5cff; color: white; }
        .assistant { align-self: flex-start; background: #f6f8fa; }
        @media (max-width: 1024px) { .container { margin: 1rem auto; } }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Chat</h1>
        <div id="log" class="log"></div>
        <div class="row">
          <input id="prompt" type="text" placeholder="Type a message and press Enter or Send" />
          <button id="btn">Send</button>
        </div>
      </div>
      <script>
        const btn = document.getElementById('btn');
        const promptEl = document.getElementById('prompt');
        const logEl = document.getElementById('log');
        const messages = [
          { role: 'system', content: 'You are a concise assistant that writes clear answers.' }
        ];

        function render() {
          logEl.innerHTML = '';
          for (const m of messages) {
            if (m.role === 'system') continue;
            const div = document.createElement('div');
            div.className = 'msg ' + (m.role === 'user' ? 'user' : 'assistant');
            div.textContent = m.content;
            logEl.appendChild(div);
          }
          logEl.scrollTop = logEl.scrollHeight;
        }

        async function send() {
          const content = promptEl.value.trim() || 'Say hello.';
          messages.push({ role: 'user', content });
          promptEl.value = '';
          render();

          try {
            const res = await fetch('/api/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ messages })
            });
            const data = await res.json();
            if (data && data.text) {
              messages.push({ role: 'assistant', content: data.text });
            } else if (data && data.error) {
              messages.push({ role: 'assistant', content: 'Error: ' + data.error });
            } else {
              messages.push({ role: 'assistant', content: '(no response)' });
            }
          } catch (e) {
            messages.push({ role: 'assistant', content: 'Error: ' + e });
          }
          render();
        }

        btn.addEventListener('click', send);
        promptEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            send();
          }
        });
        render();
      </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.get("/api/haiku")
def api_haiku():
    # Read the user's input from the query string (or use a friendly default)
    user_input = request.args.get("input") or "Ask me anything you can think of, human."
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "OPENAI_API_KEY not set"}), 500
        # Create a client using your API key (and optional project ID)
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), project=os.getenv("OPENAI_PROJECT"))
        # Prefer `gpt-5-mini`; if it fails, fall back to `gpt-4o-mini`
        requested_model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        def generate(model_name: str) -> str:
            chat = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a concise assistant that writes clear answers."},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.7,
            )
            return (chat.choices[0].message.content or "").strip()

        try:
            text = generate(requested_model)
            return jsonify({"text": text})
        except Exception as primary_error:
            logging.warning("Primary model '%s' failed: %s", requested_model, primary_error)
            fallback_model = "gpt-4o-mini"
            if requested_model != fallback_model:
                try:
                    text = generate(fallback_model)
                    return jsonify({"text": text})
                except Exception:
                    pass
            raise primary_error
    except Exception as e:
        # Any error here returns JSON `{error: ...}` and a 500 status
        logging.exception("/api/haiku error")
        return jsonify({"error": str(e)}), 500


@app.post("/api/chat")
def api_chat():
    """
    Multi-turn chat endpoint.
    Expects JSON: { "messages": [{"role":"user|assistant|system","content":"..."}, ...] }
    Returns: { "text": "assistant reply" }
    """
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "OPENAI_API_KEY not set"}), 500

        data = request.get_json(silent=True) or {}
        messages = data.get("messages")
        if not isinstance(messages, list) or not messages:
            return jsonify({"error": "messages[] required"}), 400

        # Create a client using your API key (and optional project ID)
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), project=os.getenv("OPENAI_PROJECT"))

        # Prefer `gpt-5-mini` (no temperature to avoid unsupported setting),
        # then fall back to `gpt-4o-mini` (with temperature for variety)
        requested_model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

        def try_model(model_name: str, with_temperature: bool = False) -> str:
            kwargs = {"model": model_name, "messages": messages}
            if with_temperature:
                kwargs["temperature"] = 0.7
            chat = client.chat.completions.create(**kwargs)
            return (chat.choices[0].message.content or "").strip()

        try:
            text = try_model(requested_model, with_temperature=False)
            return jsonify({"text": text})
        except Exception as primary_error:
            logging.warning("Primary model '%s' failed: %s", requested_model, primary_error)
            fallback_model = "gpt-4o-mini"
            if requested_model != fallback_model:
                try:
                    text = try_model(fallback_model, with_temperature=True)
                    return jsonify({"text": text})
                except Exception:
                    pass
            raise primary_error
    except Exception as e:
        logging.exception("/api/chat error")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Allow overriding the port via `PORT` env var (default 5000)
    port = int(os.getenv("PORT", "5000"))
    # `FLASK_DEBUG=1` enables auto-reload + debugger (local dev only)
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


