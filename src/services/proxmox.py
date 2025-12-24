"""
Proxmox API client with async wrapper.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from proxmoxer import ProxmoxAPI
import requests

logger = logging.getLogger(__name__)


class ProxmoxClient:
    """Async wrapper for Proxmox API."""
    
    def __init__(
        self,
        host: str,
        user: str,
        token_name: str,
        token_value: str,
        verify_ssl: bool = False
    ):
        """
        Initialize Proxmox client.
        
        Args:
            host: Proxmox host address
            user: Username (e.g., root@pam)
            token_name: API token name
            token_value: API token value
            verify_ssl: Whether to verify SSL certificates
        """
        self.host = host
        self.user = user
        self.token_name = token_name
        self.token_value = token_value
        self.verify_ssl = verify_ssl
        
        # Create synchronous client
        self._client = ProxmoxAPI(
            host,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl
        )
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """Run synchronous function in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get list of cluster nodes.
        
        Returns:
            List of node information
        """
        try:
            return await self._run_in_executor(self._client.nodes.get)
        except Exception as e:
            logger.error(f"Error getting nodes: {e}")
            return []
    
    async def get_node_status(self, node: str = "pve") -> Optional[Dict[str, Any]]:
        """
        Get node status information.
        
        Args:
            node: Node name
            
        Returns:
            Node status information
        """
        try:
            return await self._run_in_executor(
                self._client.nodes(node).status.get
            )
        except Exception as e:
            logger.error(f"Error getting node status: {e}")
            return None
    
    async def get_vms(self, node: str = "pve") -> List[Dict[str, Any]]:
        """
        Get list of all VMs (QEMU and LXC) on a node.
        
        Args:
            node: Node name
            
        Returns:
            List of VMs with their information
        """
        try:
            # Get QEMU VMs
            qemu_vms = await self._run_in_executor(
                self._client.nodes(node).qemu.get
            )
            for vm in qemu_vms:
                vm['type'] = 'qemu'
            
            # Get LXC containers
            lxc_vms = await self._run_in_executor(
                self._client.nodes(node).lxc.get
            )
            for vm in lxc_vms:
                vm['type'] = 'lxc'
            
            return qemu_vms + lxc_vms
        except Exception as e:
            logger.error(f"Error getting VMs: {e}")
            return []
    
    async def get_vm_status(
        self,
        node: str,
        vmid: int,
        vm_type: str = 'qemu'
    ) -> Optional[Dict[str, Any]]:
        """
        Get VM status information.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            VM status information
        """
        try:
            if vm_type == 'qemu':
                return await self._run_in_executor(
                    self._client.nodes(node).qemu(vmid).status.current.get
                )
            else:
                return await self._run_in_executor(
                    self._client.nodes(node).lxc(vmid).status.current.get
                )
        except Exception as e:
            logger.error(f"Error getting VM {vmid} status: {e}")
            return None
    
    async def start_vm(
        self,
        node: str,
        vmid: int,
        vm_type: str = 'qemu'
    ) -> bool:
        """
        Start a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            True if successful
        """
        try:
            if vm_type == 'qemu':
                await self._run_in_executor(
                    self._client.nodes(node).qemu(vmid).status.start.post
                )
            else:
                await self._run_in_executor(
                    self._client.nodes(node).lxc(vmid).status.start.post
                )
            logger.info(f"Started VM {vmid} on node {node}")
            return True
        except Exception as e:
            logger.error(f"Error starting VM {vmid}: {e}")
            return False
    
    async def stop_vm(
        self,
        node: str,
        vmid: int,
        vm_type: str = 'qemu'
    ) -> bool:
        """
        Force stop a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            True if successful
        """
        try:
            if vm_type == 'qemu':
                await self._run_in_executor(
                    self._client.nodes(node).qemu(vmid).status.stop.post
                )
            else:
                await self._run_in_executor(
                    self._client.nodes(node).lxc(vmid).status.stop.post
                )
            logger.info(f"Stopped VM {vmid} on node {node}")
            return True
        except Exception as e:
            logger.error(f"Error stopping VM {vmid}: {e}")
            return False
    
    async def shutdown_vm(
        self,
        node: str,
        vmid: int,
        vm_type: str = 'qemu'
    ) -> bool:
        """
        Gracefully shutdown a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            True if successful
        """
        try:
            if vm_type == 'qemu':
                await self._run_in_executor(
                    self._client.nodes(node).qemu(vmid).status.shutdown.post
                )
            else:
                await self._run_in_executor(
                    self._client.nodes(node).lxc(vmid).status.shutdown.post
                )
            logger.info(f"Shutdown VM {vmid} on node {node}")
            return True
        except Exception as e:
            logger.error(f"Error shutting down VM {vmid}: {e}")
            return False
    
    async def reboot_vm(
        self,
        node: str,
        vmid: int,
        vm_type: str = 'qemu'
    ) -> bool:
        """
        Reboot a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            True if successful
        """
        try:
            if vm_type == 'qemu':
                await self._run_in_executor(
                    self._client.nodes(node).qemu(vmid).status.reboot.post
                )
            else:
                await self._run_in_executor(
                    self._client.nodes(node).lxc(vmid).status.reboot.post
                )
            logger.info(f"Rebooted VM {vmid} on node {node}")
            return True
        except Exception as e:
            logger.error(f"Error rebooting VM {vmid}: {e}")
            return False
    
    async def get_vnc_ticket(
        self,
        node: str,
        vmid: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get VNC ticket for VM console.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            VNC ticket information
        """
        try:
            return await self._run_in_executor(
                self._client.nodes(node).qemu(vmid).vncproxy.post
            )
        except Exception as e:
            logger.error(f"Error getting VNC ticket for VM {vmid}: {e}")
            return None
    
    async def get_storage_list(self, node: str = "pve") -> List[Dict[str, Any]]:
        """
        Get list of storages.
        
        Args:
            node: Node name
            
        Returns:
            List of storage information
        """
        try:
            return await self._run_in_executor(
                self._client.nodes(node).storage.get
            )
        except Exception as e:
            logger.error(f"Error getting storage list: {e}")
            return []
    
    async def get_storage_content(
        self,
        node: str,
        storage: str,
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get storage content.
        
        Args:
            node: Node name
            storage: Storage ID
            content_type: Content type filter (iso, vztmpl, backup, etc.)
            
        Returns:
            List of storage content
        """
        try:
            params = {}
            if content_type:
                params['content'] = content_type
            
            return await self._run_in_executor(
                self._client.nodes(node).storage(storage).content.get,
                **params
            )
        except Exception as e:
            logger.error(f"Error getting storage content: {e}")
            return []
    
    async def get_vm_config(
        self,
        node: str,
        vmid: int,
        vm_type: str = 'qemu'
    ) -> Optional[Dict[str, Any]]:
        """
        Get VM configuration.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            VM configuration
        """
        try:
            if vm_type == 'qemu':
                return await self._run_in_executor(
                    self._client.nodes(node).qemu(vmid).config.get
                )
            else:
                return await self._run_in_executor(
                    self._client.nodes(node).lxc(vmid).config.get
                )
        except Exception as e:
            logger.error(f"Error getting VM {vmid} config: {e}")
            return None
