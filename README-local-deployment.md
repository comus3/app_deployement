# Local Kubernetes Deployment Setup

This setup uses GitHub Actions for building and testing, but handles deployment locally using a cron job that checks for new Docker images every 2 minutes.

## 🏗️ Architecture

```
GitHub Actions (CI/CD)          Local Machine (Deployment)
┌─────────────────────┐        ┌─────────────────────────┐
│ 1. Run Unit Tests   │        │ 1. Cron Job (every 2min)│
│ 2. Build Docker     │ ──────▶│ 2. Check for new image  │
│ 3. Push to Registry │        │ 3. Pull new image       │
│ 4. Notify Complete  │        │ 4. Deploy to K8s        │
└─────────────────────┘        └─────────────────────────┘
```

## 🚀 Setup Instructions

### 1. Prerequisites

- **kubectl** installed and configured
- **Docker** installed and running
- **Access to GitHub Container Registry**

### 2. Configure GitHub Container Registry Access

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u comus3 --password-stdin
```

### 3. Setup the Cron Job

```bash
# Run the setup script
./setup-cron.sh
```

This will:
- ✅ Check prerequisites (kubectl, docker, registry access)
- ✅ Create a cron job that runs every 2 minutes
- ✅ Configure logging to `/tmp/k8s-cron.log`

### 4. Manual Deployment (Optional)

```bash
# Deploy to test environment
./local-deploy.sh test latest

# Deploy to production environment  
./local-deploy.sh prod latest
```

## 📊 Monitoring

### View Cron Job Logs
```bash
# Real-time monitoring
tail -f /tmp/k8s-cron.log

# View recent logs
tail -n 50 /tmp/k8s-cron.log
```

### Check Cron Job Status
```bash
# List active cron jobs
crontab -l

# View cron job execution
grep CRON /var/log/syslog
```

### Kubernetes Status
```bash
# Check deployments
kubectl get deployments -A

# Check pods
kubectl get pods -A

# Check services
kubectl get services -A
```

## 🔧 Configuration

### Environment Variables
- `IMAGE_NAME`: `ghcr.io/comus3/app_deployement`
- `LOG_FILE`: `/tmp/k8s-cron.log`
- `LAST_IMAGE_FILE`: `/tmp/last-deployed-image.txt`

### Cron Schedule
- **Current**: Every 2 minutes (`*/2 * * * *`)
- **Customize**: Edit crontab with `crontab -e`

## 🛠️ Troubleshooting

### Common Issues

1. **Cron job not running**
   ```bash
   # Check if cron service is running
   sudo systemctl status cron
   
   # Restart cron service
   sudo systemctl restart cron
   ```

2. **Docker registry access denied**
   ```bash
   # Re-login to registry
   docker login ghcr.io -u comus3
   ```

3. **kubectl not found**
   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

### Log Files
- **Cron logs**: `/tmp/k8s-cron.log`
- **Deployment logs**: `/tmp/k8s-deploy.log`
- **System logs**: `/var/log/syslog`

## 🎯 Workflow

1. **Developer pushes code** to GitHub
2. **GitHub Actions** runs tests and builds Docker image
3. **Image is pushed** to GitHub Container Registry
4. **Local cron job** detects new image (every 2 minutes)
5. **Automatic deployment** to Kubernetes cluster
6. **Rolling update** ensures zero downtime

## 🧹 Cleanup

### Remove Cron Job
```bash
# Edit crontab
crontab -e

# Remove the line with the deployment script
# Or remove all cron jobs
crontab -r
```

### Clean Log Files
```bash
# Remove log files
rm -f /tmp/k8s-cron.log /tmp/k8s-deploy.log /tmp/last-deployed-image.txt
```

## 📈 Benefits

- ✅ **Separation of concerns**: CI/CD handles building, local handles deployment
- ✅ **Local control**: Full control over deployment timing and environment
- ✅ **Cost effective**: No need for cloud Kubernetes clusters
- ✅ **Flexible**: Easy to customize deployment logic
- ✅ **Monitoring**: Full visibility into deployment process
