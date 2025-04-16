from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from typing import Dict, Any, List
import logging

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
    neighbors = Column(JSON)

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
            device = Device(
                hostname=device_data['hostname'],
                ip=device_data['ip'],
                device_type=device_data['device_type'],
                serial_number=device_data.get('serial_number'),
                platform=device_data.get('platform'),
                version=device_data.get('version'),
                neighbors=device_data.get('neighbors', {})
            )
            self.session.add(device)
            self.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error adding device to database: {str(e)}")
            self.session.rollback()
            return False

    def device_exists(self, ip: str) -> bool:
        """Check if a device exists in the database."""
        return self.session.query(Device).filter_by(ip=ip).first() is not None

    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Retrieve all devices from the database."""
        devices = self.session.query(Device).all()
        return [{
            'hostname': d.hostname,
            'ip': d.ip,
            'device_type': d.device_type,
            'serial_number': d.serial_number,
            'platform': d.platform,
            'version': d.version,
            'neighbors': d.neighbors
        } for d in devices]

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