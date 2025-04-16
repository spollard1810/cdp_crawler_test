import yaml
import logging
import queue
import threading
import signal
import sys
import os
from datetime import datetime
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
        self.threads = []
        self.is_running = True
        
        self.logger = logging.getLogger(__name__)
        
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def setup_logging(self) -> None:
        """Configure logging with a new log file for each instance."""
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Generate timestamp for log filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'crawler_{timestamp}.log')

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config['output']['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Log startup information
        logging.info(f"Starting new crawler instance. Log file: {log_file}")
        logging.info(f"Configuration loaded from: {self.config_path}")
        logging.info(f"Database path: {self.config['database']['path']}")
        logging.info(f"Seed device: {self.config['seed_device']['host']}")

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C signal."""
        self.logger.info("Received interrupt signal. Shutting down gracefully...")
        self.is_running = False
        self._stop_workers()

    def _stop_workers(self):
        """Stop all worker threads gracefully."""
        # Signal all workers to stop
        for _ in range(len(self.threads)):
            self.device_queue.put(None)
        
        # Wait for all threads to complete
        for thread in self.threads:
            thread.join(timeout=5)
            if thread.is_alive():
                self.logger.warning(f"Thread {thread.name} did not stop gracefully")
        
        self.threads = []
        self.logger.info("All worker threads stopped")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        self.config_path = config_path
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _worker(self) -> None:
        """Worker thread for processing devices from the queue."""
        while self.is_running:
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
                    device_data = self.connector.get_device_info(connection, device_info)
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
                if not self.is_running:
                    break
                continue
            except Exception as e:
                self.logger.error(f"Error in worker thread: {str(e)}")
                self.device_queue.task_done()

    def start(self) -> None:
        """Start the crawling process."""
        try:
            # Add seed device to queue
            self.device_queue.put(self.config['seed_device'])

            # Create worker threads
            for _ in range(self.config['crawler']['max_threads']):
                thread = threading.Thread(target=self._worker)
                thread.start()
                self.threads.append(thread)

            # Wait for all devices to be processed
            self.device_queue.join()

            self.logger.info("Crawling completed")
        except KeyboardInterrupt:
            self.logger.info("Crawling interrupted by user")
        finally:
            self._stop_workers()

    def export_to_csv(self, filename: str = None) -> None:
        """Export the collected data to CSV."""
        if filename is None:
            filename = self.config['output']['csv_path']
        self.db_manager.export_to_csv(filename)

    def __del__(self) -> None:
        """Cleanup when the crawler is destroyed."""
        self._stop_workers()
        self.db_manager.close() 