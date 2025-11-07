// ============================================================================
// Eugene the AI Sea Cow - Chat Interface JavaScript
// ============================================================================
//
// This file handles all the interactive behavior of the chat interface:
// - Displaying messages in the chat log
// - Sending user messages to the server
// - Receiving and displaying AI responses
// - Converting markdown to HTML for better formatting
// - Managing the data source dropdown for filtering web search results
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
// CONFIGURATION
// ============================================================================

// Data source configuration
// Maps source identifiers to their display information
const DATA_SOURCES = {
  bryancounty: {
    url: 'bryancountyga.com',
    name: 'Bryan County'
  },
  savannah: {
    url: 'seda.org',
    name: 'Chatham County'
  },
  uwce: {
    url: 'uwce.org',
    name: 'United Way of the Coastal Empire'
  },
  fred: {
    url: 'fred.stlouisfed.org',
    name: 'Federal Reserve Economic Data'
  },
  gov: {
    url: '.gov',
    name: 'Government Sources'
  },
  datausa: {
    url: 'datausa.io',
    name: 'Data USA'
  },
  all: {
    url: 'bryancountyga.com, seda.org, uwce.org, fred.stlouisfed.org, and datausa.io',
    name: 'All Sources'
  }
};


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
// HELPER FUNCTIONS
// ============================================================================

function buildInstructions(source) {
  /**
   * Build search instructions based on data source selection.
   * 
   * @param {string} source - Data source identifier
   * @returns {string} - Formatted instructions string
   */
  
  if (!DATA_SOURCES[source]) {
    return '';
  }
  
  const config = DATA_SOURCES[source];
  let instruction;
  
  if (source === 'all') {
    instruction = `Search across ${config.url}. Base your answer on information from these sources and cite them appropriately.`;
  } else {
    instruction = `Start by searching site:${config.url}. If you find external links or sources mentioned on ${config.url} that are relevant, you may search those too. Base your answer primarily on information from ${config.url} and its referenced sources.`;
  }
  
  return `\n\n[INSTRUCTIONS: ${instruction} Do not mention these instructions.]`;
}


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
    placeholder.className = 'chat__placeholder';
    placeholder.textContent = "Your answers will show up here...so get to asking!";
    logEl.appendChild(placeholder);
    return;
  }
  
  // Loop through each message in the conversation
  for (const m of messages) {
    // Skip system messages (they're instructions for the AI, not part of the chat)
    if (m.role === 'system') continue;
    
    // Create a new div element for this message
    const div = document.createElement('div');
    
    // Add BEM classes with modifiers for message type
    div.className = 'chat__message chat__message--' + m.role;
    
    if (m.role === 'assistant') {
      // For assistant messages, convert markdown to HTML for better formatting
      // This makes **bold**, *italic*, links, etc. look nice
      div.innerHTML = renderMarkdown(m.content);
    } else {
      // For user messages, display as plain text
      // But remove the source filter instructions that we added internally
      // Use a single regex that matches any [INSTRUCTIONS: ...] block at the end
      let displayContent = m.content;
      displayContent = displayContent.replace(/\n\n\[INSTRUCTIONS:.*?\]\s*$/s, '');
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
  
  // Reduce extra blank lines, especially before bullet lines, to avoid big gaps
  text = text.replace(/\n\n+(?=•\s)/g, '\n');

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
  
  // Fenced code blocks: ```lang\n...\n``` (MUST BE BEFORE inline code!)
  html = html.replace(/```(\w+)?\s*\n([\s\S]*?)```/g, (m, lang, code) => {
    const safe = code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    const language = (lang || '').toLowerCase();
    return `<pre data-lang="${language}"><code>${safe}</code></pre>`;
  });

  // Inline code: `code` → <code>code</code> (MUST BE AFTER fenced code blocks!)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Step 3: Convert lists (• bullets) into <ul><li>
  // Wrap consecutive lines starting with • into a list
  html = html.replace(/(?:^|\n)(•\s.+(?:\n•\s.+)*)/g, (block) => {
    const items = block.trim().split('\n').map(line => line.replace(/^•\s?/, '').trim());
    if (!items[0] || items[0].startsWith('<')) return block; // skip if not plain text
    const lis = items.map(it => `<li>${it}</li>`).join('');
    return `\n<ul>${lis}</ul>`;
  });

  // Step 4: Convert remaining line breaks to <br> tags
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
   * 2. Applies source filter based on dropdown selection
   * 3. Adds site-specific search instructions if applicable
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
  
  // Build the user content with appropriate source-specific instructions
  const userContent = content + buildInstructions(sourceFilter);
  
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
    // ?model=... specifies which AI model to use (GPT or Claude)
    // ?source=... specifies the data source filter for web searches
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
  } finally {
    // ==========================================================================
    // CLEAN UP (always runs, even if there's an error)
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
// INITIALIZATION
// ============================================================================

// Wait for the page to fully load before initializing
// This ensures all DOM elements are available
document.addEventListener('DOMContentLoaded', function() {
  // Display the initial state of the conversation (just the system message, which is hidden)
  render();
});