from netmiko import ConnectHandler
from typing import Dict, Any, Optional
import logging
from parser import Parser

class DeviceConnector:
    """Handles device connections and command execution."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parser = Parser()
        self.logger = logging.getLogger(__name__)

    def connect(self, device_info: Dict[str, Any]) -> Optional[ConnectHandler]:
        """Establish connection to a network device."""
        try:
            connection = ConnectHandler(
                device_type=device_info['device_type'],
                host=device_info['host'],
                username=device_info['username'],
                password=device_info['password'],
                port=device_info.get('port', 22)
            )
            self.logger.info(f"Successfully connected to {device_info['host']}")
            return connection
        except Exception as e:
            self.logger.error(f"Failed to connect to {device_info['host']}: {str(e)}")
            return None

    def get_device_info(self, connection: ConnectHandler) -> Dict[str, Any]:
        """Gather device information using show commands."""
        device_info = {}
        
        try:
            # Get device version and basic info
            version_output = connection.send_command("show version")
            device_info.update(self.parser.parse_version(version_output))

            # Get CDP neighbors
            cdp_output = connection.send_command("show cdp neighbors detail")
            device_info['neighbors'] = self.parser.parse_cdp_neighbors(cdp_output)

            return device_info
        except Exception as e:
            self.logger.error(f"Error gathering device information: {str(e)}")
            return {}

    def disconnect(self, connection: ConnectHandler) -> None:
        """Close the connection to the device."""
        try:
            connection.disconnect()
            self.logger.info("Connection closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing connection: {str(e)}") 