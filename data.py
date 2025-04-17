from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from typing import Dict, Any, List
import logging
import json

Base = declarative_base()

class Device(Base):
    """SQLAlchemy model for network devices."""
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    ip = Column(String, unique=True)
    device_type = Column(String)
    serial_number = Column(String)
    platform = Column(String)
    version = Column(String)
    neighbors = Column(String)  # Changed from JSON to String to store serialized JSON

class DatabaseManager:
    """Manages database operations for the crawler."""

    def __init__(self, db_path: str):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.logger = logging.getLogger(__name__)

    def add_device(self, device_data: Dict[str, Any]) -> bool:
        """Add a device to the database."""
        try:
            # Ensure all required fields are present with default values
            device = Device(
                hostname=device_data.get('hostname', ''),
                ip=device_data.get('ip', ''),
                device_type=device_data.get('device_type', ''),
                serial_number=device_data.get('serial_number', ''),
                platform=device_data.get('platform', ''),
                version=device_data.get('version', ''),
                neighbors=json.dumps(device_data.get('neighbors', []))  # Serialize neighbors to JSON string
            )
            
            self.session.add(device)
            self.session.commit()
            self.logger.info(f"Successfully added device {device_data.get('ip')} to database")
            return True
        except Exception as e:
            self.logger.error(f"Error adding device to database: {str(e)}")
            self.logger.error(f"Device data: {device_data}")
            self.session.rollback()
            return False

    def device_exists(self, ip: str) -> bool:
        """Check if a device exists in the database."""
        return self.session.query(Device).filter_by(ip=ip).first() is not None

    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Retrieve all devices from the database."""
        devices = self.session.query(Device).all()
        result = []
        for d in devices:
            try:
                device_dict = {
                    'hostname': d.hostname,
                    'ip': d.ip,
                    'device_type': d.device_type,
                    'serial_number': d.serial_number,
                    'platform': d.platform,
                    'version': d.version,
                    'neighbors': json.loads(d.neighbors) if d.neighbors else []
                }
                result.append(device_dict)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding neighbors JSON for device {d.ip}: {str(e)}")
                device_dict = {
                    'hostname': d.hostname,
                    'ip': d.ip,
                    'device_type': d.device_type,
                    'serial_number': d.serial_number,
                    'platform': d.platform,
                    'version': d.version,
                    'neighbors': []
                }
                result.append(device_dict)
        return result

    def export_to_csv(self, filename: str) -> None:
        """Export device data to CSV."""
        try:
            devices = self.get_all_devices()
            df = pd.DataFrame(devices)
            df.to_csv(filename, index=False)
            self.logger.info(f"Successfully exported data to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")

    def close(self) -> None:
        """Close the database session."""
        self.session.close() 