"""
Flask app: Eugene the AI Sea Cow chat interface.

This is the main Python file that runs the web server. It provides two endpoints:
1. GET  /           → Serves the chat UI (HTML page)
2. POST /api/chat   → Handles chat messages and returns AI responses

The app uses OpenAI and Anthropic APIs to generate responses and can perform
live web searches using Brave Search API with optional source filtering.

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
import re       # For regular expression pattern matching
import requests  # For making HTTP requests to Brave Search API
import json      # For parsing JSON responses
from datetime import datetime  # For working with dates and times

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

# Claude model names mapping (only models that work with current API access)
CLAUDE_MODELS = {
    "claude-3-5-haiku-20241022",  # Claude 3.5 Haiku (latest, fastest)
    "claude-3-haiku-20240307"     # Claude 3 Haiku (stable)
}

# Data source configuration
# Maps source identifiers to their URLs and pronoun replacements
DATA_SOURCES = {
    "bryancounty": {
        "url": "bryancountyga.com",
        "name": "Bryan County",
        "your": "Bryan County's",
        "you": "Bryan County"
    },
    "savannah": {
        "url": "seda.org",
        "name": "Chatham County",
        "your": "Chatham County's",
        "you": "Chatham County"
    },
    "uwce": {
        "url": "uwce.org",
        "name": "United Way of the Coastal Empire",
        "your": "United Way of the Coastal Empire's",
        "you": "United Way of the Coastal Empire"
    },
    "fred": {
        "url": "fred.stlouisfed.org",
        "name": "Federal Reserve Economic Data",
        "your": "fred.stlouisfed.org's",
        "you": "fred.stlouisfed.org"
    },
    "gov": {
        "url": ".gov",
        "name": "Government Sources",
        "your": "government's",
        "you": "the government"
    },
    "datausa": {
        "url": "datausa.io",
        "name": "Data USA",
        "your": "Data USA's",
        "you": "Data USA"
    },
    "all": {
        "url": "(site:bryancountyga.com OR site:seda.org OR site:uwce.org OR site:fred.stlouisfed.org OR site:datausa.io)",
        "name": "All Sources",
        "your": "these sources'",
        "you": "these sources"
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def substitute_pronouns(query, source):
    """
    Substitute pronouns in the query based on the data source.
    Makes searches more specific to the organization/region.
    
    Args:
        query: The search query string
        source: Data source identifier (e.g., "bryancounty", "savannah")
    
    Returns:
        Query with pronouns replaced
    """
    if source not in DATA_SOURCES:
        return query
    
    config = DATA_SOURCES[source]
    
    # Replace "your" and "you" with source-specific terms
    query = re.sub(r'\byour\b', config["your"], query, flags=re.IGNORECASE)
    query = re.sub(r'\byou\b', config["you"], query, flags=re.IGNORECASE)
    
    return query


def apply_site_filter(query, source):
    """
    Apply site: filter to search query based on data source.
    
    Args:
        query: The search query string
        source: Data source identifier (e.g., "bryancounty", "savannah")
    
    Returns:
        Query with site: filter prepended
    """
    if source not in DATA_SOURCES:
        return query
    
    config = DATA_SOURCES[source]
    
    # For "all" source, the URL already contains the OR logic
    if source == "all":
        return f"{config['url']} {query}"
    else:
        return f"site:{config['url']} {query}"


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


def bea_api_search(dataset, table, geography, year=None):
    """
    Fetch data from the Bureau of Economic Analysis (BEA) API.
    
    Args:
        dataset: BEA dataset name (e.g., 'Regional', 'NIPA')
        table: Table code (e.g., 'CAINC1' for personal income)
        geography: Geographic identifier (e.g., 'COUNTY' or 'STATE')
        year: Year or 'ALL' for all available years
        
    Returns:
        Dictionary with BEA data or None if error
    """
    api_key = os.getenv("BEA_API_KEY")
    if not api_key:
        logging.warning("BEA_API_KEY not set, cannot fetch BEA data")
        return None
    
    try:
        url = "https://apps.bea.gov/api/data"
        params = {
            "UserID": api_key,
            "method": "GetData",
            "datasetname": dataset,
            "TableName": table,
            "GeoFips": geography,
            "Year": year or "LAST5",
            "ResultFormat": "JSON"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("BEAAPI", {}).get("Results"):
            logging.info(f"BEA API returned data for {dataset}/{table}")
            return data["BEAAPI"]["Results"]
        return None
        
    except Exception as e:
        logging.error(f"BEA API error: {e}")
        return None


def bls_api_search(series_ids, start_year=None, end_year=None):
    """
    Fetch data from the Bureau of Labor Statistics (BLS) API.
    
    Args:
        series_ids: List of BLS series IDs (e.g., ['LAUCN130510000000003'] for unemployment)
        start_year: Start year (optional)
        end_year: End year (optional)
        
    Returns:
        Dictionary with BLS data or None if error
    """
    api_key = os.getenv("BLS_API_KEY")
    # BLS API works without key but has lower rate limits
    
    try:
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        
        payload = {
            "seriesid": series_ids,
            "startyear": start_year or str(datetime.now().year - 5),
            "endyear": end_year or str(datetime.now().year)
        }
        
        if api_key:
            payload["registrationkey"] = api_key
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "REQUEST_SUCCEEDED":
            logging.info(f"BLS API returned data for {len(series_ids)} series")
            return data.get("Results", {}).get("series", [])
        return None
        
    except Exception as e:
        logging.error(f"BLS API error: {e}")
        return None


def census_acs_search(geography_type, geography_id, variables, year=2022):
    """
    Fetch data from the Census Bureau's American Community Survey (ACS) 5-Year Estimates API.
    
    Args:
        geography_type: Type of geography (e.g., 'county', 'state', 'place')
        geography_id: Geographic identifier (e.g., '13:051' for Chatham County, GA)
        variables: List of ACS variable codes (e.g., ['B19013_001E'] for median household income)
        year: ACS year (default 2022)
        
    Returns:
        Dictionary with variable data or None if error
    """
    api_key = os.getenv("CENSUS_API_KEY")
    if not api_key:
        logging.warning("CENSUS_API_KEY not set, cannot fetch Census data")
        return None
    
    try:
        # Common ACS variable codes:
        # B19013_001E - Median Household Income
        # B01003_001E - Total Population
        # B17001_002E - Population below poverty level
        # B23025_005E - Unemployed population
        
        # Build the API URL
        variables_str = ",".join(variables + ["NAME"])  # Always include NAME
        url = f"https://api.census.gov/data/{year}/acs/acs5"
        
        params = {
            "get": variables_str,
            "key": api_key
        }
        
        # Handle geography specification
        if geography_type == "county" and ":" in geography_id:
            state_id, county_id = geography_id.split(":")
            params["for"] = f"county:{county_id}"
            params["in"] = f"state:{state_id}"
        else:
            params["for"] = f"{geography_type}:{geography_id}"
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if len(data) < 2:
            return None
        
        # Parse response (first row is headers, second row is data)
        headers = data[0]
        values = data[1]
        
        result = {}
        for i, header in enumerate(headers):
            if i < len(values):
                result[header] = values[i]
        
        logging.info(f"Census ACS API returned data for {result.get('NAME', 'unknown')}")
        return result
        
    except Exception as e:
        logging.error(f"Census ACS API error: {e}")
        return None


def fetch_economic_data(query, location=None):
    """
    Smart economic data fetcher that tries multiple APIs in order:
    1. ACS (American Community Survey / Census) - for income/demographic data
    2. BLS (Bureau of Labor Statistics) - for employment data
    3. BEA (Bureau of Economic Analysis) - for GDP data
    4. Falls back to DataUSA and FRED web search
    
    Args:
        query: User's question/query
        location: Optional location identifier (not currently used)
        
    Returns:
        Tuple of (data, source) where data is the API response and source is the API name,
        or (None, None) if no API data found
    """
    print(f"\n===== fetch_economic_data called =====")
    print(f"Query: '{query}'")
    print(f"Location: '{location}'")
    logging.info(f"===== fetch_economic_data called with query: '{query}', location: '{location}' =====")
    query_lower = query.lower()
    
    # Detect year in query (e.g., "2022", "in 2023", "for 2021")
    import re
    year_match = re.search(r'\b(20\d{2})\b', query)
    requested_year = int(year_match.group(1)) if year_match else 2023  # Default to 2023
    print(f">>> Detected year: {requested_year}")
    
    # Detect what kind of economic data is being requested
    is_income = any(word in query_lower for word in ['income', 'earnings', 'wage', 'salary'])
    is_employment = any(word in query_lower for word in ['employment', 'unemployment', 'job', 'labor'])
    is_gdp = any(word in query_lower for word in ['gdp', 'gross domestic product', 'economic output'])
    is_population = any(word in query_lower for word in ['population', 'demographic'])
    
    # Detect location from query text (not dropdown value)
    has_location = any(word in query_lower for word in ['county', 'chatham', 'savannah', 'bryan', 'georgia', 'ga'])
    
    # Try ACS first for demographic/income data
    if (is_income or is_population) and has_location:
        try:
            # Map common county names to FIPS codes
            # Chatham County, GA (includes Savannah)
            if 'chatham' in query_lower or 'savannah' in query_lower:
                variables = []
                if is_income:
                    variables.append('B19013_001E')  # Median household income
                if is_population:
                    variables.append('B01003_001E')  # Total population
                
                if variables:
                    print(f">>> Attempting ACS API for Chatham County, GA: {variables} (year={requested_year})")
                    logging.info(f"Attempting ACS API for Chatham County, GA: {variables} (year={requested_year})")
                    acs_data = census_acs_search('county', '13:051', variables, year=requested_year)
                    print(f">>> ACS API result: {acs_data}")
                    if acs_data:
                        print(f">>> ACS API SUCCESS!")
                        logging.info(f"ACS API SUCCESS: {acs_data}")
                        return (acs_data, 'ACS')
                    else:
                        print(">>> ACS API returned no data")
                        logging.warning("ACS API returned no data")
            
            # Bryan County, GA
            elif 'bryan' in query_lower:
                variables = []
                if is_income:
                    variables.append('B19013_001E')
                if is_population:
                    variables.append('B01003_001E')
                
                if variables:
                    logging.info(f"Attempting ACS API for Bryan County, GA: {variables} (year={requested_year})")
                    acs_data = census_acs_search('county', '13:029', variables, year=requested_year)
                    if acs_data:
                        return (acs_data, 'ACS')
        except Exception as e:
            logging.error(f"ACS attempt failed: {e}")
    
    # Try BLS for employment data
    if is_employment and has_location:
        try:
            # Chatham County unemployment
            if 'chatham' in query_lower or 'savannah' in query_lower:
                series_ids = ['LAUCN130510000000003']  # Chatham County, GA unemployment
                logging.info(f"Attempting BLS API for Chatham County: {series_ids}")
                bls_data = bls_api_search(series_ids)
                if bls_data:
                    return (bls_data, 'BLS')
            
            # Bryan County unemployment
            elif 'bryan' in query_lower:
                series_ids = ['LAUCN130290000000003']  # Bryan County, GA unemployment
                logging.info(f"Attempting BLS API for Bryan County: {series_ids}")
                bls_data = bls_api_search(series_ids)
                if bls_data:
                    return (bls_data, 'BLS')
        except Exception as e:
            logging.error(f"BLS attempt failed: {e}")
    
    # Try BEA for GDP/economic data
    if is_gdp and has_location:
        try:
            logging.info("Attempting BEA API for GDP data")
            bea_data = bea_api_search('Regional', 'CAGDP1', 'COUNTY')
            if bea_data:
                return (bea_data, 'BEA')
        except Exception as e:
            logging.error(f"BEA attempt failed: {e}")
    
    # No API data found
    logging.info("No economic API data found, will fall back to web search")
    return (None, None)


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
        
        # Get the data source filter (for site-specific searches)
        source = request.args.get("source", "")
        
        # Check if web search is enabled via the ?web=1 query parameter
        use_web = request.args.get("web") == "1"
        
        logging.info(f"===== /api/chat request: model={model}, source={source}, use_web={use_web} =====")
        logging.info(f"Last user message: {messages[-1] if messages else 'None'}")
        
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
                    # Extract clean query (remove any [INSTRUCTIONS: ...] added by frontend)
                    raw_query = last_user_msg["content"]
                    search_query = raw_query.split('[INSTRUCTIONS:')[0].strip()
                    
                    # Substitute pronouns based on data source
                    search_query = substitute_pronouns(search_query, source)
                    
                    # Try economic data APIs first (BEA, BLS, ACS)
                    api_data, api_source = fetch_economic_data(search_query, location=source)
                    
                    if api_data and api_source:
                        # We got data from an official API!
                        print(f">>> [Claude] Using {api_source} API data instead of web search")
                        logging.info(f"Using {api_source} API data instead of web search")
                        formatted_api_data = f"\n\nData from {api_source} API:\n{json.dumps(api_data, indent=2)}\n\n"
                        api_instruction = (
                            formatted_api_data +
                            f"Use this official {api_source} data to answer the user's question. "
                            "The B19013_001E field contains the median household income value (5-year estimate). "
                            "When presenting numerical data, format them in **bold** using markdown for clarity. "
                            "Present your answer in a single paragraph without extra line breaks between sentences. "
                            "Use bullets that start with the Unicode bullet symbol (•) instead of dashes or numbers. "
                            "After the factual answer, add an 'Insights' section with 2–4 concise bullet points."
                        )
                        print(f">>> [Claude] Formatted API instruction: {api_instruction[:200]}...")
                        system_content += api_instruction
                        search_results = None  # Skip web search
                    else:
                        # Fall back to web search with DataUSA and FRED priority
                        # Add site: filter based on source parameter
                        search_query = apply_site_filter(search_query, source)
                        
                        # If no specific source, prioritize DataUSA and FRED for economic queries
                        if source == 'all' and any(word in search_query.lower() for word in ['income', 'wage', 'employment', 'unemployment', 'gdp', 'economy']):
                            # Search DataUSA first
                            logging.info(f"Trying DataUSA for economic data: site:datausa.io {search_query}")
                            search_results = brave_search(f"site:datausa.io {search_query}", count=5)
                            
                            # If DataUSA doesn't have good results, try FRED
                            if not search_results or len(search_results) < 2:
                                logging.info(f"Trying FRED for economic data: site:fred.stlouisfed.org {search_query}")
                                fred_results = brave_search(f"site:fred.stlouisfed.org {search_query}", count=5)
                                if fred_results:
                                    search_results = fred_results
                        else:
                            logging.info(f"Performing Brave Search for Claude: {search_query}")
                            search_results = brave_search(search_query, count=10)
                    
                    if search_results:
                        # Add search results to system prompt
                        formatted_results = format_search_results(search_results)
                        system_content += (
                            f"\n\n{formatted_results}\n\n"
                            "Use these search results to answer the user's question. Cite sources with URLs when possible. "
                            "When presenting numerical data (statistics, dollar amounts, percentages, years, etc.), format them in **bold** using markdown for clarity. "
                            "Use bullets that start with the Unicode bullet symbol (•) instead of dashes or numbers. "
                            "CRITICAL: Only use numerical values that are EXPLICITLY stated in the search results. Do NOT estimate, interpolate, or make up numbers. "
                            "If the user asks for a single data point (e.g., 'What is the median income in 2022?') and you find it in the search results, provide it. "
                            "If the user asks for time-series data (e.g., income from 2015-2023) and year-by-year values are NOT in the search results, provide the link and say: 'We are currently unable to display the year-by-year data directly, but you can view the complete dataset at [link]. We are working on integrating directly with the U.S. Census Bureau to provide this data in future updates.' "
                            "After the factual answer, add an 'Insights' section with 2–4 concise bullet points that synthesize patterns, comparisons, trends, or implications grounded in the cited sources. "
                            "Do not invent facts; if the evidence is insufficient, state that explicitly."
                        )
            # Always encourage a concise Insights section even without search
            system_content += (
                "\n\nWhen you present the answer, keep it concise and clear. "
                "Use bullets that start with the Unicode bullet symbol (•) instead of dashes or numbers. "
                "Then add an 'Insights' section with 2–4 bullets that provide thoughtful analysis grounded in the referenced sources. "
                "Avoid speculation beyond the evidence."
            )
            
            # Log system content for debugging chartjson
            if "time range" in last_user_message.lower() or ("from" in last_user_message.lower() and "to" in last_user_message.lower()):
                logging.info(f"[Claude] Time range query detected. System prompt includes chartjson: {'chartjson' in system_content}")
            
            # Call Claude API
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.5,  # Balanced consistency and naturalness
                system=system_content.strip() if system_content else None,
                messages=claude_messages
            )
            
            # Extract text from response
            text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    text += block.text
            
            # Log if chartjson was generated
            if "chartjson" in text:
                logging.info(f"[Claude] Response contains chartjson: {text[:200]}")
            elif "time range" in last_user_message.lower() or ("from" in last_user_message.lower() and "to" in last_user_message.lower()):
                logging.warning(f"[Claude] Time range query but no chartjson in response")
            
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
                # Extract clean query (remove any [INSTRUCTIONS: ...] added by frontend)
                raw_query = last_user_msg.get("content", "")
                search_query = raw_query.split('[INSTRUCTIONS:')[0].strip()
                
                # Substitute pronouns based on data source
                search_query = substitute_pronouns(search_query, source)
                
                # Try economic data APIs first (BEA, BLS, ACS)
                api_data, api_source = fetch_economic_data(search_query, location=source)
                
                search_instruction = None  # Will be set by either API or web search
                
                if api_data and api_source:
                    # We got data from an official API!
                    print(f">>> Using {api_source} API data instead of web search")
                    logging.info(f"Using {api_source} API data instead of web search")
                    
                    # Extract year from API data if available (ACS includes it in the response)
                    year_info = api_data.get('year', 'latest')
                    
                    formatted_api_data = f"\n\nData from {api_source} API:\n{json.dumps(api_data, indent=2)}\n\n"
                    search_instruction = (
                        formatted_api_data +
                        f"Use this official {api_source} data to answer the user's question. "
                        "The B19013_001E field contains the median household income value (5-year estimate). "
                        "When presenting numerical data, format them in **bold** using markdown for clarity. "
                        "Present your answer in a single paragraph without extra line breaks between sentences. "
                        "Use bullets that start with the Unicode bullet symbol (•) instead of dashes or numbers. "
                        "After the factual answer, add an 'Insights' section with 2–4 concise bullet points."
                    )
                    print(f">>> Formatted API instruction: {search_instruction[:200]}...")
                else:
                    # Fall back to web search with DataUSA and FRED priority
                    # Add site: filter based on source parameter
                    search_query = apply_site_filter(search_query, source)
                    
                    # If no specific source, prioritize DataUSA and FRED for economic queries
                    if source == 'all' and any(word in search_query.lower() for word in ['income', 'wage', 'employment', 'unemployment', 'gdp', 'economy']):
                        # Search DataUSA first
                        logging.info(f"Trying DataUSA for economic data: site:datausa.io {search_query}")
                        search_results = brave_search(f"site:datausa.io {search_query}", count=5)
                        
                        # If DataUSA doesn't have good results, try FRED
                        if not search_results or len(search_results) < 2:
                            logging.info(f"Trying FRED for economic data: site:fred.stlouisfed.org {search_query}")
                            fred_results = brave_search(f"site:fred.stlouisfed.org {search_query}", count=5)
                            if fred_results:
                                search_results = fred_results
                    else:
                        logging.info(f"Performing Brave Search for GPT: {search_query}")
                        search_results = brave_search(search_query, count=10)
                    
                    # Format web search results into instruction
                    if search_results:
                        formatted_results = format_search_results(search_results)
                        search_instruction = (
                            f"\n\n{formatted_results}\n\n"
                            "Use these search results to answer the user's question. Cite sources with URLs when possible. "
                            "When presenting numerical data (statistics, dollar amounts, percentages, years, etc.), format them in **bold** using markdown for clarity. "
                            "Use bullets that start with the Unicode bullet symbol (•) instead of dashes or numbers. "
                            "CRITICAL: Only use numerical values that are EXPLICITLY stated in the search results. Do NOT estimate, interpolate, or make up numbers. "
                            "If the user asks for a single data point (e.g., 'What is the median income in 2022?') and you find it in the search results, provide it. "
                            "If the user asks for time-series data (e.g., income from 2015-2023) and year-by-year values are NOT in the search results, provide the link and say: 'We are currently unable to display the year-by-year data directly, but you can view the complete dataset at [link]. We are working on integrating directly with the U.S. Census Bureau to provide this data in future updates.' "
                            "After the factual answer, add an 'Insights' section with 2–4 concise bullet points that synthesize patterns, comparisons, trends, or implications grounded in the cited sources. "
                            "Do not invent facts; if the evidence is insufficient, state that explicitly."
                        )
                
                # Now add the instruction (from either API or web search) to messages
                if search_instruction:
                    print(f">>> Adding instruction to messages (API={bool(api_data)}, Web={bool(not api_data)})")
                    # Find system message or create one
                    system_msg_found = False
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            print(f">>> Appending to existing system message")
                            msg["content"] += search_instruction
                            system_msg_found = True
                            break
                    
                    # If no system message exists, add one at the beginning
                    if not system_msg_found:
                        print(f">>> Creating new system message with instruction")
                        messages.insert(0, {"role": "system", "content": search_instruction.strip()})
                else:
                    # Ensure insights guidance is present even without search results
                    insights_only_instruction = (
                        "After the factual answer, add an 'Insights' section with 2–4 concise bullet points that "
                        "synthesize patterns, comparisons, trends, or implications grounded in the provided sources or prior context. "
                        "Use bullets that start with the Unicode bullet symbol (•) instead of dashes or numbers. "
                        "Do not invent facts; if evidence is insufficient, say so."
                    )
                    system_msg_found = False
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            msg["content"] = (msg.get("content", "") + "\n\n" + insights_only_instruction).strip()
                            system_msg_found = True
                            break
                    if not system_msg_found:
                        messages.insert(0, {"role": "system", "content": insights_only_instruction})
        
        # ====================================================================
        # 4. STANDARD OPENAI CHAT MODE (WITH OR WITHOUT SEARCH RESULTS)
        # ====================================================================
        
        # Use the standard Chat Completions API
        # If search results were found, they're now in the messages
        chat = openai_client.chat.completions.create(
            model=model,        # Which AI model to use (from dropdown)
            messages=messages,  # The conversation history (with search results if available)
            temperature=0.5     # Balanced consistency and naturalness
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