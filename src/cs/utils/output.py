"""Output utilities for CSF CLI"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
import json
import sys

console = Console()

def success(message: str, json_output: bool = False):
    """Display success message"""
    if json_output:
        print(json.dumps({"status": "success", "message": message}))
    else:
        console.print(f"✅ {message}", style="green")

def error(message: str, json_output: bool = False, exit_code: int = 1):
    """Display error message and optionally exit"""
    if json_output:
        print(json.dumps({"status": "error", "message": message, "exit_code": exit_code}))
    else:
        console.print(f"❌ {message}", style="red")
    
    if exit_code > 0:
        sys.exit(exit_code)

def info(message: str, json_output: bool = False):
    """Display info message"""
    if json_output:
        print(json.dumps({"status": "info", "message": message}))
    else:
        console.print(f"ℹ️  {message}", style="blue")

def warning(message: str, json_output: bool = False):
    """Display warning message"""
    if json_output:
        print(json.dumps({"status": "warning", "message": message}))
    else:
        console.print(f"⚠️  {message}", style="yellow")

def panel(title: str, content: str, style: str = "blue"):
    """Display content in a panel"""
    console.print(Panel(content, title=title, border_style=style))

def table_data(data: list, headers: list, json_output: bool = False):
    """Display tabular data"""
    if json_output:
        print(json.dumps({"data": data, "headers": headers}))
    else:
        from rich.table import Table
        table = Table()
        
        for header in headers:
            table.add_column(header)
        
        for row in data:
            table.add_row(*[str(cell) for cell in row])
        
        console.print(table)
