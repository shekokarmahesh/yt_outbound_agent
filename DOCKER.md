# 🐳 Ahoum Facilitator Agent - Docker Setup

This guide will help you run the Ahoum facilitator onboarding agent using Docker.

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)
- Your environment variables configured

## 🚀 Quick Start

### 1. Environment Setup

Copy the environment template and fill in your credentials:

```bash
# Copy the production environment template
cp .env.production.example .env.local

# Edit the file with your actual credentials
# You can use any text editor
notepad .env.local
```

Required environment variables:
- `LIVEKIT_URL` - Your LiveKit server URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o-mini
- `DEEPGRAM_API_KEY` - Deepgram API key for speech-to-text
- `SIP_OUTBOUND_TRUNK_ID` - Your SIP trunk ID from LiveKit

### 2. Build and Run

```bash
# Build and start the container
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

### 3. Making Calls

Once the agent is running, you can dispatch calls using the LiveKit CLI:

```bash
# Make a call to a potential facilitator
lk dispatch create --new-room --agent-name ahoum-facilitator-onboarding --metadata '+1234567890'
```

## 🛠️ Docker Commands

### Basic Operations

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up

# Start in background
docker-compose up -d

# Stop the service
docker-compose down

# View logs
docker-compose logs -f

# Restart the service
docker-compose restart
```

### Development Commands

```bash
# Rebuild and start (useful after code changes)
docker-compose up --build

# Run a one-off command in the container
docker-compose run ahoum-agent python --version

# Access the container shell
docker-compose exec ahoum-agent bash

# View real-time logs
docker-compose logs -f ahoum-agent
```

### Cleanup Commands

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all

# Clean up Docker system
docker system prune -a
```

## 📊 Monitoring

### View Logs
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific time period
docker-compose logs --since "1h"

# View last 100 lines
docker-compose logs --tail 100
```

### Container Status
```bash
# Check container status
docker-compose ps

# View container resource usage
docker stats
```

## 🔧 Configuration

### Environment Variables

You can override default settings using environment variables in `.env.local`:

```bash
# Logging
LOG_LEVEL=DEBUG

# Call settings
CALL_TIMEOUT=120
MAX_CONCURRENT_CALLS=10

# Health check settings
HEALTH_CHECK_INTERVAL=30s
```

### Volumes

The Docker setup includes persistent volumes for:
- **Logs**: `./logs` - Application logs are stored here
- **Configuration**: Environment variables are loaded from `.env.local`

### Resource Limits

The docker-compose file includes resource limits:
- **Memory**: 1GB limit, 512MB reserved
- **CPU**: 0.5 cores limit, 0.25 cores reserved

Adjust these in `docker-compose.yml` based on your needs.

## 🔒 Security Notes

- The container runs as a non-root user (`ahoum`) for security
- Sensitive files are excluded via `.dockerignore`
- Environment variables are kept in `.env.local` (gitignored)
- The `outbound-trunk.json` file is copied but should be secured

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Fix file permissions
   chmod +x agent.py
   ```

2. **Environment Variables Not Loaded**
   ```bash
   # Check if .env.local exists and has correct format
   cat .env.local
   ```

3. **Container Won't Start**
   ```bash
   # Check container logs
   docker-compose logs ahoum-agent
   
   # Check if ports are available
   netstat -an | findstr "8080"
   ```

4. **Audio/SIP Issues**
   ```bash
   # Verify SIP trunk ID format
   echo $SIP_OUTBOUND_TRUNK_ID
   # Should start with "ST_"
   ```

### Debug Mode

Run the container in debug mode:

```bash
# Override the command to run in interactive mode
docker-compose run --rm ahoum-agent bash

# Then manually run the agent
python agent.py dev
```

## 🚀 Production Deployment

For production deployment:

1. Use `.env.production` instead of `.env.local`
2. Set `restart: always` in docker-compose.yml
3. Configure proper logging and monitoring
4. Set up health checks and alerts
5. Use Docker secrets for sensitive data

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📈 Scaling

To run multiple agent instances:

```bash
# Scale up to 3 instances
docker-compose up --scale ahoum-agent=3

# Or specify in docker-compose.yml:
# deploy:
#   replicas: 3
```

## 🔗 Integration

The containerized agent integrates with:
- **LiveKit** - For real-time communication
- **Twilio** - For SIP telephony
- **OpenAI** - For AI conversation
- **Deepgram** - For speech recognition

Make sure all external services are properly configured and accessible from the container.
