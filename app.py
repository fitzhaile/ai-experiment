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

# Standard Python libraries - import these FIRST
import logging  # For logging messages to console
import os       # For reading environment variables
from pathlib import Path  # For working with file paths
import requests  # For making HTTP requests to Brave Search API
import json      # For parsing JSON responses

# OpenAI API client
from openai import OpenAI

# Anthropic API client for Claude models
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic package not installed. Install with: pip install anthropic")


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

# Check if the Anthropic API key is set (for Claude models)
if os.getenv("ANTHROPIC_API_KEY"):
    logging.info("ANTHROPIC_API_KEY detected: %s***", (os.getenv("ANTHROPIC_API_KEY") or "")[:7])
else:
    logging.warning("ANTHROPIC_API_KEY not set (Claude models will not work)")

# Check if Brave Search API key is set (for Claude web search)
if os.getenv("BRAVE_API_KEY"):
    logging.info("BRAVE_API_KEY detected: %s***", (os.getenv("BRAVE_API_KEY") or "")[:7])
else:
    logging.warning("BRAVE_API_KEY not set (Claude web search will not work)")

# Initialize the Flask web application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows the frontend JavaScript to call our API endpoints
CORS(app)

# Disable caching for development to prevent browser cache issues
@app.after_request
def add_header(response):
    """Add cache control headers to prevent aggressive browser caching during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Create the OpenAI client once when the app starts
# This client will be reused for all API requests (more efficient than creating it each time)
# Set a longer timeout (10 minutes) to handle deep research models that take a long time
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=600.0  # 10 minutes timeout for deep research models
)

# Create the Anthropic client for Claude models (if available)
anthropic_client = None
if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
    anthropic_client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=600.0  # 10 minutes timeout
    )

# The AI model we'll use for all requests (default fallback)
# gpt-4o is the GPT-4 flagship model - balanced performance and quality
# This is used when no model is specified in the API request
MODEL = "gpt-4o"

# Claude model names mapping
CLAUDE_MODELS = {
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-latest",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307"
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def brave_search(query, count=10):
    """
    Search the web using Brave Search API.
    
    Args:
        query: The search query string
        count: Number of results to return (default 10)
    
    Returns:
        List of search results with title, url, and description
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        logging.warning("BRAVE_API_KEY not set, cannot perform web search")
        return []
    
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key
        }
        params = {
            "q": query,
            "count": count
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # Extract web results
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", "")
            })
        
        logging.info(f"Brave Search returned {len(results)} results for: {query}")
        return results
        
    except Exception as e:
        logging.error(f"Brave Search error: {e}")
        return []


def format_search_results(results):
    """
    Format search results into a readable string for the AI.
    
    Args:
        results: List of search result dictionaries
    
    Returns:
        Formatted string with search results
    """
    if not results:
        return "No search results found."
    
    formatted = "Here are the web search results:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result['title']}\n"
        formatted += f"   URL: {result['url']}\n"
        formatted += f"   {result['description']}\n\n"
    
    return formatted


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
    import time
    # Add a version parameter for cache busting
    version = str(int(time.time()))
    return render_template("index.html", v=version)


