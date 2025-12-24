# 🤖 Proxmox VE Telegram Manager

A powerful asynchronous Telegram bot for managing Proxmox VE 8.4.0 with comprehensive monitoring, VM management, and system administration features.

## ✨ Features

### 🖥️ Virtual Machine Management
- 📋 List all VMs and LXC containers with real-time status
- ▶️ Start, stop, shutdown, and reboot VMs
- 📊 View detailed VM information (CPU, RAM, uptime, IP addresses)
- ⭐ Add VMs to favorites for quick access
- 🖼️ Generate NoVNC console links
- 🔍 Search VMs by name or ID

### 📈 System Monitoring
- 💻 Node resource monitoring (CPU, RAM, disk usage)
- 🌡️ CPU temperature monitoring via lm-sensors
- 💾 Disk SMART status checks
- 🌐 Network traffic statistics
- 📊 System load average
- 📉 Beautiful progress bars for resource visualization

### 💾 Storage Management
- 📀 List ISO images
- ⬇️ Download ISO from URL
- 💿 View all storage pools with usage statistics
- 📦 List and manage backups

### 🔧 System Tools
- 🏓 Ping any host
- 🛣️ Traceroute to destinations
- 🔄 System update with confirmation
- 📜 View system logs (journalctl)
- 📋 Proxmox and QEMU logs

### 💰 Finance Calculator
- ⚡ Electricity cost calculator with Almaty progressive tariffs
- 📊 Support for multi-tier pricing:
  - 0-150 kWh: 23.21 KZT/kWh
  - 150-300 kWh: 28.50 KZT/kWh
  - 300+ kWh: 35.00 KZT/kWh

### 🔔 Alert System
- 🚨 High CPU load notifications (&gt;90% for 5+ minutes)
- 🔄 VM status change alerts
- 🔐 Proxmox login event notifications
- 📱 Real-time Telegram notifications to admins

## 🚀 Installation

### Prerequisites

1. **Proxmox VE 8.4.0** server
2. **Docker** and **Docker Compose** installed
3. **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
4. **Tailscale** for secure networking (recommended)

### Step 1: Create Proxmox API Token

1. Log in to Proxmox web interface
2. Navigate to **Datacenter → Permissions → API Tokens**
3. Click **Add** and create a token:
   - User: `root@pam`
   - Token ID: `bot`
   - Privilege Separation: Unchecked (for full access)
4. Save the token value securely

### Step 2: Set Up Tailscale

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to your Tailnet
sudo tailscale up

# Get your Proxmox Tailscale IP
tailscale ip -4
```

### Step 3: Clone Repository

```bash
cd ~
git clone https://github.com/Dexoda/pve-telegram-manager.git
cd pve-telegram-manager
```

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Update the following values in `.env`:
- `BOT_TOKEN`: Your Telegram bot token
- `ADMIN_IDS`: Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
- `PVE_HOST`: Proxmox Tailscale IP
- `PVE_TOKEN_VALUE`: API token from Step 1
- `SSH_HOST`: Proxmox Tailscale IP
- `SSH_KEY_PATH`: Path to SSH key (generate if needed)

### Step 5: Set Up SSH Access

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Copy SSH key to Proxmox server
ssh-copy-id root@<PROXMOX_IP>

# Test SSH connection
ssh root@<PROXMOX_IP> "echo 'SSH connection successful'"
```

### Step 6: Run with Docker

