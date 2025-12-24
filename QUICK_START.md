# 🚀 Quick Start Guide

## Prerequisites Checklist
- [ ] Proxmox VE 8.4.0 installed
- [ ] Telegram Bot Token (from @BotFather)
- [ ] Your Telegram User ID (from @userinfobot)
- [ ] Proxmox API Token created
- [ ] Docker & Docker Compose installed
- [ ] SSH key for Proxmox access

## 5-Minute Setup

### 1. Create Proxmox API Token
```bash
# On Proxmox Web UI:
# Datacenter → Permissions → API Tokens → Add
# User: root@pam
# Token ID: bot
# Privilege Separation: UNCHECKED
# Copy the token value!
```

### 2. Clone & Configure
```bash
# Clone repository
git clone https://github.com/Dexoda/pve-telegram-manager.git
cd pve-telegram-manager

# Create environment file
cp .env.example .env
nano .env  # Edit with your values
```

### 3. Configure .env (Required)
```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11  # From @BotFather
ADMIN_IDS=123456789                                   # From @userinfobot
PVE_HOST=192.168.1.100                                # Your Proxmox IP
PVE_TOKEN_VALUE=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx # From Step 1
```

### 4. Setup SSH Key
```bash
# Generate key if needed
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Copy to Proxmox
ssh-copy-id root@YOUR_PROXMOX_IP

# Test connection
ssh root@YOUR_PROXMOX_IP "echo Connected successfully"
```

### 5. Launch Bot
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# You should see: "Bot starting..."
```

### 6. Test Bot
1. Open Telegram
2. Find your bot
3. Send `/start`
4. You should see the main menu!

## Common Issues

### "Access Denied"
- Check ADMIN_IDS in .env matches your Telegram ID
- Restart container: `docker-compose restart`

### "Cannot connect to Proxmox"
- Verify PVE_HOST is correct and accessible
- Test: `ping YOUR_PROXMOX_IP`
- Check API token is valid

### "SSH commands fail"
- Verify SSH key path: `ls -la ~/.ssh/id_rsa`
- Check key permissions: `chmod 600 ~/.ssh/id_rsa`
- Test SSH: `ssh root@YOUR_PROXMOX_IP`

## What's Next?

✅ Explore VM management
✅ Check system monitoring
✅ Set up CI/CD (optional)
✅ Configure alerts thresholds
✅ Add more admins to ADMIN_IDS

## Support

📖 Full docs: See README.md
🐛 Issues: https://github.com/Dexoda/pve-telegram-manager/issues
💬 Discussions: https://github.com/Dexoda/pve-telegram-manager/discussions

---
**Happy managing! 🎉**
