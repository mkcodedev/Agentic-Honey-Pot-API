# 🚀 Deployment Guide

Complete guide for deploying the Agentic Honey-Pot API to various platforms.

---

## Table of Contents

1. [Render Deployment](#render-deployment)
2. [Railway Deployment](#railway-deployment)
3. [Heroku Deployment](#heroku-deployment)
4. [Google Cloud Run](#google-cloud-run)
5. [AWS EC2](#aws-ec2)
6. [Docker Deployment](#docker-deployment)

---

## Render Deployment

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/honeypot.git
   git push -u origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `honeypot-api`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   ```
   HONEYPOT_API_KEY=your-secret-key-here
   LLM_PROVIDER=gemini
   LLM_API_KEY=your-gemini-key-here
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Your API will be available at: `https://honeypot-api.onrender.com`

### Cost: Free tier available

---

## Railway Deployment

### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure**
   Railway auto-detects Python and FastAPI!
   
4. **Add Environment Variables**
   - Go to Variables tab
   - Add:
     ```
     HONEYPOT_API_KEY=your-secret-key-here
     LLM_PROVIDER=gemini
     LLM_API_KEY=your-gemini-key-here
     ```

5. **Deploy**
   - Automatic deployment on push
   - Get public URL from Railway dashboard

### Cost: $5/month usage-based

---

## Heroku Deployment

### Steps:

1. **Install Heroku CLI**
   ```bash
   # Windows (using chocolatey)
   choco install heroku-cli
   
   # Mac
   brew install heroku/brew/heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Create Procfile**
   ```bash
   echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
   ```

3. **Create runtime.txt** (optional)
   ```bash
   echo "python-3.11.0" > runtime.txt
   ```

4. **Deploy**
   ```bash
   heroku login
   heroku create honeypot-api-unique-name
   
   # Set environment variables
   heroku config:set HONEYPOT_API_KEY=your-secret-key-here
   heroku config:set LLM_PROVIDER=gemini
   heroku config:set LLM_API_KEY=your-gemini-key-here
   
   # Deploy
   git push heroku main
   
   # Open app
   heroku open
   ```

5. **View Logs**
   ```bash
   heroku logs --tail
   ```

### Cost: Free tier removed, starts at $7/month

---

## Google Cloud Run

### Steps:

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. **Install Google Cloud SDK**
   - Download from [cloud.google.com/sdk](https://cloud.google.com/sdk)

3. **Deploy**
   ```bash
   # Login
   gcloud auth login
   
   # Set project
   gcloud config set project YOUR_PROJECT_ID
   
   # Build and deploy
   gcloud run deploy honeypot-api \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars HONEYPOT_API_KEY=your-key,LLM_PROVIDER=gemini,LLM_API_KEY=your-gemini-key
   ```

### Cost: Pay per use, generous free tier

---

## AWS EC2

### Steps:

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t2.micro (free tier)
   - Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)

2. **SSH into Instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx -y
   ```

4. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/honeypot.git
   cd honeypot
   ```

5. **Setup Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Create .env File**
   ```bash
   nano .env
   # Add your environment variables
   ```

7. **Setup Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/honeypot.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=Honeypot API
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/honeypot
   Environment="PATH=/home/ubuntu/honeypot/venv/bin"
   ExecStart=/home/ubuntu/honeypot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

8. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start honeypot
   sudo systemctl enable honeypot
   sudo systemctl status honeypot
   ```

9. **Setup Nginx Reverse Proxy**
   ```bash
   sudo nano /etc/nginx/sites-available/honeypot
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   Enable:
   ```bash
   sudo ln -s /etc/nginx/sites-available/honeypot /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Cost: Free tier 750 hours/month for 12 months

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  honeypot-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HONEYPOT_API_KEY=${HONEYPOT_API_KEY}
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_API_KEY=${LLM_API_KEY}
    restart: unless-stopped
```

### Usage

```bash
# Build image
docker build -t honeypot-api .

# Run container
docker run -d \
  -p 8000:8000 \
  -e HONEYPOT_API_KEY=your-key \
  -e LLM_PROVIDER=gemini \
  -e LLM_API_KEY=your-gemini-key \
  --name honeypot \
  honeypot-api

# Or use docker-compose
docker-compose up -d

# View logs
docker logs -f honeypot

# Stop
docker stop honeypot
```

---

## Environment Variables Reference

All platforms require these environment variables:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `HONEYPOT_API_KEY` | ✅ Yes | `sk_live_abc123xyz` | API authentication key |
| `LLM_PROVIDER` | ❌ No | `gemini` | LLM provider (leave empty for rule-based only) |
| `LLM_API_KEY` | ❌ No | `AIza...` | Google Gemini API key |
| `PORT` | ❌ No | `8000` | Server port (auto-set by most platforms) |

---

## Post-Deployment Checklist

- ✅ Test health endpoint: `https://your-domain.com/health`
- ✅ Test API docs: `https://your-domain.com/docs`
- ✅ Verify API key authentication
- ✅ Test sample scam message
- ✅ Check callback functionality
- ✅ Monitor logs for errors
- ✅ Setup monitoring/alerts (optional)

---

## Monitoring & Logging

### Render
- Built-in logs in dashboard
- Free log retention: 7 days

### Railway
- Logs tab in project dashboard
- Real-time log streaming

### Heroku
```bash
heroku logs --tail --app your-app-name
```

### AWS EC2
```bash
# Application logs
sudo journalctl -u honeypot -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### Issue: App crashes on startup
**Solution**: Check environment variables are set correctly

### Issue: 502 Bad Gateway
**Solution**: Ensure app is listening on `0.0.0.0` not `localhost`

### Issue: Timeout errors
**Solution**: Increase timeout in platform settings or add health check endpoint

### Issue: Memory errors
**Solution**: Upgrade to higher tier or optimize code

---

## Security Recommendations

1. **Use HTTPS**: Always enable SSL/TLS in production
2. **Rotate API Keys**: Change keys regularly
3. **Rate Limiting**: Add rate limiting middleware
4. **CORS**: Configure CORS properly for your use case
5. **Monitoring**: Setup error tracking (Sentry, etc.)
6. **Backups**: Regular session data backups if using persistent storage

---

## Performance Optimization

1. **Use production ASGI server**: Already using Uvicorn ✅
2. **Enable workers**: `uvicorn main:app --workers 4`
3. **Add Redis**: For distributed session storage
4. **Add caching**: Cache LLM responses
5. **Connection pooling**: For database if added later

---

**Choose the platform that best fits your needs and budget! 🚀**
