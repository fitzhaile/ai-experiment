# Deploy Sea Cow AI to Render 🦭☁️

This guide will walk you through deploying your Sea Cow AI app to Render's free tier.

---

## 📋 Prerequisites

✅ You already have:
- Flask app (`app.py`)
- `requirements.txt` with all dependencies
- `Procfile` for gunicorn
- `render.yaml` for configuration

✅ You need:
- GitHub account
- Render account (free)
- Your 3 API keys ready

---

## 🚀 Deployment Steps

### **Step 1: Push to GitHub**

If you haven't already, push your code to GitHub:

```bash
cd "/Users/fhaile/Dropbox/Sites/FH Website/ai-experiment"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Add Claude integration and web search"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR-USERNAME/sea-cow-ai.git
git branch -M main
git push -u origin main
```

**⚠️ Important:** Your `.env` file should be in `.gitignore` (it is by default) so your API keys aren't pushed to GitHub!

---

### **Step 2: Create Render Account**

1. Go to: **https://render.com/**
2. Click **"Get Started"** or **"Sign Up"**
3. Sign up with GitHub (easiest option)
4. Authorize Render to access your repositories

---

### **Step 3: Create New Web Service**

1. From Render Dashboard, click **"+ New"** → **"Web Service"**

2. **Connect Repository:**
   - Click **"Connect account"** if needed
   - Find your `sea-cow-ai` repository
   - Click **"Connect"**

3. **Configure Service:**
   ```
   Name: sea-cow-ai (or your choice)
   Region: Oregon (US West) or closest to you
   Branch: main
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

4. **Select Plan:**
   - Choose **"Free"** plan
   - Free tier includes:
     - 750 hours/month (enough for 24/7)
     - Sleeps after 15 min inactivity
     - Wakes up on first request (~30 sec delay)

---

### **Step 4: Add Environment Variables**

This is the most important step! In the Render setup page, scroll to **"Environment Variables"** section:

Click **"Add Environment Variable"** for each:

#### **1. OpenAI API Key**
```
Key:   OPENAI_API_KEY
Value: sk-proj-your-actual-openai-key
```

#### **2. Anthropic API Key**
```
Key:   ANTHROPIC_API_KEY
Value: sk-ant-your-actual-anthropic-key
```

#### **3. Brave Search API Key**
```
Key:   BRAVE_API_KEY
Value: BSA-your-actual-brave-key
```

#### **4. Port (Auto-set)**
Render sets this automatically, but you can add it:
```
Key:   PORT
Value: 10000
```

---

### **Step 5: Deploy!**

1. Click **"Create Web Service"** at the bottom

2. Render will:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Start your app with gunicorn
   - Assign you a URL like: `https://sea-cow-ai.onrender.com`

3. **Watch the build logs** - should take 2-3 minutes:
   ```
   ==> Building...
   ==> Installing dependencies...
   ==> Starting service...
   ==> Your service is live 🎉
   ```

---

## 🌐 Access Your App

Once deployed, your app will be live at:
```
https://sea-cow-ai.onrender.com
```
(Replace `sea-cow-ai` with your actual service name)

---

## 🔧 Post-Deployment

### **Test Everything:**

1. **Test OpenAI (GPT) models:**
   - Select "gpt-4o" 
   - Select "seda.org"
   - Ask: "What economic development programs are available?"

2. **Test Claude models:**
   - Select "Claude 3.5 Sonnet (latest)"
   - Select "bryancountyga.com"
   - Ask: "What services does Bryan County offer?"

3. **Test without data source:**
   - Ask general questions to verify both APIs work

### **Check Logs:**

From Render Dashboard:
- Go to your service
- Click **"Logs"** tab
- Look for:
  ```
  INFO:root:OPENAI_API_KEY detected: sk-proj***
  INFO:root:ANTHROPIC_API_KEY detected: sk-ant***
  INFO:root:BRAVE_API_KEY detected: BSA***
  ```

If you see warnings about missing keys, add them in the **"Environment"** tab.

---

## 🐛 Troubleshooting

### **App Won't Start**

Check build logs for errors:
- Missing dependencies? Update `requirements.txt`
- Python version issues? Render uses Python 3.11 by default
- Port binding? Gunicorn handles this automatically

### **API Keys Not Working**

1. Go to **Environment** tab in Render
2. Verify all 3 keys are set correctly
3. Click **"Manual Deploy"** → **"Deploy latest commit"** to restart

### **App is Slow to Wake Up**

This is normal on the free tier:
- App sleeps after 15 minutes of inactivity
- First request takes ~30 seconds to wake
- Upgrade to paid plan ($7/month) for always-on

### **Build Fails**

Common issues:
```bash
# If you see SSL warnings (safe to ignore)
urllib3 v2 only supports OpenSSL 1.1.1+...

# If anthropic install fails
pip install anthropic==0.39.0

# If requests install fails  
pip install requests==2.32.3
```

---

## 💰 Cost Management

### **Free Tier Limits:**
- ✅ 750 hours/month (enough for 24/7)
- ✅ Unlimited requests while awake
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ 30-second wake time

### **API Usage Costs:**
Remember, Render hosting is free, but API calls cost money:

- **OpenAI:** GPT-4o costs apply per request
- **Anthropic:** Claude costs apply per request  
- **Brave Search:** 2,000 free searches/month, then $5/1K

**Tip:** Monitor usage on each provider's dashboard!

---

## 🔄 Updating Your App

After making code changes locally:

```bash
# Commit changes
git add .
git commit -m "Your update description"

# Push to GitHub
git push origin main
```

Render will **automatically detect** the push and redeploy! 🎉

To disable auto-deploy:
- Go to service **Settings**
- Toggle off **"Auto-Deploy"**
- Deploy manually from dashboard

---

## 🔒 Security Best Practices

✅ **Do:**
- Keep API keys in Render Environment Variables only
- Never commit `.env` to GitHub
- Use `.gitignore` for sensitive files
- Rotate API keys periodically

❌ **Don't:**
- Hard-code API keys in `app.py`
- Share your render.com service URL publicly without rate limiting
- Expose your GitHub repo with keys

---

## 🎉 Success!

Your Sea Cow AI is now live on the internet! 🦭🌊

**Share your app:**
```
https://sea-cow-ai.onrender.com
```

**Show it to your client and watch their reaction!** 😊

---

## 📚 Additional Resources

- **Render Docs:** https://render.com/docs
- **Gunicorn Config:** https://docs.gunicorn.org/
- **Flask Deployment:** https://flask.palletsprojects.com/deploying/

---

## 🆘 Need Help?

If you run into issues:
1. Check Render logs first
2. Verify environment variables are set
3. Test locally with `gunicorn app:app`
4. Check API provider status pages

Happy deploying! 🚀

