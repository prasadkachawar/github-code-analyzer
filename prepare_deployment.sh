#!/bin/bash

# Deployment Preparation Script for GitHub Code Analyzer
# This script prepares your project for deployment to free hosting platforms

set -e

echo "🚀 Preparing GitHub Code Analyzer for Deployment"
echo "================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📁 Initializing git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

# Add gitignore if not exists
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}📝 Creating .gitignore file...${NC}"
    cat > .gitignore << 'EOF'
# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Analysis outputs
analysis_reports/
analysis_baselines/
temp_repos/
logs/
*.log
EOF
    echo -e "${GREEN}✅ .gitignore created${NC}"
fi

# Create a simplified README for deployment
echo -e "${YELLOW}📚 Creating deployment README...${NC}"
cat > README_DEPLOYMENT.md << 'EOF'
# 🔍 GitHub Code Analyzer

**Free MISRA C:2012 & CERT C/C++ Static Analysis for GitHub Repositories**

## ✨ Features

- 🆓 **Completely Free** - No signup required
- 🚀 **Instant Analysis** - Just paste your GitHub URL
- 📊 **Detailed Reports** - MISRA and CERT compliance checking
- 🌐 **Web Interface** - Easy-to-use browser interface
- 📱 **Mobile Friendly** - Works on all devices

## 🎯 How to Use

1. **Visit the analyzer**: [Your deployed URL here]
2. **Enter GitHub URL**: Paste any public GitHub repository URL
3. **Get Results**: View detailed code quality analysis
4. **Share**: Help other developers improve their code

## 🛡️ Supported Standards

- **MISRA C:2012** - Automotive industry coding standard
- **CERT C/C++** - Security-focused coding practices
- **Custom Rules** - Extensible rule engine

## 🏗️ Example Repositories to Try

- `https://github.com/curl/curl`
- `https://github.com/git/git`
- `https://github.com/redis/redis`

## 🤝 Contributing

Found a bug or want to contribute? 
- Create an issue on GitHub
- Submit a pull request
- Share feedback

---

**Built with ❤️ for the developer community**
EOF

echo -e "${GREEN}✅ Deployment README created${NC}"

# Add all files to git
echo -e "${YELLOW}📦 Adding files to git...${NC}"
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${GREEN}✅ No changes to commit${NC}"
else
    # Commit changes
    echo -e "${YELLOW}💾 Committing changes...${NC}"
    git commit -m "Prepare for deployment: GitHub Code Analyzer web app

Features:
- Web interface for GitHub repository analysis
- MISRA C:2012 and CERT C/C++ rule checking  
- Real-time analysis with detailed reports
- Mobile-friendly responsive design
- Free hosting ready configuration

Ready for deployment on Render, Railway, Heroku, or Vercel."

    echo -e "${GREEN}✅ Changes committed${NC}"
fi

# Show current status
echo
echo -e "${GREEN}🎉 Deployment preparation complete!${NC}"
echo
echo "📋 Next Steps:"
echo "1. Create GitHub repository (if not already done)"
echo "2. Push code: git push origin main"
echo "3. Deploy to free platform (see DEPLOYMENT_GUIDE.md)"
echo "4. Share your live URL with developers!"
echo
echo "🌐 Recommended deployment platforms:"
echo "   • Render.com (easiest) - https://render.com"
echo "   • Railway.app - https://railway.app" 
echo "   • Heroku - https://heroku.com"
echo "   • Vercel - https://vercel.com"
echo
echo "📚 Full deployment guide: DEPLOYMENT_GUIDE.md"

# Show git status
echo
echo "📊 Git Status:"
git status --porcelain | head -10
