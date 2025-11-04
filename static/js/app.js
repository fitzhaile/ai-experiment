// ============================================================================
// Eugene the AI Sea Cow - Chat Interface JavaScript
// ============================================================================
//
// This file handles all the interactive behavior of the chat interface:
// - Displaying messages in the chat log
// - Sending user messages to the server
// - Receiving and displaying AI responses
// - Converting markdown to HTML for better formatting
// - Managing the ".gov only" checkbox for filtering web search results
//

// ============================================================================
// DOM ELEMENTS (Get references to HTML elements)
// ============================================================================

// Get the submit button
const btn = document.getElementById('btn');

// Get the text input where users type their messages
const promptEl = document.getElementById('prompt');

// Get the chat log container where messages are displayed
const logEl = document.getElementById('log');

// Get the status message element (shows "Looking for your answers...")
const statusEl = document.getElementById('status');

// Get the source filter dropdown
const sourceFilterSelect = document.getElementById('sourceFilter');

// Get the "Change source" link
const changeSourceLink = document.getElementById('changeSourceLink');

// Get the "Cancel" link for source
const cancelSourceLink = document.getElementById('cancelSourceLink');

// Get the model selector dropdown
const modelSelect = document.getElementById('modelSelect');

// Get the "Change model" link
const changeModelLink = document.getElementById('changeModelLink');

// Get the "Cancel" link
const cancelModelLink = document.getElementById('cancelModelLink');

// Get the deep research warning message element
const deepResearchWarning = document.getElementById('deepResearchWarning');


// ============================================================================
// CONVERSATION STATE
// ============================================================================

// Array to store the entire conversation history
// This includes system messages, user messages, and assistant responses
// The system message tells the AI how to behave

// Default (general) system message
const generalSystemMessage = 'You are a concise assistant that writes clear answers.';

// Specialized system message for Black/African American topics
const blackTopicsSystemMessage = `You are a specialized AI assistant focused EXCLUSIVELY on Black/African American topics, including:
- History, culture, and heritage
- Current events and news affecting Black communities
- Achievements, innovations, and contributions by Black individuals
- Social justice, civil rights, and equity issues
- Business, economics, and community development
- Arts, literature, music, and entertainment
- Education and scholarship
- Health, wellness, and social issues

Guidelines:
- When performing web searches, prioritize sources from .gov, .edu, HBCUs, and Black-owned media
- If a query is completely unrelated to Black/African American topics, politely explain your specialization and ask the user to rephrase or ask something relevant to the Black/African American experience
- If a query has indirect relevance to Black communities, explain the connection
- Always provide historical context when relevant
- Cite sources whenever possible
- Be educational, respectful, and thorough

Statistical Data (Census/ACS, ABS, BLS, etc.):
- For ANY requests involving Census Bureau (ACS), American Community Survey, Bureau of Labor Statistics (BLS), or other statistical agencies that have race categories, AUTOMATICALLY assume the user is asking for Black/African American data ONLY
- Look for categories like "Black alone", "Black or African American alone", "Black alone or in combination", or similar race designations
- If Black race category data exists, provide it without asking for clarification
- If Black race category data does NOT exist for that dataset, simply state: "This dataset does not include a separate Black/African American category"
- HOWEVER, if the user SPECIFICALLY requests data for another race (e.g., "What is the median income for White families in Atlanta?" or "Compare Black and Hispanic poverty rates"), honor that request and provide the requested data

CRITICAL - Data Sources and Recency:
- ALWAYS use data.census.gov as your PRIMARY source for all demographic and economic data
- data.census.gov is the official portal for detailed Census Bureau tables with race breakdowns
- ALWAYS use the MOST RECENT data available (check for latest year - typically 2023 or 2024 estimates)
- When searching web, use: "site:data.census.gov [topic] [location] Black"
- For county-level data, search: "site:data.census.gov [County Name] County [State] median household income Black"
- Look for ACS (American Community Survey) tables:
  * Table B19013B = Median Household Income (Black or African American Alone)
  * Table B17001B = Poverty Status (Black or African American Alone)
  * Table B23001B = Employment Status (Black or African American Alone)
- Always cite: table number, geography, year, and estimate type (1-year or 5-year)
- Example searches:
  * "site:data.census.gov Chatham County Georgia median household income Black 2023"
  * "site:data.census.gov table B19013B Chatham County Georgia"
  * "data.census.gov American Community Survey Chatham County Black income"

- Examples: 
  - "median household income in Atlanta" → search Census Bureau for Black household income in Atlanta, latest year
  - "unemployment rate in Georgia" → search BLS for Black unemployment rate in Georgia, most recent month
  - "median income for Asian families in Seattle" → provide Asian family income data from Census Bureau, latest year
  - "compare Black and White unemployment rates" → provide both from official sources with most recent data`;

