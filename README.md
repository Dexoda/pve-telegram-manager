# 🤖 Proxmox VE Telegram Manager

A comprehensive Telegram bot for managing Proxmox Virtual Environment 8.4.0 from your mobile device. Built with aiogram 3.x and featuring full async support.

## ✨ Features

### 🖥 Virtual Machine Management
- 📋 List all VMs and containers with real-time status
- ▶️ Start/Stop/Shutdown/Reboot VMs
- 📊 View detailed VM information (CPU, RAM, uptime, IP)
- ⭐ Add VMs to favorites for quick access
- 🖥 Generate NoVNC console links
- 🔍 Search VMs by name or ID

### 📊 System Monitoring
- 💻 Node status (CPU, RAM, disk usage, uptime)
- 🌡 CPU temperature monitoring (lm-sensors)
- 💽 Disk status and usage
- 🔍 SMART disk health status
- 🌐 Network traffic statistics
- ⚡ System load average

### 💾 Storage Management
- 📀 List ISO images
- 💿 View all storages with usage statistics
- 🗄 List backups
- 📥 Download ISO from URL (feature available)

### 🔧 System Tools
- 🏓 Ping any host
- 🗺 Traceroute to any destination
- 🔄 System package updates

### 💰 Finance Calculator
- 💡 Electricity cost calculator with Almaty (Kazakhstan) progressive tariffs
- 📈 Supports multi-tier pricing (0-150, 150-300, 300+ kWh)
- 📊 Cost breakdown and monthly estimates

### 📋 Logs & Monitoring
- 📜 System logs (journalctl)
- 🖥 Proxmox daemon logs
- 🔍 QEMU guest agent logs

## 🚀 Installation

### Prerequisites

1. **Proxmox VE 8.4.0** installed and running
2. **Docker** and **Docker Compose** on your management server
3. **Tailscale** (optional, for secure remote access)
4. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

### Step 1: Create Proxmox API Token

1. Log in to Proxmox web interface
2. Navigate to **Datacenter → Permissions → API Tokens**
3. Click **Add** and create a token:
   - User: `root@pam`
   - Token ID: `bot`
   - Privilege Separation: **Unchecked** (for full access)
4. Save the token value securely

### Step 2: Set Up Tailscale (Optional)

For secure remote access without opening ports:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Get your Tailscale IP
tailscale ip -4
```

Update your `.env` with the Tailscale IP.

### Step 3: Clone Repository

```bash
git clone https://github.com/Dexoda/pve-telegram-manager.git
cd pve-telegram-manager
```

### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env
```

Update the following values:

```env
# Required
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=your_telegram_user_id
PVE_HOST=your_proxmox_ip
PVE_TOKEN_VALUE=your_api_token

# Optional
SSH_KEY_PATH=/root/.ssh/id_rsa  # Path to SSH key
TARIFF_STEP_1=23.21              # Electricity tariffs
```

**Getting your Telegram User ID:**
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your ID
3. Add to `ADMIN_IDS` (multiple IDs: `123456789,987654321`)

### Step 5: Generate SSH Key (if not exists)

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
ssh-copy-id root@your_proxmox_ip
```

### Step 6: Run with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📱 Usage

### Basic Commands

- `/start` - Show main menu
- `/help` - Display help information
- `/menu` - Return to main menu

### Navigation

The bot uses inline keyboards for easy navigation. Simply tap the buttons to:

- 🖥 Manage virtual machines
- 📊 Monitor system resources
- 💾 View storage and ISOs
- 🔧 Use system tools
- 💰 Calculate electricity costs
- 📋 View logs

## 🔧 CI/CD Setup

### GitHub Actions Auto-Deployment

1. **Add GitHub Secrets:**

   Go to **Settings → Secrets and variables → Actions** and add:

   - `SSH_HOST` - Your server IP
   - `SSH_USER` - Server username
   - `SSH_KEY` - Private SSH key for server access

2. **Enable Workflow:**

   The workflow in `.github/workflows/deploy.yml` will automatically:
   - Deploy on push to `main` branch
   - SSH to your server
   - Pull latest code
   - Rebuild and restart container

3. **Manual Trigger:**

   ```bash
   git push origin main
   ```

## 🛠 Development

### Project Structure

```
pve-telegram-manager/
├── src/
│   ├── config.py                 # Configuration loader
│   ├── main.py                   # Bot entry point
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py                 # SQLite database manager
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── common.py             # Auth, /start, /help
│   │   ├── vms.py                # VM management
│   │   ├── monitoring.py         # System monitoring
│   │   ├── storage.py            # Storage management
│   │   ├── finance.py            # Cost calculator
│   │   ├── logs.py               # System logs
│   │   └── tools.py              # Utilities
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline.py             # Inline keyboards
│   ├── services/
│   │   ├── __init__.py
│   │   ├── proxmox.py            # Proxmox API client
│   │   └── ssh_client.py         # SSH command executor
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py         # MarkdownV2 utils
│       └── progress_bars.py      # Progress bars, formatters
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run bot
python -m src.main
```

## 🔒 Security

### Important Security Notes

⚠️ **Never commit the `.env` file to version control**
⚠️ **Use strong, unique API tokens**
⚠️ **Restrict admin access via `ADMIN_IDS`**
⚠️ **Keep SSH keys secure and read-only in container**
⚠️ **Use Tailscale or VPN for remote access**
⚠️ **Regularly update system packages**

### Authorization

The bot uses middleware to verify user IDs. Only users listed in `ADMIN_IDS` can:
- View VM information
- Execute commands
- Access monitoring data
- Perform system operations

Unauthorized users receive an access denied message.

## 🐛 Troubleshooting

### Bot not starting

```bash
# Check logs
docker-compose logs

# Verify environment variables
docker-compose config

# Ensure data directory exists
mkdir -p data
```

### Cannot connect to Proxmox

- Verify `PVE_HOST` is correct
- Check API token is valid and not expired
- Ensure Proxmox is accessible from bot server
- Test with: `curl https://<PVE_HOST>:8006`

### SSH commands failing

- Verify SSH key path is correct
- Test SSH connection: `ssh -i /path/to/key root@proxmox_ip`
- Ensure key is mounted in Docker: check `docker-compose.yml`
- Check key permissions: `chmod 600 ~/.ssh/id_rsa`

### Database errors

```bash
# Reset database
rm -rf data/
mkdir data
docker-compose restart
```

### MarkdownV2 formatting errors

The bot uses MarkdownV2 format. Special characters are automatically escaped in `formatters.py`.

## 📊 Database Schema

The bot uses SQLite with three tables:

- **users** - Track bot users
- **favorites** - User favorite VMs
- **usage_logs** - Command usage logs

Data is stored in `./data/bot.db`

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [proxmoxer](https://github.com/proxmoxer/proxmoxer) - Proxmox API wrapper
- [asyncssh](https://github.com/ronf/asyncssh) - Async SSH library

## 📧 Support

For issues, questions, or suggestions:
- 🐛 [Open an issue](https://github.com/Dexoda/pve-telegram-manager/issues)
- 💬 [Discussions](https://github.com/Dexoda/pve-telegram-manager/discussions)

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Made with ❤️ for Proxmox users who want to manage their infrastructure on the go!**