```bash
# Create data directory
mkdir -p data

# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔧 CI/CD Setup

### GitHub Secrets Configuration

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

- `SERVER_HOST`: Your server's IP or hostname
- `SERVER_USER`: SSH user (usually `root`)
- `SERVER_SSH_KEY`: Private SSH key content

The bot will automatically redeploy when you push to the `main` branch.

## 📱 Bot Commands

### Basic Commands
- `/start` - Start the bot and show main menu
- `/help` - Display help information

### Main Menu Options
- **🖥️ Virtual Machines** - Manage VMs and containers
- **📊 Monitoring** - View system resources
- **💾 Storage** - Manage storage and ISOs
- **⚡ Finance** - Calculate electricity costs
- **📜 Logs** - View system logs
- **🔧 Tools** - System utilities

### VM Management
- View all VMs with status indicators (🟢 running, 🔴 stopped)
- Quick actions: Start, Stop, Shutdown, Reboot
- View detailed information
- Access NoVNC console
- Add/remove favorites

### Monitoring Features
- CPU usage and temperature
- RAM usage
- Disk usage and SMART status
- Network statistics
- System load average

### Storage Operations
- Browse ISO library
- Download new ISOs from URLs
- View storage pool usage
- Browse backups

### System Tools
- Ping test with latency
- Traceroute diagnostics
- System package updates

## 🔒 Security

### ⚠️ Important Security Notes

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use API tokens** - More secure than password authentication
3. **Restrict admin access** - Configure `ADMIN_IDS` properly
4. **Use Tailscale** - Secure networking without exposing ports
5. **SSH keys only** - Disable password authentication
6. **Regular updates** - Keep system and dependencies updated

### SSH Key Security

```bash
# Mount SSH keys as read-only in Docker
volumes:
  - ~/.ssh:/root/.ssh:ro
```

### Telegram Authorization

Only users listed in `ADMIN_IDS` can access the bot. All unauthorized access attempts are logged.

## 🐛 Troubleshooting

### Bot doesn't respond

```bash
# Check if container is running
docker-compose ps

# View logs
docker-compose logs -f

# Restart bot
docker-compose restart
```

### Proxmox API connection issues

```bash
# Test Proxmox API from container
docker-compose exec pve-telegram-bot curl -k https://<PVE_HOST>:8006/api2/json/version

# Verify token has correct permissions
# Check Proxmox web UI → Permissions → API Tokens
```

### SSH connection issues

```bash
# Test SSH from container
docker-compose exec pve-telegram-bot ssh -i /root/.ssh/id_rsa root@<SSH_HOST> "echo test"

# Verify SSH key permissions
chmod 600 ~/.ssh/id_rsa
```

### Database errors

```bash
# Remove and recreate database
rm data/bot.db
docker-compose restart
```

### High CPU usage

```bash
# Check alert service configuration
# Adjust ALERT_CHECK_INTERVAL in .env (default: 60 seconds)
```

## 📊 Database Schema

The bot uses SQLite with the following tables:

### `users`
- `user_id` (INTEGER PRIMARY KEY)
- `username` (TEXT)
- `first_seen` (TIMESTAMP)
- `last_seen` (TIMESTAMP)

### `favorites`
- `user_id` (INTEGER)
- `vmid` (INTEGER)
- `name` (TEXT)
- `node` (TEXT)
- `vm_type` (TEXT)
- `added_at` (TIMESTAMP)

### `usage_logs`
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER)
- `username` (TEXT)
- `command` (TEXT)
- `timestamp` (TIMESTAMP)

## 🏗️ Project Structure

```
pve-telegram-manager/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── src/
│   ├── config.py               # Configuration loader
│   ├── main.py                 # Bot initialization
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py              # Database manager
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── common.py          # Auth, /start, /help
│   │   ├── vms.py             # VM management
│   │   ├── monitoring.py      # System monitoring
│   │   ├── storage.py         # Storage management
│   │   ├── finance.py         # Cost calculator
│   │   ├── logs.py            # Log viewer
│   │   └── tools.py           # Utilities
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline.py          # Inline keyboards
│   ├── services/
│   │   ├── __init__.py
│   │   ├── proxmox.py         # Proxmox API client
│   │   ├── ssh_client.py      # SSH executor
│   │   └── alerts.py          # Alert service
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py      # MarkdownV2 formatting
│       └── progress_bars.py   # Progress visualization
├── data/                       # Database and logs
├── .env.example               # Environment template
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Async Telegram Bot API framework
- [proxmoxer](https://github.com/proxmoxer/proxmoxer) - Proxmox API wrapper
- [asyncssh](https://github.com/ronf/asyncssh) - Async SSH client

## 📧 Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/Dexoda/pve-telegram-manager/issues)
- Contact: [@Dexoda](https://t.me/Dexoda)

---

**⚡ Made with ❤️ for Proxmox VE system administrators**
