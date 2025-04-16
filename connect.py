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

    def get_device_info(self, connection: ConnectHandler, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Gather device information using show commands."""
        try:
            # Get device version and basic info
            version_output = connection.send_command("show version")
            device_data = self.parser.parse_version(version_output)
            
            # Ensure all required fields are present
            required_fields = {
                'ip': device_info['host'],
                'device_type': device_info['device_type'],
                'hostname': device_data.get('hostname', ''),
                'serial_number': device_data.get('serial_number', ''),
                'platform': device_data.get('platform', ''),
                'version': device_data.get('version', ''),
                'neighbors': []
            }
            
            # Get CDP neighbors
            cdp_output = connection.send_command("show cdp neighbors detail")
            required_fields['neighbors'] = self.parser.parse_cdp_neighbors(cdp_output)

            # Log any missing required fields
            for field, value in required_fields.items():
                if not value:
                    self.logger.warning(f"Missing value for field: {field}")

            return required_fields
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