// Initialize messages with the general system message
// This will be updated when the Black topics checkbox is checked
const messages = [
  { role: 'system', content: generalSystemMessage }
];


// ============================================================================
// RENDER FUNCTION - Display messages in the chat
// ============================================================================

function render() {
  /**
   * Displays all messages in the conversation.
   * 
   * This function:
   * 1. Clears the chat log
   * 2. Loops through all messages
   * 3. Creates a div for each message (except system messages)
   * 4. Applies styling based on role (user vs assistant)
   * 5. Converts markdown to HTML for assistant messages
   * 6. Scrolls to the bottom to show the latest message
   */
  
  // Clear the chat log
  logEl.innerHTML = '';
  
  // Check if there are any visible messages (non-system messages)
  const hasVisibleMessages = messages.some(m => m.role !== 'system');
  
  // If no messages yet, show a placeholder
  if (!hasVisibleMessages) {
    const placeholder = document.createElement('div');
    placeholder.className = 'placeholder';
    placeholder.textContent = "You're answers will show up here...so get to asking!";
    logEl.appendChild(placeholder);
    return;
  }
  
  // Loop through each message in the conversation
  for (const m of messages) {
    // Skip system messages (they're instructions for the AI, not part of the chat)
    if (m.role === 'system') continue;
    
    // Create a new div element for this message
    const div = document.createElement('div');
    
    // Add CSS classes: 'msg' for all messages, plus 'user' or 'assistant'
    // This controls the styling (color, alignment, etc.)
    div.className = 'msg ' + (m.role === 'user' ? 'user' : 'assistant');
    
    if (m.role === 'assistant') {
      // For assistant messages, convert markdown to HTML for better formatting
      // This makes **bold**, *italic*, links, etc. look nice
      div.innerHTML = renderMarkdown(m.content);
    } else {
      // For user messages, display as plain text
      // But remove the source filter instructions that we added internally
      let displayContent = m.content;
      displayContent = displayContent.replace(/\s*\(Only search and cite information from https:\/\/bryancountyga\.com\/ - use site:bryancountyga\.com in your web search\)\s*$/, '');
      displayContent = displayContent.replace(/\s*\(Only cite sources from \.gov domains\)\s*$/, '');
      div.textContent = displayContent;
    }
    
    // Add the message div to the chat log
    logEl.appendChild(div);
  }
  
  // Scroll to the bottom of the chat log to show the latest message
  logEl.scrollTop = logEl.scrollHeight;
}


// ============================================================================
// MARKDOWN RENDERER - Convert markdown text to HTML
// ============================================================================

function renderMarkdown(text) {
  /**
   * Converts markdown syntax to HTML for better formatting.
   * 
   * Supports:
   * - **bold text** → <strong>bold text</strong>
   * - *italic text* → <em>italic text</em>
   * - [link text](url) → <a href="url">link text</a>
   * - `code` → <code>code</code>
   * - # Heading → <h1>Heading</h1> (also ## and ###)
   * - Line breaks → <br>
   * 
   * @param {string} text - The markdown text to convert
   * @returns {string} - HTML string
   */
  
  let html = text;
  
  // Step 1: Escape HTML special characters to prevent security issues
  // This ensures that < > & are displayed as text, not interpreted as HTML
  html = html.replace(/&/g, '&amp;')   // & must be first
             .replace(/</g, '&lt;')    // < becomes &lt;
             .replace(/>/g, '&gt;');   // > becomes &gt;
  
  // Step 2: Convert markdown syntax to HTML tags
  
  // Headings (must be at the start of a line)
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  
  // Bold: **text** → <strong>text</strong>
  html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
  
  // Italic: *text* → <em>text</em>
  // Negative lookbehind/lookahead to avoid matching ** in bold text
  html = html.replace(/(?<!\*)\*([^\*]+)\*(?!\*)/g, '<em>$1</em>');
  
  // Links: [text](url) → <a href="url" target="_blank">text</a>
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, 
                      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  
  // Inline code: `code` → <code>code</code>
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Step 3: Convert line breaks to <br> tags
  html = html.replace(/\n/g, '<br>');
  
  return html;
}


// ============================================================================
// SEND FUNCTION - Send a message to the AI
// ============================================================================

