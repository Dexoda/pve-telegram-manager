"""SSH command executor using asyncssh."""

import asyncio
import logging
from typing import Optional, Tuple
import asyncssh

logger = logging.getLogger(__name__)


class SSHClient:
    """Async SSH client for executing commands on Proxmox host."""
    
    def __init__(self, host: str, user: str, key_path: str, port: int = 22):
        """Initialize SSH client.
        
        Args:
            host: SSH host address.
            user: SSH username.
            key_path: Path to SSH private key.
            port: SSH port (default: 22).
        """
        self.host = host
        self.user = user
        self.key_path = key_path
        self.port = port
    
    async def run_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute SSH command.
        
        Args:
            command: Command to execute.
            timeout: Command timeout in seconds.
            
        Returns:
            Tuple[str, str, int]: (stdout, stderr, exit_code)
        """
        try:
            async with asyncssh.connect(
                self.host,
                port=self.port,
                username=self.user,
                client_keys=[self.key_path],
                known_hosts=None
            ) as conn:
                result = await asyncio.wait_for(
                    conn.run(command),
                    timeout=timeout
                )
                
                stdout = result.stdout if result.stdout else ""
                stderr = result.stderr if result.stderr else ""
                exit_code = result.exit_status if result.exit_status is not None else 0
                
                return stdout, stderr, exit_code
        except asyncio.TimeoutError:
            logger.error(f"Command timeout: {command}")
            raise Exception(f"Command timeout after {timeout}s")
        except Exception as e:
            logger.error(f"SSH command failed: {e}")
            raise
    
    async def get_cpu_temperature(self) -> Optional[str]:
        """Get CPU temperature via lm-sensors.
        
        Returns:
            Optional[str]: Temperature output or None if not available.
        """
        try:
            stdout, stderr, code = await self.run_command("sensors -A")
            if code == 0:
                return stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get CPU temperature: {e}")
            return None
    
    async def get_smart_status(self, device: str = "/dev/sda") -> Optional[str]:
        """Get disk SMART status.
        
        Args:
            device: Disk device path.
            
        Returns:
            Optional[str]: SMART status output or None if not available.
        """
        try:
            stdout, stderr, code = await self.run_command(f"smartctl -H {device}")
            if code == 0 or code == 1:  # Exit code 1 can be normal for some SMART checks
                return stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get SMART status: {e}")
            return None
    
    async def ping_host(self, host: str, count: int = 4) -> Tuple[str, bool]:
        """Ping a host.
        
        Args:
            host: Host to ping.
            count: Number of ping packets.
            
        Returns:
            Tuple[str, bool]: (output, success)
        """
        try:
            stdout, stderr, code = await self.run_command(f"ping -c {count} -W 5 {host}")
            return stdout, code == 0
        except Exception as e:
            logger.error(f"Failed to ping {host}: {e}")
            return str(e), False
    
    async def traceroute_host(self, host: str, max_hops: int = 30) -> Tuple[str, bool]:
        """Traceroute to a host.
        
        Args:
            host: Host to traceroute.
            max_hops: Maximum hops.
            
        Returns:
            Tuple[str, bool]: (output, success)
        """
        try:
            stdout, stderr, code = await self.run_command(
                f"traceroute -m {max_hops} -w 2 {host}",
                timeout=60
            )
            return stdout, code == 0
        except Exception as e:
            logger.error(f"Failed to traceroute {host}: {e}")
            return str(e), False
    
    async def get_system_logs(self, lines: int = 50, service: Optional[str] = None) -> Optional[str]:
        """Get system logs via journalctl.
        
        Args:
            lines: Number of log lines.
            service: Optional service name filter.
            
        Returns:
            Optional[str]: Log output or None if failed.
        """
        try:
            cmd = f"journalctl -n {lines} --no-pager"
            if service:
                cmd += f" -u {service}"
            
            stdout, stderr, code = await self.run_command(cmd)
            if code == 0:
                return stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            return None
    
    async def get_network_stats(self, interface: str = "all") -> Optional[str]:
        """Get network statistics.
        
        Args:
            interface: Network interface name or 'all'.
            
        Returns:
            Optional[str]: Network statistics or None if failed.
        """
        try:
            if interface == "all":
                stdout, stderr, code = await self.run_command("ip -s link")
            else:
                stdout, stderr, code = await self.run_command(f"ip -s link show {interface}")
            
            if code == 0:
                return stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return None
    
    async def download_iso(self, url: str, storage_path: str) -> Tuple[bool, str]:
        """Download ISO file.
        
        Args:
            url: ISO download URL.
            storage_path: Destination path on server.
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Use wget with progress
            cmd = f"wget -P {storage_path} {url}"
            stdout, stderr, code = await self.run_command(cmd, timeout=3600)
            
            if code == 0:
                return True, "ISO downloaded successfully"
            else:
                return False, stderr or "Download failed"
        except Exception as e:
            logger.error(f"Failed to download ISO: {e}")
            return False, str(e)
    
    async def update_system(self) -> Tuple[bool, str]:
        """Update system packages.
        
        Returns:
            Tuple[bool, str]: (success, output)
        """
        try:
            # Update package list and upgrade
            cmd = "apt-get update && apt-get upgrade -y"
            stdout, stderr, code = await self.run_command(cmd, timeout=600)
            
            if code == 0:
                return True, stdout
            else:
                return False, stderr or "Update failed"
        except Exception as e:
            logger.error(f"Failed to update system: {e}")
            return False, str(e)
    
    async def get_disk_usage(self) -> Optional[str]:
        """Get disk usage information.
        
        Returns:
            Optional[str]: Disk usage output or None if failed.
        """
        try:
            stdout, stderr, code = await self.run_command("df -h")
            if code == 0:
                return stdout
            return None
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return None
