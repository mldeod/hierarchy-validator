# GitHub Deployment Guide

## Step-by-Step Instructions

### 1. Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click "New Repository" (+ icon top right)
3. Repository name: `hierarchy-validator`
4. Description: "Professional FP&A tool for Excel hierarchy validation and conversion"
5. Choose: **Public** or **Private** (your choice)
6. **DO NOT** initialize with README (we already have one)
7. Click "Create repository"

### 2. Push Code to GitHub

```bash
# Navigate to your project directory
cd /path/to/vena_analytics_accelerator

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Tree Converter v1.0"

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/hierarchy-validator.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Deploy to Streamlit Cloud

#### Option A: Direct from GitHub

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - Repository: `YOUR_USERNAME/hierarchy-validator`
   - Branch: `main`
   - Main file path: `main.py`
5. Click "Deploy!"
6. Wait 2-3 minutes for deployment
7. Your app is live! 🎉

#### Option B: Manual Configuration

If you need custom settings:

1. Create `.streamlit/config.toml` in your repository:

```toml
[theme]
primaryColor = "#34c759"
backgroundColor = "#f5f5f7"
secondaryBackgroundColor = "#ffffff"
textColor = "#1d1d1f"
font = "sans serif"

[server]
maxUploadSize = 200
enableXsrfProtection = false
```

2. Push the changes:
```bash
git add .streamlit/config.toml
git commit -m "Add Streamlit configuration"
git push
```

3. Redeploy on Streamlit Cloud

### 4. Share Your App

Your app will be available at:
```
https://YOUR_USERNAME-hierarchy-validator-main-xxxxx.streamlit.app
```

Share this URL with clients, colleagues, or on your website!

---

## GitHub Best Practices

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/new-validation

# Make changes, commit
git add .
git commit -m "Add new validation rule"

# Push feature branch
git push origin feature/new-validation

# Create Pull Request on GitHub
# Merge after review
```

### Useful Git Commands

```bash
# Check status
git status

# See changes
git diff

# View commit history
git log --oneline

# Create tag for release
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0
```

---

## Updating the Live App

When you push changes to `main` branch, Streamlit Cloud automatically redeploys:

```bash
# Make changes locally
# Test with: streamlit run main.py

# Commit and push
git add .
git commit -m "Fix: Improve error messages"
git push

# App automatically updates in 1-2 minutes!
```

---

## Troubleshooting

### Issue: App won't deploy

**Check:**
- `requirements.txt` includes all dependencies
- `main.py` exists in root directory
- No syntax errors (test locally first)

### Issue: File upload fails

**Solution:**
- Streamlit Cloud has 200MB upload limit (already configured)
- Check file size in app

### Issue: Slow performance

**Solution:**
- Streamlit Cloud free tier has resource limits
- Consider upgrading for production use
- Optimize code for caching

---

## Making Repository Private

If you want to keep code private:

1. Go to repository Settings
2. Scroll to "Danger Zone"
3. Click "Change visibility"
4. Select "Private"

**Note:** Streamlit app will still be public even with private repo!

---

## Next Steps

1. ✅ Push to GitHub
2. ✅ Deploy to Streamlit Cloud
3. 📸 Take screenshots for documentation
4. 📢 Share with your client
5. 🎯 Gather feedback
6. 🚀 Iterate and improve

---

**Questions?** Open an issue on GitHub or contact support!
