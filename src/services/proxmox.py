"""Proxmox API client for managing Proxmox VE."""
import asyncio
from typing import List, Dict, Any, Optional
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import logging

from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)


def run_in_executor(func):
    """Decorator to run synchronous Proxmox API calls in executor."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: func(self, *args, **kwargs)
        )
    return wrapper


class ProxmoxClient:
    """Proxmox API client with async methods."""
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        token_name: str,
        token_value: str,
        verify_ssl: bool = False
    ):
        """
        Initialize Proxmox client.
        
        Args:
            host: Proxmox host
            port: Proxmox port
            user: User name
            token_name: API token name
            token_value: API token value
            verify_ssl: Verify SSL certificate
        """
        self.host = host
        self.port = port
        self.user = user
        self.verify_ssl = verify_ssl
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Initialize ProxmoxAPI with token authentication
        self.proxmox = ProxmoxAPI(
            host,
            user=user,
            token_name=token_name,
            token_value=token_value,
            port=port,
            verify_ssl=verify_ssl
        )
        
        logger.info(f"Proxmox client initialized for {host}:{port}")
    
    @run_in_executor
    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get list of nodes.
        
        Returns:
            List of nodes
        """
        try:
            nodes = self.proxmox.nodes.get()
            return nodes
        except Exception as e:
            logger.error(f"Error getting nodes: {e}")
            return []
    
    @run_in_executor
    def get_vms(self, node: str) -> List[Dict[str, Any]]:
        """
        Get list of VMs on a node.
        
        Args:
            node: Node name
            
        Returns:
            List of VMs
        """
        try:
            vms = []
            
            # Get QEMU VMs
            try:
                qemu_vms = self.proxmox.nodes(node).qemu.get()
                for vm in qemu_vms:
                    vm['type'] = 'qemu'
                    vm['node'] = node
                    vms.append(vm)
            except Exception as e:
                logger.error(f"Error getting QEMU VMs from {node}: {e}")
            
            # Get LXC containers
            try:
                lxc_vms = self.proxmox.nodes(node).lxc.get()
                for vm in lxc_vms:
                    vm['type'] = 'lxc'
                    vm['node'] = node
                    vms.append(vm)
            except Exception as e:
                logger.error(f"Error getting LXC containers from {node}: {e}")
            
            return vms
        except Exception as e:
            logger.error(f"Error getting VMs from {node}: {e}")
            return []
    
    async def get_all_vms(self) -> List[Dict[str, Any]]:
        """
        Get all VMs from all nodes.
        
        Returns:
            List of all VMs
        """
        nodes = await self.get_nodes()
        all_vms = []
        
        for node in nodes:
            node_name = node['node']
            vms = await self.get_vms(node_name)
            all_vms.extend(vms)
        
        return all_vms
    
    @run_in_executor
    def start_vm(self, node: str, vmid: int, vm_type: str) -> Dict[str, Any]:
        """
        Start a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            Response from API
        """
        try:
            if vm_type == 'qemu':
                result = self.proxmox.nodes(node).qemu(vmid).status.start.post()
            else:
                result = self.proxmox.nodes(node).lxc(vmid).status.start.post()
            logger.info(f"Started {vm_type} VM {vmid} on {node}")
            return result
        except Exception as e:
            logger.error(f"Error starting VM {vmid} on {node}: {e}")
            raise
    
    @run_in_executor
    def stop_vm(self, node: str, vmid: int, vm_type: str) -> Dict[str, Any]:
        """
        Stop (kill) a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            Response from API
        """
        try:
            if vm_type == 'qemu':
                result = self.proxmox.nodes(node).qemu(vmid).status.stop.post()
            else:
                result = self.proxmox.nodes(node).lxc(vmid).status.stop.post()
            logger.info(f"Stopped {vm_type} VM {vmid} on {node}")
            return result
        except Exception as e:
            logger.error(f"Error stopping VM {vmid} on {node}: {e}")
            raise
    
    @run_in_executor
    def shutdown_vm(self, node: str, vmid: int, vm_type: str) -> Dict[str, Any]:
        """
        Shutdown a VM gracefully.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            Response from API
        """
        try:
            if vm_type == 'qemu':
                result = self.proxmox.nodes(node).qemu(vmid).status.shutdown.post()
            else:
                result = self.proxmox.nodes(node).lxc(vmid).status.shutdown.post()
            logger.info(f"Shutdown {vm_type} VM {vmid} on {node}")
            return result
        except Exception as e:
            logger.error(f"Error shutting down VM {vmid} on {node}: {e}")
            raise
    
    @run_in_executor
    def reboot_vm(self, node: str, vmid: int, vm_type: str) -> Dict[str, Any]:
        """
        Reboot a VM.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            Response from API
        """
        try:
            if vm_type == 'qemu':
                result = self.proxmox.nodes(node).qemu(vmid).status.reboot.post()
            else:
                result = self.proxmox.nodes(node).lxc(vmid).status.reboot.post()
            logger.info(f"Rebooted {vm_type} VM {vmid} on {node}")
            return result
        except Exception as e:
            logger.error(f"Error rebooting VM {vmid} on {node}: {e}")
            raise
    
    @run_in_executor
    def get_vm_status(self, node: str, vmid: int, vm_type: str) -> Dict[str, Any]:
        """
        Get VM status.
        
        Args:
            node: Node name
            vmid: VM ID
            vm_type: VM type (qemu or lxc)
            
        Returns:
            VM status
        """
        try:
            if vm_type == 'qemu':
                status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            else:
                status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            return status
        except Exception as e:
            logger.error(f"Error getting VM {vmid} status on {node}: {e}")
            raise
    
    @run_in_executor
    def get_vm_config(self, node: str, vmid: int, vm_type: str) -> Dict[str, Any]:
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
                config = self.proxmox.nodes(node).qemu(vmid).config.get()
            else:
                config = self.proxmox.nodes(node).lxc(vmid).config.get()
            return config
        except Exception as e:
            logger.error(f"Error getting VM {vmid} config on {node}: {e}")
            raise
    
    @run_in_executor
    def get_node_status(self, node: str) -> Dict[str, Any]:
        """
        Get node status.
        
        Args:
            node: Node name
            
        Returns:
            Node status
        """
        try:
            status = self.proxmox.nodes(node).status.get()
            return status
        except Exception as e:
            logger.error(f"Error getting node {node} status: {e}")
            raise
    
    @run_in_executor
    def get_vnc_ticket(self, node: str, vmid: int) -> Dict[str, Any]:
        """
        Get VNC ticket for NoVNC access.
        
        Args:
            node: Node name
            vmid: VM ID
            
        Returns:
            VNC ticket data
        """
        try:
            ticket = self.proxmox.nodes(node).qemu(vmid).vncproxy.post()
            return ticket
        except Exception as e:
            logger.error(f"Error getting VNC ticket for VM {vmid} on {node}: {e}")
            raise
    
    @run_in_executor
    def get_storage_list(self, node: str) -> List[Dict[str, Any]]:
        """
        Get list of storage on a node.
        
        Args:
            node: Node name
            
        Returns:
            List of storage
        """
        try:
            storage = self.proxmox.nodes(node).storage.get()
            return storage
        except Exception as e:
            logger.error(f"Error getting storage list on {node}: {e}")
            return []
    
    @run_in_executor
    def get_storage_content(
        self, 
        node: str, 
        storage: str, 
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get storage content.
        
        Args:
            node: Node name
            storage: Storage name
            content_type: Content type filter (iso, vztmpl, backup, etc.)
            
        Returns:
            List of storage content
        """
        try:
            params = {}
            if content_type:
                params['content'] = content_type
            
            content = self.proxmox.nodes(node).storage(storage).content.get(**params)
            return content
        except Exception as e:
            logger.error(f"Error getting storage {storage} content on {node}: {e}")
            return []
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
