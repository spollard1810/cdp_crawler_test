import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
from crawler import CDPCrawler
import os
import sys

console = Console()

def validate_config(ctx, param, value):
    """Validate the config file exists and is valid YAML."""
    if not os.path.exists(value):
        raise click.BadParameter(f"Config file '{value}' does not exist")
    try:
        with open(value, 'r') as f:
            yaml.safe_load(f)
        return value
    except yaml.YAMLError as e:
        raise click.BadParameter(f"Invalid YAML in config file: {str(e)}")

@click.group()
def cli():
    """CDP Network Crawler - Discover and inventory network devices using CDP."""
    pass

@cli.command()
@click.option('--config', '-c', default='config.yaml', 
              callback=validate_config,
              help='Path to configuration file')
@click.option('--threads', '-t', type=int, help='Number of worker threads')
@click.option('--timeout', type=int, help='Connection timeout in seconds')
@click.option('--output', '-o', help='Output CSV file path')
def crawl(config, threads, timeout, output):
    """Start the network crawling process."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing crawler...", total=None)
            
            # Load and update config
            with open(config, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if threads:
                config_data['crawler']['max_threads'] = threads
            if timeout:
                config_data['crawler']['timeout'] = timeout
            if output:
                config_data['output']['csv_path'] = output
            
            # Create crawler instance
            crawler = CDPCrawler(config_path=config)
            
            progress.update(task, description="Starting crawl...")
            crawler.start()
            
            progress.update(task, description="Exporting results...")
            crawler.export_to_csv(config_data['output']['csv_path'])
            
            progress.update(task, description="Crawl completed!")
            
        # Display summary
        table = Table(title="Crawl Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Seed Device", config_data['seed_device']['host'])
        table.add_row("Threads Used", str(config_data['crawler']['max_threads']))
        table.add_row("Output File", config_data['output']['csv_path'])
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--config', '-c', default='config.yaml', 
              callback=validate_config,
              help='Path to configuration file')
def show_config(config):
    """Display the current configuration."""
    with open(config, 'r') as f:
        config_data = yaml.safe_load(f)
    
    console.print(Panel.fit(
        yaml.dump(config_data, default_flow_style=False),
        title="Current Configuration",
        border_style="blue"
    ))

@cli.command()
@click.option('--config', '-c', default='config.yaml', 
              callback=validate_config,
              help='Path to configuration file')
def status(config):
    """Show the status of the crawl database."""
    try:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        from data import DatabaseManager
        db = DatabaseManager(config_data['database']['path'])
        
        devices = db.get_all_devices()
        
        table = Table(title="Crawl Status")
        table.add_column("Total Devices", style="cyan")
        table.add_column("Database Path", style="green")
        
        table.add_row(str(len(devices)), config_data['database']['path'])
        
        console.print(table)
        
        if devices:
            device_table = Table(title="Discovered Devices")
            device_table.add_column("Hostname", style="cyan")
            device_table.add_column("IP", style="green")
            device_table.add_column("Type", style="yellow")
            
            for device in devices:
                device_table.add_row(
                    device['hostname'],
                    device['ip'],
                    device['device_type']
                )
            
            console.print(device_table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli() 