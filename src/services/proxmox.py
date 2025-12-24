"""Proxmox API client with async wrapper."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from functools import wraps
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException

logger = logging.getLogger(__name__)


def run_async(func):
    """Decorator to run synchronous Proxmox API calls in executor."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(self, *args, **kwargs))
    return wrapper


class ProxmoxClient:
    """Async wrapper for Proxmox API client."""
    
    def __init__(self, host: str, user: str, token_name: str, token_value: str, verify_ssl: bool = False):
        """Initialize Proxmox API client.
        
        Args:
            host: Proxmox host address.
            user: Proxmox user (e.g., root@pam).
            token_name: API token name.
            token_value: API token value.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.host = host
        self.user = user
        self.token_name = token_name
        self.verify_ssl = verify_ssl
        
        try:
            self.api = ProxmoxAPI(
                host,
                user=user,
                token_name=token_name,
                token_value=token_value,
                verify_ssl=verify_ssl
            )
            logger.info(f"Connected to Proxmox API at {host}")
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox API: {e}")
            raise
    
    @run_async
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get list of Proxmox nodes.
        
        Returns:
            List[Dict]: List of nodes.
        """
        try:
            return self.api.nodes.get()
        except Exception as e:
            logger.error(f"Failed to get nodes: {e}")
            raise
    
    @run_async
    def get_node_status(self, node: str) -> Dict[str, Any]:
        """Get node status.
        
        Args:
            node: Node name.
            
        Returns:
            Dict: Node status information.
        """
        try:
            return self.api.nodes(node).status.get()
        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            raise
    
    @run_async
    def get_vms(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of all VMs and containers.
        
        Args:
            node: Optional node name. If None, gets VMs from all nodes.
            
        Returns:
            List[Dict]: List of VMs with their information.
        """
        try:
            vms = []
            nodes = [node] if node else [n['node'] for n in self.api.nodes.get()]
            
            for node_name in nodes:
                # Get QEMU VMs
                try:
                    qemu_vms = self.api.nodes(node_name).qemu.get()
                    for vm in qemu_vms:
                        vm['node'] = node_name
                        vm['type'] = 'qemu'
                    vms.extend(qemu_vms)
                except Exception as e:
                    logger.warning(f"Failed to get QEMU VMs from {node_name}: {e}")
                
                # Get LXC containers
                try:
                    lxc_containers = self.api.nodes(node_name).lxc.get()
                    for ct in lxc_containers:
                        ct['node'] = node_name
                        ct['type'] = 'lxc'
                    vms.extend(lxc_containers)
                except Exception as e:
                    logger.warning(f"Failed to get LXC containers from {node_name}: {e}")
            
            return vms
        except Exception as e:
            logger.error(f"Failed to get VMs: {e}")
            raise
    
    @run_async
    def get_vm_status(self, node: str, vmid: int, vm_type: str = 'qemu') -> Dict[str, Any]:
        """Get VM status and configuration.
        
        Args:
            node: Node name.
            vmid: VM ID.
            vm_type: VM type ('qemu' or 'lxc').
            
        Returns:
            Dict: VM status information.
        """
        try:
            if vm_type == 'lxc':
                return self.api.nodes(node).lxc(vmid).status.current.get()
            else:
                return self.api.nodes(node).qemu(vmid).status.current.get()
        except Exception as e:
            logger.error(f"Failed to get VM {vmid} status: {e}")
            raise
    
    @run_async
    def get_vm_config(self, node: str, vmid: int, vm_type: str = 'qemu') -> Dict[str, Any]:
        """Get VM configuration.
        
        Args:
            node: Node name.
            vmid: VM ID.
            vm_type: VM type ('qemu' or 'lxc').
            
        Returns:
            Dict: VM configuration.
        """
        try:
            if vm_type == 'lxc':
                return self.api.nodes(node).lxc(vmid).config.get()
            else:
                return self.api.nodes(node).qemu(vmid).config.get()
        except Exception as e:
            logger.error(f"Failed to get VM {vmid} config: {e}")
            raise
    
    @run_async
    def start_vm(self, node: str, vmid: int, vm_type: str = 'qemu') -> str:
        """Start a VM.
        
        Args:
            node: Node name.
            vmid: VM ID.
            vm_type: VM type ('qemu' or 'lxc').
            
        Returns:
            str: Task ID.
        """
        try:
            if vm_type == 'lxc':
                result = self.api.nodes(node).lxc(vmid).status.start.post()
            else:
                result = self.api.nodes(node).qemu(vmid).status.start.post()
            logger.info(f"Started VM {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to start VM {vmid}: {e}")
            raise
    
    @run_async
    def stop_vm(self, node: str, vmid: int, vm_type: str = 'qemu') -> str:
        """Stop a VM (forced).
        
        Args:
            node: Node name.
            vmid: VM ID.
            vm_type: VM type ('qemu' or 'lxc').
            
        Returns:
            str: Task ID.
        """
        try:
            if vm_type == 'lxc':
                result = self.api.nodes(node).lxc(vmid).status.stop.post()
            else:
                result = self.api.nodes(node).qemu(vmid).status.stop.post()
            logger.info(f"Stopped VM {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to stop VM {vmid}: {e}")
            raise
    
    @run_async
    def shutdown_vm(self, node: str, vmid: int, vm_type: str = 'qemu') -> str:
        """Gracefully shutdown a VM.
        
        Args:
            node: Node name.
            vmid: VM ID.
            vm_type: VM type ('qemu' or 'lxc').
            
        Returns:
            str: Task ID.
        """
        try:
            if vm_type == 'lxc':
                result = self.api.nodes(node).lxc(vmid).status.shutdown.post()
            else:
                result = self.api.nodes(node).qemu(vmid).status.shutdown.post()
            logger.info(f"Shutdown VM {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to shutdown VM {vmid}: {e}")
            raise
    
    @run_async
    def reboot_vm(self, node: str, vmid: int, vm_type: str = 'qemu') -> str:
        """Reboot a VM.
        
        Args:
            node: Node name.
            vmid: VM ID.
            vm_type: VM type ('qemu' or 'lxc').
            
        Returns:
            str: Task ID.
        """
        try:
            if vm_type == 'lxc':
                result = self.api.nodes(node).lxc(vmid).status.reboot.post()
            else:
                result = self.api.nodes(node).qemu(vmid).status.reboot.post()
            logger.info(f"Rebooted VM {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to reboot VM {vmid}: {e}")
            raise
    
    @run_async
    def get_vnc_ticket(self, node: str, vmid: int) -> Dict[str, str]:
        """Get VNC console ticket for a VM.
        
        Args:
            node: Node name.
            vmid: VM ID.
            
        Returns:
            Dict: VNC ticket information (ticket, user, cert, port).
        """
        try:
            result = self.api.nodes(node).qemu(vmid).vncproxy.post(websocket=1)
            logger.info(f"Generated VNC ticket for VM {vmid}")
            return result
        except Exception as e:
            logger.error(f"Failed to get VNC ticket for VM {vmid}: {e}")
            raise
    
    @run_async
    def get_storage_list(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of storage pools.
        
        Args:
            node: Optional node name for node-specific storage.
            
        Returns:
            List[Dict]: List of storage pools.
        """
        try:
            if node:
                return self.api.nodes(node).storage.get()
            else:
                return self.api.storage.get()
        except Exception as e:
            logger.error(f"Failed to get storage list: {e}")
            raise
    
    @run_async
    def get_storage_content(self, node: str, storage: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get storage content.
        
        Args:
            node: Node name.
            storage: Storage name.
            content_type: Optional content type filter (iso, backup, etc.).
            
        Returns:
            List[Dict]: List of storage content.
        """
        try:
            params = {}
            if content_type:
                params['content'] = content_type
            return self.api.nodes(node).storage(storage).content.get(**params)
        except Exception as e:
            logger.error(f"Failed to get storage content: {e}")
            raise
    
    @run_async
    def get_vm_agent_info(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get QEMU guest agent information.
        
        Args:
            node: Node name.
            vmid: VM ID.
            
        Returns:
            Optional[Dict]: Guest agent info if available.
        """
        try:
            return self.api.nodes(node).qemu(vmid).agent('network-get-interfaces').get()
        except Exception as e:
            logger.debug(f"Guest agent not available for VM {vmid}: {e}")
            return None
