# 🚀 Coolify Deployment Guide for Ahoum Agent

This guide will help you deploy the Ahoum facilitator onboarding agent to Coolify (self-hosted platform).

## 📋 Prerequisites

- Coolify instance running
- Git repository with your code
- LiveKit SIP trunk configured
- Required API keys (OpenAI, Deepgram, LiveKit)

## 🔧 Deployment Steps

### 1. **Environment Variables Setup**

In your Coolify dashboard, set these environment variables for your application:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret

# AI Services
OPENAI_API_KEY=sk-your-openai-key
DEEPGRAM_API_KEY=your-deepgram-key

# SIP Configuration (CRITICAL)
SIP_OUTBOUND_TRUNK_ID=ST_your-sip-trunk-id

# Optional Settings
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

### 2. **SIP Trunk Setup** (If not done already)

**Before deploying**, you need to create a SIP trunk in LiveKit:

```powershell
# On your local machine with LiveKit CLI installed:

# 1. Create the trunk configuration
# Note: outbound-trunk.json is gitignored for security
# You can create it temporarily for this setup

# 2. Create the SIP trunk
lk sip outbound create outbound-trunk.json

# 3. Copy the returned SIP_OUTBOUND_TRUNK_ID
# It should look like: ST_abc123def456...

# 4. Add this ID to your Coolify environment variables
```

### 3. **Repository Configuration**

Make sure your repository has:
- ✅ `Dockerfile` (updated to handle missing outbound-trunk.json)
- ✅ `requirements.txt`
- ✅ `agent.py`
- ❌ `outbound-trunk.json` (should be gitignored)
- ❌ `.env.local` (should be gitignored)

### 4. **Coolify Application Setup**

1. **Create New Application** in Coolify
2. **Connect Repository** (GitHub/GitLab)
3. **Set Build Pack**: Docker
4. **Dockerfile Path**: `./Dockerfile`
5. **Port**: 8080 (optional, mainly for health checks)

### 5. **Environment Variables in Coolify**

Add these in the Coolify dashboard under your app's Environment section:

| Variable | Value | Description |
|----------|-------|-------------|
| `LIVEKIT_URL` | `wss://your-server.com` | LiveKit server URL |
| `LIVEKIT_API_KEY` | `your-api-key` | LiveKit API key |
| `LIVEKIT_API_SECRET` | `your-api-secret` | LiveKit API secret |
| `OPENAI_API_KEY` | `sk-your-key` | OpenAI API key |
| `DEEPGRAM_API_KEY` | `your-key` | Deepgram API key |
| `SIP_OUTBOUND_TRUNK_ID` | `ST_your-trunk-id` | **Critical**: SIP trunk ID |
| `LOG_LEVEL` | `INFO` | Logging level |

### 6. **Deploy**

1. **Push code** to your repository
2. **Trigger deployment** in Coolify
3. **Monitor logs** for successful startup

## 🐛 Troubleshooting

### **Issue: outbound-trunk.json not found**
✅ **Solution**: The Dockerfile has been updated to make this file optional. The SIP configuration is now handled via environment variables.

### **Issue: SIP_OUTBOUND_TRUNK_ID not set**
❌ **Error**: `ValueError: SIP_OUTBOUND_TRUNK_ID is not set or invalid`
✅ **Solution**: 
1. Create SIP trunk: `lk sip outbound create outbound-trunk.json`
2. Copy the returned ID (starts with `ST_`)
3. Add to Coolify environment variables

### **Issue: Build fails during pip install**
❌ **Error**: Package installation errors
✅ **Solution**: The Dockerfile includes all necessary system dependencies for audio processing

### **Issue: LiveKit connection failed**
❌ **Error**: Connection timeout or authentication errors
✅ **Solution**: 
1. Verify `LIVEKIT_URL` is accessible from Coolify
2. Check `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`
3. Ensure LiveKit project is properly configured

## 📞 Testing Deployment

Once deployed, test the agent:

```powershell
# From your local machine with LiveKit CLI:
lk dispatch create --new-room --agent-name ahoum-facilitator-onboarding --metadata '+1234567890'
```

Monitor the logs in Coolify to see:
- ✅ Agent startup
- ✅ Room connection
- ✅ SIP participant creation
- ✅ Call initiation

## 🔄 Deployment Workflow

### **For Updates**:
1. **Update code** in your repository
2. **Push to main branch**
3. **Coolify auto-deploys** (if auto-deployment enabled)
4. **Monitor logs** for successful restart

### **For Configuration Changes**:
1. **Update environment variables** in Coolify
2. **Restart application** in Coolify dashboard
3. **Verify new settings** in logs

## 🔒 Security Notes

- ✅ **outbound-trunk.json is gitignored** (contains sensitive SIP credentials)
- ✅ **Environment variables used** for sensitive data
- ✅ **Non-root user** in Docker container
- ✅ **No hardcoded secrets** in code

## 📊 Monitoring

Monitor your application in Coolify:
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory usage
- **Health**: Container health checks
- **Deployments**: Deployment history

## 🆘 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Build fails at COPY outbound-trunk.json | File doesn't exist | ✅ Fixed in updated Dockerfile |
| SIP calls fail | Missing/invalid trunk ID | Set correct `SIP_OUTBOUND_TRUNK_ID` |
| AI responses fail | Missing API keys | Set `OPENAI_API_KEY`, `DEEPGRAM_API_KEY` |
| Connection timeout | LiveKit unreachable | Check `LIVEKIT_URL` and network |

## 🎉 Success Indicators

Your deployment is successful when you see:
- ✅ Container starts without errors
- ✅ Agent connects to LiveKit room
- ✅ SIP trunk validation passes
- ✅ Test calls work properly

The agent will be ready to receive dispatch commands and make outbound calls to facilitate Ahoum onboarding! 🚀
