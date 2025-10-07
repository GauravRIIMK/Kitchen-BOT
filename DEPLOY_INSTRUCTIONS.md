# 🚀 Quick Deployment Instructions

## 1. Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/kitchen-reporter-bot.git
git push -u origin main
```

## 2. Deploy to Railway.app
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Add environment variables from .env.template

## 3. Verify Deployment
- Check Railway logs for: "✅ Cloud scheduler started"
- Bot will run at: 00:01, 07:00, 08:30 IST

## 4. Test
- Wait for next scheduled time or use /demo commands in Slack