async function send() {
  /**
   * Sends the user's message to the server and displays the AI's response.
   * 
   * This function:
   * 1. Gets the user's message from the input field
   * 2. Updates the system message based on the Black topics checkbox
   * 3. Adds a ".gov only" instruction if the checkbox is checked
   * 4. Adds the message to the conversation history
   * 5. Shows a loading indicator
   * 6. Sends the conversation to the server via POST request
   * 7. Receives and displays the AI's response
   * 8. Handles any errors that occur
   */
  
  // Get the user's message from the input field
  // If the input is empty, use a default message
  const content = promptEl.value.trim() || 'Say hello.';
  
  // Get the selected source filter
  const sourceFilter = sourceFilterSelect.value;
  
  // Update the system message based on the source filter selection
  // This must happen BEFORE adding the user message
  const blackTopicsMode = (sourceFilter === 'blacktopics');
  messages[0].content = blackTopicsMode ? blackTopicsSystemMessage : generalSystemMessage;
  
  // Build the user content with appropriate restrictions based on dropdown selection
  let userContent = content;
  
  // Apply source filter based on dropdown selection
  if (sourceFilter === 'bryancounty') {
    // Only search and cite information from bryancountyga.com
    userContent = content + ' (Only search and cite information from https://bryancountyga.com/ - use site:bryancountyga.com in your web search)';
  } else if (sourceFilter === 'gov') {
    // Only cite sources from .gov domains
    userContent = content + ' (Only cite sources from .gov domains)';
  } else if (sourceFilter === 'blacktopics') {
    // Black/African American topics mode - system message handles this
    // No additional instruction needed in user content
  }
  
  // Add the user's message to the conversation history
  messages.push({ role: 'user', content: userContent });
  
  // Clear the input field
  promptEl.value = '';
  
  // Update the display to show the user's message
  render();

  try {
    // ========================================================================
    // SHOW LOADING STATE
    // ========================================================================
    
    // Get the selected model from the dropdown
    const selectedModel = modelSelect.value;
    
    // Show different loading messages based on the model
    // Deep research models take much longer (minutes instead of seconds)
    if (selectedModel.includes('deep-research')) {
      statusEl.textContent = '🔬 Deep research in progress... this may take several minutes…';
    } else {
      statusEl.textContent = 'Looking for your answers…';
    }
    
    // Disable the button and input field while waiting for a response
    // This prevents the user from sending multiple messages at once
    btn.disabled = true;
    promptEl.disabled = true;
    
    // ========================================================================
    // SEND REQUEST TO SERVER
    // ========================================================================
    
    // Send a POST request to the /api/chat endpoint
    // ?web=1 enables web search (the AI can look up current information)
    // ?model=... specifies which OpenAI model to use
    const res = await fetch(`/api/chat?web=1&model=${selectedModel}`, {
      method: 'POST',                                    // HTTP method
      headers: { 'Content-Type': 'application/json' },  // Tell server we're sending JSON
      body: JSON.stringify({ messages })                // Convert messages array to JSON string
    });
    
    // Parse the JSON response from the server
    const data = await res.json();
    
    // ========================================================================
    // HANDLE RESPONSE
    // ========================================================================
    
    if (data && data.text) {
      // Success! Add the AI's response to the conversation
      messages.push({ role: 'assistant', content: data.text });
    } else if (data && data.error) {
      // Server returned an error message
      messages.push({ role: 'assistant', content: 'Error: ' + data.error });
    } else {
      // Unexpected response format
      messages.push({ role: 'assistant', content: '(no response)' });
    }
    
  } catch (e) {
    // ========================================================================
    // HANDLE NETWORK ERRORS
    // ========================================================================
    
    // If the fetch fails (network error, server down, etc.), show an error
    messages.push({ role: 'assistant', content: 'Error: ' + e });
  }
  
  // ==========================================================================
  // CLEAN UP
  // ==========================================================================
  
  // Update the display to show the AI's response
  render();
  
  // Clear the loading message
  statusEl.textContent = '';
  
  // Re-enable the button and input field
  btn.disabled = false;
  promptEl.disabled = false;
  
  // Put focus back on the input field so the user can type another message
  promptEl.focus();
}


// ============================================================================
// EVENT LISTENERS - Respond to user actions
// ============================================================================

// When the "Change source" link is clicked, show the source dropdown
if (changeSourceLink) {
  changeSourceLink.addEventListener('click', (e) => {
    // Prevent the link from navigating
    e.preventDefault();
    
    // Show the source dropdown and cancel link
    if (sourceFilterSelect) {
      sourceFilterSelect.style.display = 'inline-block';
    }
    if (cancelSourceLink) {
      cancelSourceLink.style.display = 'inline-block';
    }
    // Hide the "Change source" link
    changeSourceLink.style.display = 'none';
  });
}

