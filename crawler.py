import yaml
import logging
import queue
import threading
from typing import Dict, Any
from devices import NetworkDevice
from connect import DeviceConnector
from data import DatabaseManager

class CDPCrawler:
    """Main crawler class that manages the crawling process."""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        self.device_queue = queue.Queue()
        self.visited_devices = set()
        self.db_manager = DatabaseManager(self.config['database']['path'])
        self.connector = DeviceConnector(self.config)
        
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self) -> None:
        """Configure logging based on config."""
        logging.basicConfig(
            level=getattr(logging, self.config['output']['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _worker(self) -> None:
        """Worker thread for processing devices from the queue."""
        while True:
            try:
                device_info = self.device_queue.get(timeout=5)
                if device_info is None:
                    break

                ip = device_info['host']
                if ip in self.visited_devices:
                    self.device_queue.task_done()
                    continue

                self.visited_devices.add(ip)
                self.logger.info(f"Processing device: {ip}")

                connection = self.connector.connect(device_info)
                if connection:
                    device_data = self.connector.get_device_info(connection)
                    self.connector.disconnect(connection)

                    if device_data:
                        self.db_manager.add_device(device_data)
                        
                        # Add neighbors to queue
                        for neighbor in device_data.get('neighbors', []):
                            if neighbor['ip'] not in self.visited_devices:
                                neighbor_info = {
                                    'host': neighbor['ip'],
                                    'device_type': 'cisco_ios',  # Default, can be updated
                                    'username': self.config['seed_device']['username'],
                                    'password': self.config['seed_device']['password']
                                }
                                self.device_queue.put(neighbor_info)

                self.device_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Error in worker thread: {str(e)}")
                self.device_queue.task_done()

    def start(self) -> None:
        """Start the crawling process."""
        # Add seed device to queue
        self.device_queue.put(self.config['seed_device'])

        # Create worker threads
        threads = []
        for _ in range(self.config['crawler']['max_threads']):
            thread = threading.Thread(target=self._worker)
            thread.start()
            threads.append(thread)

        # Wait for all devices to be processed
        self.device_queue.join()

        # Stop worker threads
        for _ in range(self.config['crawler']['max_threads']):
            self.device_queue.put(None)

        for thread in threads:
            thread.join()

        self.logger.info("Crawling completed")

    def export_to_csv(self, filename: str = None) -> None:
        """Export the collected data to CSV."""
        if filename is None:
            filename = self.config['output']['csv_path']
        self.db_manager.export_to_csv(filename)

    def __del__(self) -> None:
        """Cleanup when the crawler is destroyed."""
        self.db_manager.close() 