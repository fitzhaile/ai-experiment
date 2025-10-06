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

// Get the ".gov only" checkbox
const govOnlyCheckbox = document.getElementById('govOnly');

// Get the model selector dropdown
const modelSelect = document.getElementById('modelSelect');

// Get the deep research warning message element
const deepResearchWarning = document.getElementById('deepResearchWarning');


// ============================================================================
// CONVERSATION STATE
// ============================================================================

// Array to store the entire conversation history
// This includes system messages, user messages, and assistant responses
// The system message tells the AI how to behave
const messages = [
  { role: 'system', content: 'You are a concise assistant that writes clear answers.' }
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
      // But remove the ".gov only" instruction that we added internally
      let displayContent = m.content;
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
  
  // Bold: **text** → <strong>text</strong>
  html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
  
  // Italic: *text* → <em>text</em>
  // The (?<!\*) and (?!\*) are "negative lookbehind/lookahead" assertions
  // They prevent matching the asterisks in **bold** text
  html = html.replace(/(?<!\*)\*([^\*]+)\*(?!\*)/g, '<em>$1</em>');
  
  // Links: [text](url) → <a href="url" target="_blank">text</a>
  // target="_blank" opens links in a new tab
  // rel="noopener noreferrer" is a security best practice for external links
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, 
                      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  
  // Inline code: `code` → <code>code</code>
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Headings (must be at the start of a line)
  // ### Heading → <h3>Heading</h3>
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  // ## Heading → <h2>Heading</h2>
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  // # Heading → <h1>Heading</h1>
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  
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
   * 2. Adds a ".gov only" instruction if the checkbox is checked
   * 3. Adds the message to the conversation history
   * 4. Shows a loading indicator
   * 5. Sends the conversation to the server via POST request
   * 6. Receives and displays the AI's response
   * 7. Handles any errors that occur
   */
  
  // Get the user's message from the input field
  // If the input is empty, use a default message
  const content = promptEl.value.trim() || 'Say hello.';
  
  // Check if the ".gov only" checkbox is checked
  const govOnly = govOnlyCheckbox.checked;
  
  // If ".gov only" is checked, add an instruction to the message
  // This tells the AI to only cite sources from .gov domains
  let userContent = content;
  if (govOnly) {
    userContent = content + ' (Only cite sources from .gov domains)';
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

// When the model selector changes, show/hide the deep research warning
modelSelect.addEventListener('change', () => {
  // Check if the selected model is a deep research model
  if (modelSelect.value.includes('deep-research')) {
    // Show the warning message
    deepResearchWarning.style.display = 'block';
  } else {
    // Hide the warning message
    deepResearchWarning.style.display = 'none';
  }
});

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
// INITIALIZATION
// ============================================================================

// Display the initial state of the conversation (just the system message, which is hidden)
render();