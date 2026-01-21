# 🔗 GitHub Webhook Configuration Guide

This guide will help you configure GitHub webhooks to automatically analyze commits using your static analysis framework.

## 🚀 Step 1: Set Up Environment Variables

Create a `.env` file in your project root:

```bash
# Copy example file
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_WEBHOOK_SECRET=your_chosen_webhook_secret_here

# Email Configuration (Gmail recommended)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password_here
FROM_EMAIL=your_email@gmail.com

# Optional: Anthropic API for AI explanations
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

### 🔑 Getting Required Credentials:

#### GitHub Personal Access Token:
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`, `read:user`
4. Copy the token (starts with `ghp_`)

#### Gmail App Password:
1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this password (not your regular Gmail password)

#### Webhook Secret:
- Choose any random string (e.g., `my-webhook-secret-123`)
- This will be used to verify webhook authenticity

## 🚀 Step 2: Start the Webhook Server

Load your environment variables and start the server:

```bash
# Load environment variables
source .env

# Or export them manually:
export GITHUB_TOKEN="your_token_here"
export GITHUB_WEBHOOK_SECRET="your_secret_here"
export EMAIL_USER="your_email@gmail.com"
export EMAIL_PASSWORD="your_app_password"
export FROM_EMAIL="your_email@gmail.com"

# Start the webhook handler
python3 simple_webhook_handler.py
```

You should see:
```
🚀 Starting GitHub webhook handler...
📡 Webhook endpoint: http://localhost:5000/webhook
🔍 Health check: http://localhost:5000/health
```

## 🌐 Step 3: Make Your Server Accessible (Choose One Option)

### Option A: Using ngrok (Recommended for Testing)

1. **Install ngrok**: Download from https://ngrok.com/download
2. **Start tunnel**:
   ```bash
   ngrok http 5000
   ```
3. **Copy the public URL** (e.g., `https://abc123.ngrok.io`)
4. **Your webhook URL will be**: `https://abc123.ngrok.io/webhook`

### Option B: Deploy to Cloud (Production)

Deploy to platforms like:
- **Heroku**: `git push heroku main`
- **DigitalOcean App Platform**
- **AWS Lambda** with API Gateway
- **Google Cloud Run**

### Option C: Local Development with Port Forwarding

If you have a public IP, forward port 5000:
```bash
# Your webhook URL: http://your-public-ip:5000/webhook
```

## 🔧 Step 4: Configure GitHub Repository Webhook

### In Your GitHub Repository:

1. **Go to Settings** → **Webhooks** → **Add webhook**

2. **Fill in the webhook details**:
   ```
   Payload URL: https://your-ngrok-url.ngrok.io/webhook
   Content type: application/json
   Secret: your_chosen_webhook_secret_here
   ```

3. **Select events to trigger**:
   - ✅ **Push events** (for commit analysis)
   - ✅ **Pull request events** (for PR analysis)
   - ❌ Uncheck "Just the push event" if selected

4. **Ensure webhook is Active**: ✅ Active

5. **Click "Add webhook"**

### ✅ Verification:

GitHub will send a ping event. You should see:
- ✅ Green checkmark next to your webhook
- Recent deliveries in the webhook page
- Logs in your terminal showing the ping event

## 🧪 Step 5: Test the Webhook

### Make a Test Commit:

1. **Create a test file** with some violations:
   ```bash
   cd your-repository
   cat > test_violations.c << 'EOF'
   #include <stdio.h>
   
   static int unused_var = 42;  // MISRA violation
   
   int main() {
       char buf[10];
       gets(buf);  // CERT violation
       return 0;
   }
   EOF
   ```

2. **Commit and push**:
   ```bash
   git add test_violations.c
   git commit -m "Test commit for static analysis"
   git push origin main
   ```

### Expected Results:

1. **In your terminal**: You should see analysis logs
2. **In GitHub**: Check webhook deliveries for success (200 response)
3. **In your email**: You should receive an analysis report

## 📧 Step 6: Verify Email Reports

Check your email for a report like:

```
Subject: ⚠️ Code Issues - your-repo/main (abc12345) - 2 violations

🚨 Critical Issues Found
Repository: your-username/your-repository
Commit: abc12345
Author: Your Name
Message: Test commit for static analysis

📊 Summary
Total Violations: 2
Errors: 2 | Warnings: 0 | Info: 0

🔍 Violations Found
MISRA-C-2012-8.7 - Unused static variable
CERT-C-EXP34-C - Dangerous function usage
```

## 🔧 Step 7: Configure Multiple Repositories

To monitor multiple repositories, add the same webhook configuration to each repository:

1. **Use the same webhook URL** for all repositories
2. **Use the same secret** for consistency
3. **The server will handle multiple repositories automatically**

## 🐛 Troubleshooting

### Webhook Not Triggering:
```bash
# Check webhook deliveries in GitHub
# Look for error messages (400, 500 status codes)

# Test webhook endpoint manually:
curl -X GET http://localhost:5000/health
```

### Analysis Failing:
```bash
# Check if static analyzer works locally:
python3 -m static_analyzer.cli analyze --path samples/

# Check clang installation:
clang --version
```

### Email Not Sending:
```bash
# Test email configuration:
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('$EMAIL_USER', '$EMAIL_PASSWORD')
print('Email configuration OK')
server.quit()
"
```

### Common Issues:

1. **"Invalid signature" error**: Check `GITHUB_WEBHOOK_SECRET` matches
2. **"Connection refused"**: Ensure server is running and accessible
3. **"Analysis failed"**: Check static analyzer dependencies (clang, libclang)
4. **"Email failed"**: Verify Gmail app password, not regular password

## 📊 Monitoring

### Check Webhook Status:
```bash
# Health check
curl http://localhost:5000/health

# Should return:
{
  "status": "healthy",
  "service": "static-analysis-webhook", 
  "configured": {
    "github_token": true,
    "webhook_secret": true,
    "email": true
  }
}
```

### View Logs:
- **Server logs**: Check terminal where webhook handler is running
- **GitHub webhook logs**: Repository Settings → Webhooks → Recent Deliveries
- **Email logs**: Check sent items in your email client

## 🚀 Production Deployment

For production use:

1. **Use HTTPS**: Deploy with SSL certificate
2. **Use environment secrets**: Don't commit credentials
3. **Add monitoring**: Health checks, error tracking
4. **Scale appropriately**: Multiple server instances if needed
5. **Add rate limiting**: Prevent abuse

### Example Production Setup:

```bash
# Use systemd service or Docker
docker run -d \
  -p 5000:5000 \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e GITHUB_WEBHOOK_SECRET="$GITHUB_WEBHOOK_SECRET" \
  -e EMAIL_USER="$EMAIL_USER" \
  -e EMAIL_PASSWORD="$EMAIL_PASSWORD" \
  your-webhook-server
```

## ✅ Success Checklist

- [ ] Environment variables configured
- [ ] Webhook server running
- [ ] Server accessible from GitHub (ngrok or public URL)
- [ ] GitHub webhook configured with correct URL and secret
- [ ] Test commit triggers analysis
- [ ] Email report received
- [ ] Webhook shows green checkmark in GitHub

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs** in your terminal
2. **Verify webhook deliveries** in GitHub
3. **Test components individually** (analyzer, email, webhook)
4. **Review the troubleshooting section** above

---

**🎉 Congratulations!** Once set up, every commit to your repository will be automatically analyzed for MISRA and CERT violations, with reports emailed to the commit author!
