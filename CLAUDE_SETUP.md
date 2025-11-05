# Claude Integration Setup Guide 🦭

This guide will help you set up Claude models with Brave Search integration.

## 📋 Prerequisites

You'll need three API keys:

1. **OpenAI API Key** (you already have this)
2. **Anthropic API Key** (for Claude models)
3. **Brave Search API Key** (for Claude web search)

---

## 🔑 Getting API Keys

### 1. Anthropic API Key (Claude)

1. Visit: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy your key (starts with `sk-ant-`)

**Pricing:**
- $5 free credit for new accounts
- Claude 3.5 Sonnet: $3 per million input tokens, $15 per million output tokens

### 2. Brave Search API Key

1. Visit: https://brave.com/search/api/
2. Sign up for a free account
3. Go to your dashboard
4. Get your API key (starts with `BSA`)

**Pricing:**
- **FREE tier**: 2,000 queries per month
- Perfect for testing and personal use!

---

## ⚙️ Installation

### Step 1: Install Dependencies

```bash
pip install anthropic requests
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Step 2: Add API Keys to .env

Add these lines to your `.env` file:

```bash
# Anthropic API Key (for Claude models)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Brave Search API Key (for Claude web search)
BRAVE_API_KEY=BSA-your-key-here
```

Your `.env` file should now look like:

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
BRAVE_API_KEY=BSAxxxxxxxxxxxxx
PORT=8080
FLASK_DEBUG=1
```

### Step 3: Restart the Server

1. Stop the current server (Ctrl+C)
2. Restart:

```bash
PORT=8080 FLASK_DEBUG=1 python app.py
```

---

## 🎯 Using Claude Models

1. Open http://localhost:8080/ in your browser
2. In the **Chat Model** dropdown, select a Claude model:
   - **Claude 3.5 Sonnet (latest)** - Best overall, recommended
   - **Claude 3 Opus** - Most capable, slower
   - **Claude 3 Sonnet** - Balanced
   - **Claude 3 Haiku** - Fastest, good for simple tasks

3. Select a data source (bryancountyga.com, seda.org, or .gov)

4. Ask your question!

### How Claude Web Search Works

When you select a Claude model and a data source:

1. Your query is sent to **Brave Search API**
2. Top 10 web results are retrieved
3. Results are filtered by your data source (e.g., site:seda.org)
4. **Claude analyzes the search results** with its superior reasoning
5. Claude provides a well-structured answer with citations

---

## 🆚 Claude vs GPT

### When to Use Claude:
- ✅ Complex reasoning tasks
- ✅ Coding and technical analysis
- ✅ Long context (200K tokens)
- ✅ Detailed, thorough responses
- ✅ Better instruction following

### When to Use GPT:
- ✅ OpenAI's native web search (Responses API)
- ✅ Faster for simple queries
- ✅ More conversational tone
- ✅ Better for creative tasks

---

## 🔍 Testing

Try these test queries with Claude 3.5 Sonnet:

1. **Without data source filter:**
   "Explain quantum entanglement"

2. **With seda.org:**
   "What economic development programs are available?"

3. **With bryancountyga.com:**
   "What are the property tax rates?"

You should see Claude analyze Brave Search results and provide detailed answers with source citations!

---

## 🐛 Troubleshooting

### "Claude models not available" error
- Install anthropic: `pip install anthropic`
- Add ANTHROPIC_API_KEY to .env
- Restart the server

### "Brave Search error" in logs
- Check that BRAVE_API_KEY is in .env
- Verify your key at https://brave.com/search/api/
- Check you haven't exceeded free tier (2,000 queries/month)

### Claude responses are slow
- This is normal! Claude takes 10-30 seconds for complex queries
- Claude 3 Haiku is faster if you need speed
- Consider the quality/speed tradeoff

---

## 💰 Cost Comparison

**Example:** 1000 questions with ~500 token responses

| Model | Input Cost | Output Cost | Total |
|-------|-----------|-------------|-------|
| GPT-4o | $2.50 | $7.50 | $10.00 |
| Claude 3.5 Sonnet | $1.50 | $7.50 | $9.00 |
| Claude 3 Haiku | $0.13 | $0.63 | $0.76 |
| Brave Search (free) | $0.00 | - | $0.00 |

**Note:** Brave's free tier (2,000 queries/month) is plenty for personal use!

---

## 🎉 You're All Set!

You now have:
- ✅ OpenAI GPT models with native web search
- ✅ Claude models with Brave Search integration
- ✅ Source filtering (bryancountyga.com, seda.org, .gov)
- ✅ The best of both AI worlds! 🦭

Enjoy your enhanced Sea Cow AI! 🌊

