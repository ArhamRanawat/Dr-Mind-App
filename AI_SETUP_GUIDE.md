# 🤖 **Real AI Setup Guide for Dr. Mind**

## 🎯 **Get Real AI Responses Instead of Fallback System**

Your app now supports **real AI** from Hugging Face and Cohere! Here's how to set them up:

---

## 🆓 **Option 1: Hugging Face (Completely Free)**

### **Step 1: Create Hugging Face Account**
1. Go to [Hugging Face](https://huggingface.co/)
2. Click **"Sign Up"**
3. Create your account (email + password)

### **Step 2: Get API Token**
1. **Sign in** to your Hugging Face account
2. Click your **profile picture** → **Settings**
3. Go to **"Access Tokens"** in the left sidebar
4. Click **"New token"**
5. **Name:** `DrMind`
6. **Role:** Read
7. Click **"Generate token"**
8. **Copy the token** (starts with `hf_`)

### **Step 3: Add to Environment Variables**
**For Local Development:**
```bash
# Windows (PowerShell)
$env:HF_API_KEY="your_huggingface_token_here"

# Windows (Command Prompt)
set HF_API_KEY=your_huggingface_token_here
```

**For Render Deployment:**
1. Go to your Render dashboard
2. Click your app → **Environment** tab
3. Add environment variable:
   - **Key:** `HF_API_KEY`
   - **Value:** `your_huggingface_token_here`

---

## 🆓 **Option 2: Cohere (Free Tier - 5 requests/minute)**

### **Step 1: Create Cohere Account**
1. Go to [Cohere.ai](https://cohere.ai/)
2. Click **"Get Started"**
3. Sign up with email

### **Step 2: Get API Key**
1. **Sign in** to your Cohere account
2. Go to **"API Keys"** section
3. Click **"Create API Key"**
4. **Name:** `DrMind`
5. Click **"Create"**
6. **Copy the API key**

### **Step 3: Add to Environment Variables**
**For Local Development:**
```bash
# Windows (PowerShell)
$env:COHERE_API_KEY="your_cohere_api_key_here"

# Windows (Command Prompt)
set COHERE_API_KEY=your_cohere_api_key_here
```

**For Render Deployment:**
1. Go to your Render dashboard
2. Click your app → **Environment** tab
3. Add environment variable:
   - **Key:** `COHERE_API_KEY`
   - **Value:** `your_cohere_api_key_here`

---

## 🚀 **How It Works**

### **AI Priority Order:**
1. **Hugging Face** (FREE) - First try
2. **Cohere** (FREE tier) - Second try  
3. **Google AI** (if you have API key) - Third try
4. **Fallback System** - Always works as backup

### **What You'll See:**
```
🤖 Trying Hugging Face AI (FREE)...
🤖 Hugging Face response received!
```

Instead of:
```
🤖 Hugging Face API requires setup - using fallback system...
```

---

## 🔧 **Testing Your Setup**

### **Step 1: Set Environment Variables**
```bash
# Set both API keys
$env:HF_API_KEY="hf_your_token_here"
$env:COHERE_API_KEY="your_cohere_key_here"
```

### **Step 2: Run Your App**
```bash
python DrMind_OpenAI.py
```

### **Step 3: Test AI Response**
1. Open your app in browser
2. Enter a mood and journal entry
3. Submit
4. Check the terminal for AI service messages

---

## 📊 **Free Tier Limits**

### **Hugging Face:**
- ✅ **Completely free** for personal use
- ✅ **No rate limits** for basic usage
- ✅ **No credit card required**

### **Cohere:**
- ✅ **Free tier:** 5 requests per minute
- ✅ **No credit card required**
- ✅ **Upgrade anytime** for more requests

### **Google AI:**
- ✅ **Free tier:** 1,000 requests per month
- ⚠️ **Requires credit card** for verification

---

## 🎉 **Benefits of Real AI**

### **vs Fallback System:**
- **More creative responses**
- **Better context understanding**
- **More varied suggestions**
- **Real AI intelligence**

### **vs Google AI Only:**
- **Multiple AI services** = better reliability
- **Free options** = no cost
- **No quota limits** (Hugging Face)
- **Always works** (fallback backup)

---

## 🆘 **Troubleshooting**

### **"API failed" Messages:**
1. **Check your API keys** are correct
2. **Verify environment variables** are set
3. **Check internet connection**
4. **Try the other AI service**

### **"Rate limit exceeded":**
- **Cohere:** Wait 1 minute, try again
- **Google AI:** Wait for quota reset (monthly)

### **Still using fallback:**
- **Check terminal messages** for specific errors
- **Verify API keys** are properly set
- **Restart the app** after setting environment variables

---

## 🎯 **Next Steps**

1. **Get your API keys** (Hugging Face + Cohere)
2. **Set environment variables**
3. **Test the app**
4. **Deploy to Render** with environment variables
5. **Enjoy real AI responses!**

Your Dr. Mind app will now provide **genuine AI-powered** mental health support! 🧠✨ 
