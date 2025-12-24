"""SSH client for executing commands on Proxmox host."""
import asyncio
import asyncssh
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SSHClient:
    """SSH client for executing commands on Proxmox host."""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None
    ):
        """
        Initialize SSH client.
        
        Args:
            host: SSH host
            port: SSH port
            username: SSH username
            password: SSH password (optional)
            key_path: Path to SSH private key (optional)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        
        logger.info(f"SSH client initialized for {username}@{host}:{port}")
    
    async def _connect(self) -> asyncssh.SSHClientConnection:
        """
        Create SSH connection.
        
        Returns:
            SSH connection
        """
        try:
            if self.key_path:
                conn = await asyncssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    client_keys=[self.key_path],
                    known_hosts=None
                )
            else:
                conn = await asyncssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    known_hosts=None
                )
            return conn
        except Exception as e:
            logger.error(f"Error connecting to SSH: {e}")
            raise
    
    async def run_command(self, command: str) -> Tuple[str, str, int]:
        """
        Run a command via SSH.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        try:
            async with await self._connect() as conn:
                result = await conn.run(command)
                return result.stdout, result.stderr, result.exit_status
        except Exception as e:
            logger.error(f"Error running command '{command}': {e}")
            return "", str(e), 1
    
    async def get_cpu_temperature(self) -> str:
        """
        Get CPU temperature using sensors.
        
        Returns:
            Temperature information
        """
        try:
            stdout, stderr, exit_code = await self.run_command("sensors")
            if exit_code == 0:
                return stdout
            else:
                return f"Error: {stderr}"
        except Exception as e:
            logger.error(f"Error getting CPU temperature: {e}")
            return f"Error: {str(e)}"
    
    async def get_smart_status(self) -> str:
        """
        Get SMART status for all disks.
        
        Returns:
            SMART status information
        """
        try:
            # Get list of disks
            stdout, stderr, exit_code = await self.run_command(
                "lsblk -d -n -o NAME | grep -E '^sd|^nvme'"
            )
            
            if exit_code != 0:
                return "Error: Could not list disks"
            
            disks = stdout.strip().split('\n')
            smart_info = []
            
            for disk in disks:
                disk = disk.strip()
                if not disk:
                    continue
                
                stdout, stderr, exit_code = await self.run_command(
                    f"smartctl -H /dev/{disk}"
                )
                
                if exit_code == 0 or exit_code == 4:  # 4 means disk has errors
                    smart_info.append(f"=== {disk} ===\n{stdout}\n")
                else:
                    smart_info.append(f"=== {disk} ===\nError: {stderr}\n")
            
            return "\n".join(smart_info) if smart_info else "No disk information available"
        except Exception as e:
            logger.error(f"Error getting SMART status: {e}")
            return f"Error: {str(e)}"
    
    async def ping_host(self, host: str, count: int = 4) -> str:
        """
        Ping a host.
        
        Args:
            host: Host to ping
            count: Number of packets to send
            
        Returns:
            Ping output
        """
        try:
            stdout, stderr, exit_code = await self.run_command(
                f"ping -c {count} {host}"
            )
            
            if exit_code == 0:
                return stdout
            else:
                return f"Error: {stderr if stderr else 'Host unreachable'}"
        except Exception as e:
            logger.error(f"Error pinging {host}: {e}")
            return f"Error: {str(e)}"
    
    async def traceroute_host(self, host: str) -> str:
        """
        Traceroute to a host.
        
        Args:
            host: Host to traceroute
            
        Returns:
            Traceroute output
        """
        try:
            # Try traceroute, if not available, use mtr
            stdout, stderr, exit_code = await self.run_command(
                f"traceroute -n -m 20 {host} 2>&1 || mtr -n -c 1 -r {host}"
            )
            
            if exit_code == 0:
                return stdout
            else:
                return f"Error: {stderr if stderr else 'Traceroute failed'}"
        except Exception as e:
            logger.error(f"Error tracerouting {host}: {e}")
            return f"Error: {str(e)}"
    
    async def get_system_logs(self, lines: int = 100) -> str:
        """
        Get system logs using journalctl.
        
        Args:
            lines: Number of log lines to retrieve
            
        Returns:
            System logs
        """
        try:
            stdout, stderr, exit_code = await self.run_command(
                f"journalctl -n {lines} --no-pager"
            )
            
            if exit_code == 0:
                return stdout
            else:
                return f"Error: {stderr}"
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return f"Error: {str(e)}"
    
    async def download_iso(self, url: str, storage_path: str) -> Tuple[bool, str]:
        """
        Download ISO file to storage.
        
        Args:
            url: URL of ISO file
            storage_path: Path to storage directory
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract filename from URL
            filename = url.split('/')[-1]
            if not filename.endswith('.iso'):
                filename += '.iso'
            
            full_path = f"{storage_path}/{filename}"
            
            # Use wget to download
            command = f"wget -O {full_path} {url}"
            stdout, stderr, exit_code = await self.run_command(command)
            
            if exit_code == 0:
                return True, f"Successfully downloaded {filename}"
            else:
                return False, f"Error: {stderr}"
        except Exception as e:
            logger.error(f"Error downloading ISO: {e}")
            return False, f"Error: {str(e)}"
    
    async def update_system(self) -> str:
        """
        Update system packages.
        
        Returns:
            Update output
        """
        try:
            # Run apt update and upgrade
            command = "apt-get update && apt-get upgrade -y"
            stdout, stderr, exit_code = await self.run_command(command)
            
            if exit_code == 0:
                return f"System updated successfully:\n{stdout}"
            else:
                return f"Error updating system:\n{stderr}"
        except Exception as e:
            logger.error(f"Error updating system: {e}")
            return f"Error: {str(e)}"
    
    async def get_disk_usage(self) -> str:
        """
        Get disk usage information.
        
        Returns:
            Disk usage output
        """
        try:
            stdout, stderr, exit_code = await self.run_command("df -h")
            
            if exit_code == 0:
                return stdout
            else:
                return f"Error: {stderr}"
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return f"Error: {str(e)}"
    
    async def get_network_stats(self) -> str:
        """
        Get network statistics.
        
        Returns:
            Network stats output
        """
        try:
            stdout, stderr, exit_code = await self.run_command(
                "ip -s link show"
            )
            
            if exit_code == 0:
                return stdout
            else:
                return f"Error: {stderr}"
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return f"Error: {str(e)}"
