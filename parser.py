import textfsm
from typing import Dict, Any, List
import logging
import os

class Parser:
    """Handles parsing of device output using TextFSM templates."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.template_dir = "templates"

    def _parse_with_template(self, template_name: str, output: str) -> List[Dict[str, Any]]:
        """Parse output using a TextFSM template."""
        try:
            template_path = os.path.join(self.template_dir, template_name)
            with open(template_path) as f:
                template = textfsm.TextFSM(f)
                return template.ParseText(output)
        except Exception as e:
            self.logger.error(f"Error parsing with template {template_name}: {str(e)}")
            return []

    def parse_version(self, output: str) -> Dict[str, Any]:
        """Parse show version output."""
        parsed = self._parse_with_template("show_version.textfsm", output)
        if parsed:
            return {
                'hostname': parsed[0][4],  # HOSTNAME
                'version': parsed[0][1],   # VERSION
                'platform': parsed[0][12], # HARDWARE (first item)
                'serial_number': parsed[0][13],  # SERIAL (first item)
                'rommon': parsed[0][3],    # ROMMON
                'config_register': parsed[0][15],  # CONFIG_REGISTER
                'mac_address': parsed[0][16],  # MAC_ADDRESS (first item)
                'uptime': parsed[0][5]     # UPTIME
            }
        return {}

    def parse_cdp_neighbors(self, output: str) -> List[Dict[str, Any]]:
        """Parse show cdp neighbors detail output."""
        parsed = self._parse_with_template("show_cdp_neighbors_detail.textfsm", output)
        neighbors = []
        for entry in parsed:
            neighbors.append({
                'device_id': entry[0],     # NEIGHBOR_NAME
                'ip': entry[1],            # MGMT_ADDRESS
                'platform': entry[2],       # PLATFORM
                'local_interface': entry[4],  # LOCAL_INTERFACE
                'neighbor_interface': entry[3],  # NEIGHBOR_INTERFACE
                'capabilities': entry[6]    # CAPABILITIES
            })
        return neighbors 