@app.post("/api/chat")
def api_chat():
    """
    Chat API endpoint - handles conversation with the AI.
    
    This endpoint receives a list of messages (the conversation history)
    and returns the AI's response. It can optionally use web search if
    the user has enabled it via the ?web=1 query parameter.
    
    Supports both OpenAI (GPT) and Anthropic (Claude) models.
    
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
        model=<model_name> : Specify which AI model to use (optional)
    
    Returns (JSON):
        Success: {"text": "The AI's response text", "web": true/false}
        Error:   {"error": "Error message"}
    """
    try:
        # ====================================================================
        # 1. VALIDATE REQUEST
        # ====================================================================
        
        # Get the JSON data from the request body
        # silent=True means don't crash if the JSON is invalid, just return None
        data = request.get_json(silent=True) or {}
        
        # Extract the messages array from the request
        messages = data.get("messages")
        
        # Validate that messages is a list and not empty
        if not isinstance(messages, list) or not messages:
            return jsonify({"error": "messages[] required"}), 400
        
        # Get the model from query parameter, or use the default
        # This allows the user to select which model to use via the dropdown
        model = request.args.get("model", MODEL)
        
        # Check if web search is enabled via the ?web=1 query parameter
        use_web = request.args.get("web") == "1"
        
        # ====================================================================
        # 2. CLAUDE (ANTHROPIC) MODELS
        # ====================================================================
        
        if model in CLAUDE_MODELS:
            # Check if Anthropic client is available
            if not anthropic_client:
                return jsonify({"error": "Claude models not available. Install anthropic package and set ANTHROPIC_API_KEY"}), 500
            
            # Separate system messages from conversation
            system_content = ""
            claude_messages = []
            
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role")
                content = msg.get("content", "")
                
                if role == "system":
                    system_content += content + "\n\n"
                elif role in ("user", "assistant"):
                    claude_messages.append({"role": role, "content": content})
            
            # If web search is enabled, perform search and add results
            if use_web and claude_messages:
                # Get the last user message for search query
                last_user_msg = next((m for m in reversed(claude_messages) if m["role"] == "user"), None)
                
                if last_user_msg:
                    search_query = last_user_msg["content"]
                    logging.info(f"Performing Brave Search for Claude: {search_query}")
                    
                    search_results = brave_search(search_query, count=10)
                    
                    if search_results:
                        # Add search results to system prompt
                        formatted_results = format_search_results(search_results)
                        system_content += f"\n\n{formatted_results}\n\nUse these search results to answer the user's question. Cite sources with URLs when possible."
            
            # Call Claude API
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_content.strip() if system_content else None,
                messages=claude_messages
            )
            
            # Extract text from response
            text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    text += block.text
            
            text = text.strip()
            
            return jsonify({"text": text, "web": use_web and bool(search_results) if use_web else False})
        
        # ====================================================================
        # 3. OPENAI (GPT) MODELS WITH BRAVE SEARCH
        # ====================================================================
        
        # Make sure the API key is set
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "OPENAI_API_KEY not set"}), 500
        
        # If web search is enabled, use Brave Search API
        search_results = []
        if use_web:
            # Get the last user message for search query
            last_user_msg = next((m for m in reversed(messages) if isinstance(m, dict) and m.get("role") == "user"), None)
            
            if last_user_msg:
                search_query = last_user_msg.get("content", "")
                logging.info(f"Performing Brave Search for GPT: {search_query}")
                
                search_results = brave_search(search_query, count=10)
                
                if search_results:
                    # Add search results to the system message
                    formatted_results = format_search_results(search_results)
                    search_instruction = f"\n\n{formatted_results}\n\nUse these search results to answer the user's question. Cite sources with URLs when possible."
                    
                    # Find system message or create one
                    system_msg_found = False
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            msg["content"] += search_instruction
                            system_msg_found = True
                            break
                    
                    # If no system message exists, add one at the beginning
                    if not system_msg_found:
                        messages.insert(0, {"role": "system", "content": search_instruction.strip()})
        
        # ====================================================================
        # 4. STANDARD OPENAI CHAT MODE (WITH OR WITHOUT SEARCH RESULTS)
        # ====================================================================
        
        # Use the standard Chat Completions API
        # If search results were found, they're now in the messages
        chat = openai_client.chat.completions.create(
            model=model,        # Which AI model to use (from dropdown)
            messages=messages   # The conversation history (with search results if available)
        )
        
        # Extract the AI's response text from the API response
        # choices[0] gets the first (and usually only) response
        # message.content is the actual text
        text = (chat.choices[0].message.content or "").strip()
        
        # Return the response as JSON
        return jsonify({"text": text, "web": use_web and bool(search_results)})
        
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