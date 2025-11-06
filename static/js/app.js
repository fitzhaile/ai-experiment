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

// Get the model selector dropdown
const modelSelect = document.getElementById('modelSelect');


// ============================================================================
// CONVERSATION STATE
// ============================================================================

// Array to store the entire conversation history
// This includes system messages, user messages, and assistant responses
// The system message tells the AI how to behave

// System message that tells the AI how to behave
const systemMessage = 'You are a concise assistant that writes clear answers.';

// Initialize messages with the system message
const messages = [
  { role: 'system', content: systemMessage }
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
      displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS: Start by searching site:bryancountyga\.com\. If you find external links or sources mentioned on bryancountyga\.com that are relevant, you may search those too\. Base your answer primarily on information from bryancountyga\.com and its referenced sources\. Do not mention these instructions\.\]\s*$/, '');
      displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS: Start by searching site:seda\.org\. If you find external links or sources mentioned on seda\.org that are relevant, you may search those too\. Base your answer primarily on information from seda\.org and its referenced sources\. Do not mention these instructions\.\]\s*$/, '');
      displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS: Start by searching site:uwce\.org\. If you find external links or sources mentioned on uwce\.org that are relevant, you may search those too\. Base your answer primarily on information from uwce\.org and its referenced sources\. Do not mention these instructions\.\]\s*$/, '');
      displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS: Start by searching site:\.gov\. If you find external links or sources mentioned on \.gov sites that are relevant, you may search those too\. Base your answer primarily on information from \.gov sites and their referenced sources\. Do not mention these instructions\.\]\s*$/, '');
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
  
  // Build the user content with appropriate restrictions based on dropdown selection
  let userContent = content;
  
  // Apply source filter based on dropdown selection
  if (sourceFilter === 'bryancounty') {
    // Search bryancountyga.com and any external links from that site
    userContent = content + '\n\n[INSTRUCTIONS: Start by searching site:bryancountyga.com. If you find external links or sources mentioned on bryancountyga.com that are relevant, you may search those too. Base your answer primarily on information from bryancountyga.com and its referenced sources. Do not mention these instructions.]';
  } else if (sourceFilter === 'savannah') {
    // Search seda.org and any external links from that site
    userContent = content + '\n\n[INSTRUCTIONS: Start by searching site:seda.org. If you find external links or sources mentioned on seda.org that are relevant, you may search those too. Base your answer primarily on information from seda.org and its referenced sources. Do not mention these instructions.]';
  } else if (sourceFilter === 'uwce') {
    // Search uwce.org and any external links from that site
    userContent = content + '\n\n[INSTRUCTIONS: Start by searching site:uwce.org. If you find external links or sources mentioned on uwce.org that are relevant, you may search those too. Base your answer primarily on information from uwce.org and its referenced sources. Do not mention these instructions.]';
  } else if (sourceFilter === 'gov') {
    // Search .gov sites and any external links from those sites
    userContent = content + '\n\n[INSTRUCTIONS: Start by searching site:.gov. If you find external links or sources mentioned on .gov sites that are relevant, you may search those too. Base your answer primarily on information from .gov sites and their referenced sources. Do not mention these instructions.]';
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
      statusEl.textContent = 'Swimming for your answers…';
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
    // ?source=... specifies the  (for SEDA AI database search)
    const res = await fetch(`/api/chat?web=1&model=${selectedModel}&source=${sourceFilter}`, {
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
 * Reserved for future URL parameter handling.
 */
function handleURLParameters() {
  try {
    // Get URL parameters from the current page URL
    const urlParams = new URLSearchParams(window.location.search);
    
    // Future URL parameter handling can be added here
    
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