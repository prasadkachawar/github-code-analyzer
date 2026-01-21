# 🎯 RENDER.COM STEP-BY-STEP VISUAL GUIDE

## 📍 **Exact Steps to Find Render Settings**

### **Step 1: Go to Render.com**
1. Open your browser
2. Visit: **https://render.com**
3. Click **"Get Started for Free"** or **"Sign In"**

### **Step 2: Sign Up/Sign In**
1. Click **"Sign in with GitHub"** (recommended)
2. Authorize Render to access your GitHub account

### **Step 3: Create New Service**
Once you're logged in, you'll see the Render dashboard:

1. Look for a **blue button** that says **"New +"** (top right corner)
2. Click **"New +"** 
3. From dropdown menu, select **"Web Service"**

### **Step 4: Connect Repository**
You'll see a page titled **"Create a new Web Service"**:

1. Look for section: **"Build and deploy from a Git repository"**
2. Click **"Connect"** next to GitHub
3. Find and select: **`prasadkachawar/github-code-analyzer`**
4. Click **"Connect"** button next to your repository

### **Step 5: Configure Settings** ⭐ **THIS IS WHERE YOU ENTER THE SETTINGS**

You'll now see a form with these fields. **Copy these EXACT values**:

```
┌─────────────────────────────────────────────────────┐
│  🔧 RENDER.COM CONFIGURATION FORM                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ✏️  Name:                                          │
│      [github-code-analyzer                      ]   │
│                                                     │
│  🌿  Branch:                                        │
│      [main                              ▼]          │
│                                                     │
│  🐍  Runtime:                                       │
│      [Python 3                         ▼]          │
│                                                     │
│  🔨  Build Command:                                 │
│      [pip install -r requirements_minimal.txt   ]  │
│                                                     │
│  🚀  Start Command:                                 │
│      [gunicorn app_simple:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1]
│                                                     │
│  💰  Plan:                                          │
│      [Free                              ▼]          │
│                                                     │
│      [Create Web Service]                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 📋 **COPY-PASTE VALUES** (Select and copy these exactly):

### Name:
```
github-code-analyzer
```

### Branch:
```
main
```

### Runtime:
```
Python 3
```

### Build Command:
```
pip install -r requirements_minimal.txt
```

### Start Command:
```
gunicorn app_simple:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
```

## 🔍 **Can't Find These Fields? Here's What to Look For:**

### **If you see different options:**

1. **"Dockerfile"** option - **DON'T choose this**
2. **"Build from source"** - **Choose this one**
3. **"Python"** in runtime dropdown - **Choose this**

### **Field Names Might Appear As:**
- **Name** = "Service Name" or "App Name"
- **Branch** = "Branch" or "Git Branch" 
- **Runtime** = "Environment" or "Runtime Environment"
- **Build Command** = "Build Command" or "Install Command"
- **Start Command** = "Start Command" or "Run Command"

## 🚨 **Common Issues & Solutions:**

### **Issue 1: "Can't find my repository"**
- Make sure you've pushed code to GitHub
- Check repository is public or Render has access
- Repository name should be exactly: `github-code-analyzer`

### **Issue 2: "Runtime dropdown doesn't show Python 3"**
- Look for "Python" (any version)
- Try "Python 3.11" or "Python 3.x"
- Avoid "Docker" option

### **Issue 3: "Build Command field is missing"**
- Look for "Custom Build Command"
- Or "Override Build Command" 
- Make sure you're NOT using Docker deployment

## 📱 **Alternative: Try Railway.app (Easier)**

If Render.com is confusing, try Railway instead:

1. **Go to**: https://railway.app
2. **Sign in** with GitHub  
3. **Click**: "Deploy from GitHub repo"
4. **Select**: `prasadkachawar/github-code-analyzer`
5. **That's it!** Railway auto-deploys

## 🆘 **Still Can't Find Settings?**

### **Take a Screenshot and Look For:**
- Blue "New +" button (top right)
- "Web Service" option in dropdown
- Form with "Name", "Branch", "Runtime" fields
- "Build Command" and "Start Command" text boxes

### **If All Else Fails:**
1. Try Railway.app instead (much simpler)
2. Or try Heroku (more complex but well-documented)
3. Or share a screenshot and I'll guide you step-by-step

## ✅ **Success Indicators:**
- You should see a form asking for Name, Branch, Runtime
- Build Command and Start Command should be text input boxes
- There should be a "Create Web Service" button at the bottom

**Once you find the form, just copy-paste the values above and click "Create Web Service"!** 🚀

---

**Your live URL will be**: `https://github-code-analyzer-XXXX.onrender.com`
