"""
SSH client for executing commands on Proxmox host.
"""
import asyncio
import logging
from typing import Optional, Tuple
import asyncssh

logger = logging.getLogger(__name__)


class SSHClient:
    """Async SSH client for remote command execution."""
    
    def __init__(
        self,
        host: str,
        user: str,
        key_path: str,
        port: int = 22
    ):
        """
        Initialize SSH client.
        
        Args:
            host: SSH host address
            user: SSH username
            key_path: Path to SSH private key
            port: SSH port
        """
        self.host = host
        self.user = user
        self.key_path = key_path
        self.port = port
    
    async def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute command via SSH.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, output)
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
                
                if result.exit_status == 0:
                    return True, result.stdout
                else:
                    return False, result.stderr or result.stdout
                    
        except asyncio.TimeoutError:
            logger.error(f"Command timed out: {command}")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"SSH command error: {e}")
            return False, str(e)
    
    async def get_cpu_temperature(self) -> Optional[dict]:
        """
        Get CPU temperature using lm-sensors.
        
        Returns:
            Dictionary with temperature information
        """
        success, output = await self.run_command("sensors -A -u")
        
        if not success:
            return None
        
        temps = {}
        current_chip = None
        
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Chip name
            if line.endswith(':') and not line.startswith(' '):
                current_chip = line[:-1]
                temps[current_chip] = {}
            # Temperature reading
            elif '_input:' in line and current_chip:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = float(parts[1].strip())
                    temps[current_chip][key] = value
        
        return temps
    
    async def get_smart_status(self, device: str = "/dev/sda") -> Optional[str]:
        """
        Get SMART status for a disk.
        
        Args:
            device: Device path
            
        Returns:
            SMART status output
        """
        success, output = await self.run_command(f"smartctl -H {device}")
        return output if success else None
    
    async def get_disk_info(self) -> Optional[str]:
        """
        Get disk usage information.
        
        Returns:
            Disk usage output
        """
        success, output = await self.run_command("df -h")
        return output if success else None
    
    async def get_network_stats(self) -> Optional[str]:
        """
        Get network statistics.
        
        Returns:
            Network statistics output
        """
        success, output = await self.run_command("cat /proc/net/dev")
        return output if success else None
    
    async def get_load_average(self) -> Optional[str]:
        """
        Get system load average.
        
        Returns:
            Load average output
        """
        success, output = await self.run_command("cat /proc/loadavg")
        return output if success else None
    
    async def ping_host(self, host: str, count: int = 4) -> Tuple[bool, str]:
        """
        Ping a host.
        
        Args:
            host: Host to ping
            count: Number of ping attempts
            
        Returns:
            Tuple of (success, output)
        """
        return await self.run_command(f"ping -c {count} {host}")
    
    async def traceroute_host(self, host: str, max_hops: int = 30) -> Tuple[bool, str]:
        """
        Traceroute to a host.
        
        Args:
            host: Host to traceroute
            max_hops: Maximum number of hops
            
        Returns:
            Tuple of (success, output)
        """
        return await self.run_command(f"traceroute -m {max_hops} {host}", timeout=60)
    
    async def get_system_logs(self, lines: int = 50, service: Optional[str] = None) -> Optional[str]:
        """
        Get system logs using journalctl.
        
        Args:
            lines: Number of lines to retrieve
            service: Optional service name filter
            
        Returns:
            Log output
        """
        if service:
            cmd = f"journalctl -u {service} -n {lines} --no-pager"
        else:
            cmd = f"journalctl -n {lines} --no-pager"
        
        success, output = await self.run_command(cmd)
        return output if success else None
    
    async def get_proxmox_logs(self, lines: int = 50) -> Optional[str]:
        """
        Get Proxmox logs.
        
        Args:
            lines: Number of lines to retrieve
            
        Returns:
            Log output
        """
        success, output = await self.run_command(f"tail -n {lines} /var/log/pve/tasks/active")
        if not success:
            # Try alternative log location
            success, output = await self.run_command(f"journalctl -u pvedaemon -n {lines} --no-pager")
        
        return output if success else None
    
    async def get_qemu_logs(self, vmid: int, lines: int = 50) -> Optional[str]:
        """
        Get QEMU guest agent logs for a VM.
        
        Args:
            vmid: VM ID
            lines: Number of lines to retrieve
            
        Returns:
            Log output
        """
        success, output = await self.run_command(
            f"tail -n {lines} /var/log/qemu-server/{vmid}.log"
        )
        return output if success else None
    
    async def download_iso(self, url: str, storage: str = "local") -> Tuple[bool, str]:
        """
        Download ISO image to Proxmox storage.
        
        Args:
            url: URL of ISO to download
            storage: Storage location
            
        Returns:
            Tuple of (success, output)
        """
        # Get storage path
        success, path_output = await self.run_command(
            f"pvesm path {storage}:iso"
        )
        
        if not success:
            return False, "Failed to get storage path"
        
        storage_path = path_output.strip().rsplit('/', 1)[0]
        filename = url.split('/')[-1]
        
        # Download ISO
        cmd = f"cd {storage_path} && wget -c '{url}' -O {filename}"
        return await self.run_command(cmd, timeout=3600)
    
    async def update_system(self) -> Tuple[bool, str]:
        """
        Update system packages.
        
        Returns:
            Tuple of (success, output)
        """
        return await self.run_command(
            "apt-get update && apt-get upgrade -y",
            timeout=600
        )