// When the "Cancel" link for source is clicked, hide the dropdown
if (cancelSourceLink) {
  cancelSourceLink.addEventListener('click', (e) => {
    // Prevent the link from navigating
    e.preventDefault();
    
    // Hide the source dropdown and cancel link
    if (sourceFilterSelect) {
      sourceFilterSelect.style.display = 'none';
    }
    cancelSourceLink.style.display = 'none';
    // Show the "Change source" link
    if (changeSourceLink) {
      changeSourceLink.style.display = 'inline-block';
    }
  });
}

// When the source selector changes, hide it again and show the link
if (sourceFilterSelect) {
  sourceFilterSelect.addEventListener('change', () => {
    // Hide the dropdown and cancel link
    sourceFilterSelect.style.display = 'none';
    if (cancelSourceLink) {
      cancelSourceLink.style.display = 'none';
    }
    // Show the "Change source" link
    if (changeSourceLink) {
      changeSourceLink.style.display = 'inline-block';
    }
  });
}

// When the "Change model" link is clicked, show the dropdown
// Add null check to prevent errors if element doesn't exist
if (changeModelLink) {
  changeModelLink.addEventListener('click', (e) => {
    // Prevent the link from navigating
    e.preventDefault();
    
    // Toggle the dropdown visibility
    if (modelSelect && modelSelect.style.display === 'none') {
      // Show the dropdown and cancel link
      modelSelect.style.display = 'inline-block';
      if (cancelModelLink) {
        cancelModelLink.style.display = 'inline-block';
      }
      // Hide the "Change model" link
      changeModelLink.style.display = 'none';
    }
  });
}

// When the "Cancel" link is clicked, hide the dropdown
// Add null check to prevent errors if element doesn't exist
if (cancelModelLink) {
  cancelModelLink.addEventListener('click', (e) => {
    // Prevent the link from navigating
    e.preventDefault();
    
    // Hide the dropdown and cancel link
    if (modelSelect) {
      modelSelect.style.display = 'none';
    }
    cancelModelLink.style.display = 'none';
    // Show the "Change model" link
    if (changeModelLink) {
      changeModelLink.style.display = 'inline-block';
    }
  });
}

// When the model selector changes, hide it again and show the link
// Add null check to prevent errors if element doesn't exist
if (modelSelect) {
  modelSelect.addEventListener('change', () => {
    // Check if the selected model is a deep research model
    if (modelSelect.value.includes('deep-research')) {
      // Show the warning message
      if (deepResearchWarning) {
        deepResearchWarning.style.display = 'block';
      }
    } else {
      // Hide the warning message
      if (deepResearchWarning) {
        deepResearchWarning.style.display = 'none';
      }
    }
    
    // After selecting, hide the dropdown and cancel link, show the "Change model" link
    modelSelect.style.display = 'none';
    if (cancelModelLink) {
      cancelModelLink.style.display = 'none';
    }
    if (changeModelLink) {
      changeModelLink.style.display = 'inline-block';
    }
  });
}

// When the submit button is clicked, send the message
btn.addEventListener('click', send);

// When the user presses Enter in the input field, send the message
promptEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    // Prevent the default Enter behavior (which would add a newline)
    e.preventDefault();
    // Send the message
    send();
  }
});


// ============================================================================
// URL PARAMETER HANDLING
// ============================================================================

/**
 * Check for URL parameters and set source filter accordingly.
 * 
 * Supported parameters:
 * - ?focus=black-community → Sets source filter to "Black/African American topics" and hides the selector
 * 
 * Examples:
 * - http://127.0.0.1:8080/?focus=black-community
 */
function handleURLParameters() {
  try {
    // Get URL parameters from the current page URL
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check if focus parameter is set to "black-community"
    const focus = urlParams.get('focus');
    
    if (focus === 'black-community') {
      // Set the source filter to Black/African American topics
      if (sourceFilterSelect) {
        sourceFilterSelect.value = 'blacktopics';
      }
      
      // Hide the source selector when a URL parameter is set
      // This creates a cleaner, more focused interface
      const modelSelector = document.querySelector('.model-selector');
      if (modelSelector) {
        modelSelector.style.display = 'none';
      }
    }
  } catch (error) {
    // Log any errors but don't break the page
    console.error('Error handling URL parameters:', error);
  }
}


// ============================================================================
// INITIALIZATION
// ============================================================================

// Wait for the page to fully load before initializing
// This ensures all DOM elements are available
document.addEventListener('DOMContentLoaded', function() {
  // Handle URL parameters to set initial state
  handleURLParameters();
  
  // Display the initial state of the conversation (just the system message, which is hidden)
  render();
});