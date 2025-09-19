# 🛡️ Safe Deployment Guide

## ✅ **Safe Deploy Method (Recommended)**
```bash
git add .
git commit -m "Your changes"
git push origin main
```
**Result:** Auto-deploy preserves database ✅

## 🔧 **Manual Deploy with Data Protection**

### **Before Manual Deploy:**
```bash
python pre_deploy.py
```
**This creates a backup of your database**

### **After Manual Deploy:**
```bash
python post_deploy.py
```
**This restores your data from backup**

## 🚨 **Emergency Recovery**

If you accidentally wiped your database:

1. **Find your backup file:**
   ```bash
   ls backup_*.json
   ```

2. **Restore from specific backup:**
   ```bash
   python db_persistence.py restore backup_20240919_205730.json
   ```

## 📋 **Quick Commands**

```bash
# Check database status
python db_persistence.py check

# Create backup
python db_persistence.py backup

# Restore from backup
python db_persistence.py restore backup_file.json
```

## 🎯 **Best Practices**

1. **Always use auto-deploy** (git push)
2. **If manual deploy needed:** Run pre_deploy.py first
3. **After manual deploy:** Run post_deploy.py
4. **Keep backup files** in your project directory

## 🚀 **Your Data is Now Protected!**

Even if you click "Deploy Latest Commit" manually, your data will be safe! 🛡️
