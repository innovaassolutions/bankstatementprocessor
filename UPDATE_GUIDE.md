# 🔄 Update Guide for Docker Hub Users

This guide explains how to get updates when new versions of the Bank Statement Processor are released on Docker Hub.

**Docker Hub Repository**: `innovaassolutions/bank-processor`

## 🚀 Quick Update Commands

### **Option 1: Update to Latest Version**
```bash
# Pull the latest version
docker pull innovaassolutions/bank-processor:latest

# Stop current container
docker stop your-container-name

# Remove old container
docker rm your-container-name

# Start new container with latest version
docker run -d -p 3005:5000 --name bank-processor innovaassolutions/bank-processor:latest
```

### **Option 2: Update to Specific Version**
```bash
# Pull specific version (e.g., 1.1.0)
docker pull innovaassolutions/bank-processor:1.1.0

# Stop and remove old container
docker stop your-container-name
docker rm your-container-name

# Start new container with specific version
docker run -d -p 3005:5000 --name bank-processor innovaassolutions/bank-processor:1.1.0
```

## 🔧 Using Docker Compose

### **Update docker-compose.yml**
```yaml
version: '3.8'
services:
  bank-processor:
    image: innovaassolutions/bank-processor:latest  # or specific version like :1.1.0
    ports:
      - "3005:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
      - ./data:/app/data
      - ./merchant_config.txt:/app/merchant_config.txt
    restart: unless-stopped
```

### **Update with Compose**
```bash
# Pull latest images
docker-compose pull

# Restart services with new images
docker-compose up -d
```

## 🤖 Automated Updates

### **Option 1: Cron Job (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add this line to check for updates daily at 2 AM
0 2 * * * cd /path/to/your/project && docker pull innovaassolutions/bank-processor:latest && docker-compose up -d
```

### **Option 2: Update Script**
Create `update.sh`:
```bash
#!/bin/bash
cd /path/to/your/project
docker pull yourusername/bank-processor:latest
docker-compose down
docker-compose up -d
echo "Updated at $(date)"
```

Make it executable and run:
```bash
chmod +x update.sh
./update.sh
```

### **Option 3: Watchtower (Automatic Updates)**
```bash
# Install Watchtower for automatic updates
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 86400 \
  innovaassolutions/bank-processor
```

## 📋 Update Checklist

Before updating, ensure you:

1. **Backup your data**:
   ```bash
   cp -r output/ output_backup_$(date +%Y%m%d)/
   cp -r data/ data_backup_$(date +%Y%m%d)/
   cp merchant_config.txt merchant_config_backup_$(date +%Y%m%d).txt
   ```

2. **Check current version**:
   ```bash
   docker inspect innovaassolutions/bank-processor:latest | grep -i version
   ```

3. **Review release notes** on GitHub for breaking changes

4. **Test the update** in a staging environment if possible

## 🔍 Version Information

### **Check Available Versions**
```bash
# List all available tags
docker images innovaassolutions/bank-processor

# Check version in running container
docker exec your-container-name python -c "import app; print(app.VERSION)"
```

### **Version Tags Available**
- `:latest` - Most recent stable version
- `:1.0.0` - Specific version (semantic versioning)
- `:develop` - Development version (unstable)

## ⚠️ Important Notes

1. **Data Persistence**: Your data is safe in mounted volumes
2. **Breaking Changes**: Check release notes for major version updates
3. **Rollback**: You can always go back to a previous version
4. **Testing**: Test updates in non-production environments first

## 🆘 Troubleshooting

### **Update Fails**
```bash
# Check container logs
docker logs your-container-name

# Verify image integrity
docker images --digests yourusername/bank-processor

# Force pull (overwrite local image)
docker pull --force yourusername/bank-processor:latest
```

### **Container Won't Start**
```bash
# Check port conflicts
netstat -tulpn | grep 3005

# Verify image exists
docker images yourusername/bank-processor

# Run with interactive mode for debugging
docker run -it --rm -p 3005:5000 yourusername/bank-processor:latest
```

## 📞 Support

If you encounter issues with updates:

1. Check the [GitHub Issues](https://github.com/yourusername/bank-processor/issues)
2. Review the [README.md](README.md) for troubleshooting
3. Create a new issue with your error details

## 🎯 Best Practices

1. **Use specific versions** in production for stability
2. **Test updates** before applying to production
3. **Keep backups** of your data and configuration
4. **Monitor logs** after updates for any issues
5. **Update regularly** to get security patches and new features

---

**Happy Processing! 🎉**
