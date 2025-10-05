"""
Flask app: Eugene the AI Sea Cow chat interface.

This is the main Python file that runs the web server. It provides two endpoints:
1. GET  /           → Serves the chat UI (HTML page)
2. POST /api/chat   → Handles chat messages and returns AI responses

The app uses OpenAI's API to generate responses and can optionally perform
live web searches when the user enables the ".gov only" checkbox.

Environment variables (set in .env file):
- OPENAI_API_KEY (required): your OpenAI API key from platform.openai.com
- PORT (optional): which port to run the server on (default 5000)
- FLASK_DEBUG (optional): set to "1" for auto-reload during development
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Load environment variables from .env file
from dotenv import load_dotenv

# Flask web framework components
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS  # Allows cross-origin requests

# OpenAI API client
from openai import OpenAI

# Standard Python libraries
import logging  # For logging messages to console
import os       # For reading environment variables
from pathlib import Path  # For working with file paths


# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Load environment variables from the .env file in the same directory as this file
# This lets us keep secrets (like API keys) out of the code
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

# Set up logging so we can see what's happening
# INFO level means we'll see informational messages and errors
logging.basicConfig(level=logging.INFO)

# Check if the OpenAI API key is set and log a message
if os.getenv("OPENAI_API_KEY"):
    # Show first 7 characters of the key (for debugging) but hide the rest for security
    logging.info("OPENAI_API_KEY detected: %s***", (os.getenv("OPENAI_API_KEY") or "")[:7])
else:
    # Warn if the API key is missing (the app won't work without it)
    logging.warning("OPENAI_API_KEY not set")

# Initialize the Flask web application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows the frontend JavaScript to call our API endpoints
CORS(app)

# Create the OpenAI client once when the app starts
# This client will be reused for all API requests (more efficient than creating it each time)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# The AI model we'll use for all requests
# gpt-4o-mini is a fast, cost-effective model that's good for chat
MODEL = "gpt-4o-mini"


# ============================================================================
# ROUTES (URL ENDPOINTS)
# ============================================================================

@app.get("/")
def index():
    """
    Home page route - serves the chat interface.
    
    When a user visits http://localhost:8080/ in their browser,
    this function runs and returns the HTML page (templates/index.html).
    
    Returns:
        The rendered HTML page with the chat interface
    """
    return render_template("index.html")


@app.post("/api/chat")
def api_chat():
    """
    Chat API endpoint - handles conversation with the AI.
    
    This endpoint receives a list of messages (the conversation history)
    and returns the AI's response. It can optionally use web search if
    the user has enabled it via the ?web=1 query parameter.
    
    Expected POST data (JSON):
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "What is the capital of France?"},
                {"role": "assistant", "content": "The capital of France is Paris."},
                {"role": "user", "content": "What about Spain?"}
            ]
        }
    
    Query parameters:
        web=1 : Enable web search for live information
    
    Returns (JSON):
        Success: {"text": "The AI's response text", "web": true/false}
        Error:   {"error": "Error message"}
    """
    try:
        # ====================================================================
        # 1. VALIDATE REQUEST
        # ====================================================================
        
        # Make sure the API key is set (double-check even though we checked at startup)
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "OPENAI_API_KEY not set"}), 500

        # Get the JSON data from the request body
        # silent=True means don't crash if the JSON is invalid, just return None
        data = request.get_json(silent=True) or {}
        
        # Extract the messages array from the request
        messages = data.get("messages")
        
        # Validate that messages is a list and not empty
        if not isinstance(messages, list) or not messages:
            return jsonify({"error": "messages[] required"}), 400

        # ====================================================================
        # 2. WEB SEARCH MODE (OPTIONAL)
        # ====================================================================
        
        # Check if web search is enabled via the ?web=1 query parameter
        # Example: POST /api/chat?web=1
        use_web = request.args.get("web") == "1"
        
        if use_web:
            try:
                # Build a single text string from all messages in the conversation
                # This is needed because the Responses API (used for web search)
                # takes a single input string rather than a messages array
                
                # Use a list comprehension to format each message
                # Example output: ["System: You are helpful", "User: What is...", "Assistant: ..."]
                conversation_parts = [
                    f"{m.get('role', '').capitalize()}: {m.get('content', '')}"
                    for m in messages
                    if isinstance(m, dict) and m.get("role") in ("system", "user", "assistant")
                ]
                
                # Join all parts with double newlines for readability
                full_context = "\n\n".join(conversation_parts)
                
                # Call OpenAI's Responses API with the web_search tool
                # This allows the AI to search the web for current information
                resp = openai_client.responses.create(
                    model=MODEL,                          # Which AI model to use
                    input=full_context,                   # The conversation so far
                    tools=[{"type": "web_search"}],       # Enable web search tool
                    tool_choice="auto",                   # Let the AI decide when to search
                    store=False,                          # Don't store this conversation
                )
                
                # Extract the text from the response and remove extra whitespace
                text = (resp.output_text or "").strip()
                
                # If we got a response, return it with a flag indicating web search was used
                if text:
                    return jsonify({"text": text, "web": True})
                    
            except Exception as web_err:
                # If web search fails, log the error and fall through to regular chat
                logging.warning("Web search failed, falling back to chat.completions: %s", web_err)

        # ====================================================================
        # 3. STANDARD CHAT MODE (NO WEB SEARCH)
        # ====================================================================
        
        # Use the standard Chat Completions API (no web search)
        # This is faster and cheaper but doesn't have access to current information
        chat = openai_client.chat.completions.create(
            model=MODEL,        # Which AI model to use
            messages=messages   # The conversation history
        )
        
        # Extract the AI's response text from the API response
        # choices[0] gets the first (and usually only) response
        # message.content is the actual text
        text = (chat.choices[0].message.content or "").strip()
        
        # Return the response as JSON
        return jsonify({"text": text})
        
    except Exception as e:
        # If anything goes wrong, log the full error with stack trace
        logging.exception("/api/chat error")
        
        # Return an error response to the client
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    """
    This block only runs when you execute this file directly with:
        python app.py
    
    It doesn't run when the file is imported by another module or
    when using a production server like gunicorn.
    """
    
    # Get the port number from the PORT environment variable
    # If PORT is not set, default to 5000
    port = int(os.getenv("PORT", "5000"))
    
    # Check if debug mode is enabled via FLASK_DEBUG=1
    # Debug mode enables:
    # - Auto-reload when code changes
    # - Better error messages
    # - Interactive debugger
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    
    # Start the Flask development server
    # host="0.0.0.0" means accept connections from any IP address
    # (not just localhost, so you can access from other devices on your network)
    app.run(host="0.0.0.0", port=port, debug=debug)