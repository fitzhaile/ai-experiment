# 🚀 Render Deployment Checklist

Quick checklist to deploy Sea Cow AI to Render.

---

## ✅ Pre-Deployment Checklist

### **Files Ready:**
- [x] `app.py` - Main Flask application
- [x] `requirements.txt` - All dependencies (Flask, OpenAI, Anthropic, Requests, etc.)
- [x] `Procfile` - Gunicorn configuration
- [x] `render.yaml` - Render service configuration
- [x] `.gitignore` - Prevents committing `.env` and sensitive files

### **API Keys Ready:**
- [ ] OpenAI API Key (`sk-proj-...`)
- [ ] Anthropic API Key (`sk-ant-...`)
- [ ] Brave Search API Key (`BSA...`)

### **GitHub Ready:**
- [ ] Code pushed to GitHub repository
- [ ] Repository is accessible (public or connected to Render)
- [ ] `.env` file is NOT in the repository (check!)

---

## 🎯 Deployment Steps

### **1. Connect to Render**
- [ ] Create account at https://render.com/
- [ ] Sign in with GitHub
- [ ] Authorize Render to access repositories

### **2. Create Web Service**
- [ ] Click "+ New" → "Web Service"
- [ ] Select your GitHub repository
- [ ] Name: `sea-cow-ai` (or your choice)
- [ ] Region: Oregon (US West) or nearest
- [ ] Branch: `main`
- [ ] Runtime: Python 3
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `gunicorn app:app`
- [ ] Plan: Free

### **3. Add Environment Variables**
Go to "Environment Variables" section and add:

- [ ] `OPENAI_API_KEY` = `sk-proj-your-key`
- [ ] `ANTHROPIC_API_KEY` = `sk-ant-your-key`
- [ ] `BRAVE_API_KEY` = `BSA-your-key`
- [ ] `PORT` = `10000` (optional, auto-set)

### **4. Deploy**
- [ ] Click "Create Web Service"
- [ ] Wait for build to complete (2-3 minutes)
- [ ] Check logs for successful startup
- [ ] Note your app URL: `https://YOUR-SERVICE.onrender.com`

---

## ✅ Post-Deployment Testing

### **Test GPT Models:**
- [ ] Select "gpt-4o" model
- [ ] Select "seda.org" data source
- [ ] Ask: "What are the average wages in Chatham County?"
- [ ] Verify answer includes search results

### **Test Claude Models:**
- [ ] Select "Claude 3.5 Sonnet (latest)" model
- [ ] Select "bryancountyga.com" data source
- [ ] Ask: "What services does Bryan County provide?"
- [ ] Verify Brave Search integration works

### **Test General Chat:**
- [ ] Select any model
- [ ] No data source filter
- [ ] Ask general knowledge question
- [ ] Verify response is coherent

### **Check Logs:**
- [ ] Go to Render Dashboard → Logs tab
- [ ] Verify all 3 API keys detected:
  ```
  INFO:root:OPENAI_API_KEY detected: sk-proj***
  INFO:root:ANTHROPIC_API_KEY detected: sk-ant***
  INFO:root:BRAVE_API_KEY detected: BSA***
  ```

---

## 🎨 Optional: Custom Domain

If you want a custom domain instead of `.onrender.com`:

- [ ] Go to Settings → Custom Domain
- [ ] Add your domain (e.g., `seacow-ai.yourdomain.com`)
- [ ] Update DNS records at your domain provider
- [ ] Wait for SSL certificate (automatic)

---

## 🔄 Future Updates

To update your deployed app:

```bash
# Make changes locally
git add .
git commit -m "Description of changes"
git push origin main
```

Render will auto-deploy! 🎉

**Or manually deploy:**
- [ ] Go to Render Dashboard
- [ ] Click "Manual Deploy" → "Deploy latest commit"

---

## 📊 Monitoring

### **Check regularly:**
- [ ] Render Dashboard - Service status
- [ ] OpenAI Dashboard - Usage and costs
- [ ] Anthropic Console - Usage and costs  
- [ ] Brave API Dashboard - Query count (2,000/month free limit)

### **Set up alerts (optional):**
- [ ] OpenAI - Set usage alerts
- [ ] Anthropic - Monitor credit balance
- [ ] Brave - Check monthly query usage

---

## 🐛 Common Issues

**Build fails:**
- Check `requirements.txt` has all dependencies
- Check Python version compatibility
- Review build logs

**App won't start:**
- Verify environment variables are set
- Check logs for errors
- Test locally: `gunicorn app:app`

**APIs not working:**
- Verify keys are correct in Render Environment tab
- Check API provider dashboards for issues
- Review app logs for error messages

**App is slow:**
- Free tier sleeps after 15 min inactivity
- First request after sleep takes ~30 sec
- Upgrade to paid plan for always-on

---

## 📧 Share Your App

Once deployed and tested:

**Your live URL:**
```
https://YOUR-SERVICE-NAME.onrender.com
```

Share with your client and enjoy! 🦭🌊

---

## 🎉 Done!

- [ ] App is live on Render
- [ ] All features tested and working
- [ ] Client demo scheduled
- [ ] Usage monitoring set up

**Congratulations! Your Sea Cow AI is swimming in the cloud!** 🦭☁️

