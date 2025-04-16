from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

@dataclass
class NetworkDevice:
    """Represents a network device in the inventory."""
    hostname: str
    ip: str
    device_type: str
    serial_number: Optional[str] = None
    platform: Optional[str] = None
    version: Optional[str] = None
    neighbors: Dict[str, Any] = None

    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = {}
        self.logger = logging.getLogger(__name__)

    def add_neighbor(self, neighbor_ip: str, neighbor_info: Dict[str, Any]) -> None:
        """Add a CDP neighbor to the device's neighbor list."""
        self.neighbors[neighbor_ip] = neighbor_info
        self.logger.debug(f"Added neighbor {neighbor_ip} to device {self.hostname}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert device information to a dictionary."""
        return {
            'hostname': self.hostname,
            'ip': self.ip,
            'device_type': self.device_type,
            'serial_number': self.serial_number,
            'platform': self.platform,
            'version': self.version,
            'neighbors': self.neighbors
        }

    def __str__(self) -> str:
        """String representation of the device."""
        return f"Device(hostname={self.hostname}, ip={self.ip}, type={self.device_type})" 