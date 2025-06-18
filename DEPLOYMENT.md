# 🚀 Deployment Guide - Iron & Steel Business

This guide will help you deploy your application to the cloud for free!

## 📋 Prerequisites
- GitHub account: **ashish7475**
- Render.com account (free)

---

## 🔧 Backend Deployment (Render.com)

### Step 1: Prepare Your Code
1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/ashish7475/iron-steel-business.git
   git push -u origin main
   ```

### Step 2: Deploy on Render.com
1. **Go to [Render.com](https://render.com)** and sign up/login
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**: `ashish7475/iron-steel-business`
4. **Configure the service:**
   - **Name**: `iron-steel-business-api`
   - **Environment**: `Python 3`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`

5. **Add Environment Variables:**
   - `SECRET_KEY`: (auto-generated)
   - `JWT_SECRET_KEY`: (auto-generated)

6. **Click "Create Web Service"**

### Step 3: Get Your Backend URL
- Your API will be available at: `https://iron-steel-business-api.onrender.com`
- Note this URL for frontend configuration

---

## 🌐 Frontend Deployment (GitHub Pages)

### Step 1: Update API URL
1. **Edit `frontend/script.js`:**
   ```javascript
   // Change this line:
   const API_BASE_URL = 'https://iron-steel-business-api.onrender.com/api';
   ```

### Step 2: Deploy to GitHub Pages
1. **Create a new repository for frontend:**
   - Go to GitHub and create: `ashish7475/iron-steel-frontend`

2. **Push frontend files to GitHub:**
   ```bash
   cd frontend
   git init
   git add .
   git commit -m "Frontend deployment"
   git remote add origin https://github.com/ashish7475/iron-steel-frontend.git
   git push -u origin main
   ```

3. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)
   - Click Save

4. **Your frontend will be available at:**
   `https://ashish7475.github.io/iron-steel-frontend`

---

## 🔗 Connect Frontend to Backend

### Update API URL in Frontend
1. **Edit `frontend/script.js`:**
   ```javascript
   // Replace localhost with your Render.com URL
   const API_BASE_URL = 'https://iron-steel-business-api.onrender.com/api';
   ```

2. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "Update API URL for production"
   git push
   ```

---

## ✅ Deployment Checklist

### Backend (Render.com)
- [ ] Code pushed to GitHub: `ashish7475/iron-steel-business`
- [ ] Render.com service created: `iron-steel-business-api`
- [ ] Environment variables set
- [ ] Service deployed successfully
- [ ] API health check passes: `https://iron-steel-business-api.onrender.com/api/health`

### Frontend (GitHub Pages)
- [ ] API URL updated in script.js
- [ ] Code pushed to GitHub: `ashish7475/iron-steel-frontend`
- [ ] GitHub Pages enabled
- [ ] Frontend accessible at: `https://ashish7475.github.io/iron-steel-frontend`

### Testing
- [ ] Login works with admin/admin123
- [ ] Can create receipts
- [ ] Can view dashboard
- [ ] Can export data
- [ ] Print receipts works

---

## 🔧 Troubleshooting

### Backend Issues
- **Build fails**: Check build logs in Render.com dashboard
- **Database errors**: Ensure instance folder is writable
- **CORS errors**: Verify CORS is enabled in Flask app

### Frontend Issues
- **API calls fail**: Check API URL in script.js
- **Page not loading**: Verify GitHub Pages is enabled
- **Login issues**: Check backend is running

### Common Solutions
1. **Clear browser cache** after deployment
2. **Check browser console** for JavaScript errors
3. **Verify API endpoints** are accessible
4. **Test with Postman** or similar tool

---

## 📞 Support

If you encounter issues:
1. Check Render.com logs
2. Check GitHub Pages settings
3. Verify all URLs are correct
4. Test API endpoints individually

---

## 🎉 Success!

Once deployed, your application will be accessible from anywhere in the world!

**Frontend**: `https://ashish7475.github.io/iron-steel-frontend`  
**Backend**: `https://iron-steel-business-api.onrender.com`

**Default Login**: admin / admin123

---

## 🚀 Quick Commands

### Backend Repository:
```bash
git remote add origin https://github.com/ashish7475/iron-steel-business.git
git push -u origin main
```

### Frontend Repository:
```bash
cd frontend
git remote add origin https://github.com/ashish7475/iron-steel-frontend.git
git push -u origin main
```

Repository (GitHub):
├── backend/          ← Render uses this as root
│   ├── app.py
│   ├── requirements.txt
│   ├── models.py
│   └── ...
├── frontend/         ← GitHub Pages uses this
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── .gitignore 