# CDP Network Crawler

A Python-based network crawler that uses CDP (Cisco Discovery Protocol) to discover and inventory network devices.

## Overview

This crawler is designed to:
1. Start from a seed device
2. Connect to devices using Netmiko
3. Gather device information (hostname, IP, serial number, device type)
4. Use CDP to discover neighboring devices
5. Store all information in a SQLite database
6. Export results to CSV

## Project Structure

```
cdp_crawler/
├── devices.py      # NetworkDevice class and device-related logic
├── crawler.py      # Main crawler logic with threading and queue management
├── connect.py      # Connection handling using Netmiko
├── parser.py       # Data parsing using TextFSM templates
├── data.py         # Database management and data storage
├── config.yaml     # Configuration file
└── templates/      # TextFSM templates for parsing
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.yaml` to set:
- Seed device information
- Credentials
- Database settings
- Thread count
- Timeout values

## Usage

```python
from crawler import CDPCrawler

# Initialize crawler
crawler = CDPCrawler(config_path='config.yaml')

# Start crawling
crawler.start()

# Export results
crawler.export_to_csv('network_inventory.csv')
```

## Features

- Multi-threaded crawling
- Automatic device type detection
- SQLite database for tracking crawled devices
- CSV export functionality
- Configurable timeouts and retries
- Support for multiple device types through TextFSM templates

## Requirements

- Python 3.8+
- Network devices with CDP enabled
- SSH access to devices
- TextFSM templates for device parsing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 